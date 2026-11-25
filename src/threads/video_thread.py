"""Video thread: reads a camera or a video file, frame by frame, and processes each frame."""

import logging
import os
import threading
import time

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

from src.ai.extractor import MediaPipeExtractor
from src.ai.fall_model import FallModelError
from src.domain.monitoring_profiles import (
    HighRiskStrategy,
    LowRiskStrategy,
    MonitoringStrategy,
)
from src.dtos.frame_packet import FramePacket
from src.dtos.telemetry import Telemetry
from src.threads.fall_detection_thread import FallDetectionThread
from src.threads.frame_utils import (
    FALL_COLOR,
    OK_COLOR,
    censor_face,
    draw_person_box,
    draw_skeleton,
    person_bounds,
    to_qimage,
)
from src.views.theme import Colors

logger = logging.getLogger(__name__)

THREAD_NAME = "video-thread"
DEFAULT_FILE_FPS = 30.0   # when a video file does not say its frame rate
_STAGE_RGB = bytes.fromhex(Colors.STAGE.lstrip("#"))
SKELETON_BACKGROUND = tuple(reversed(_STAGE_RGB))   # BGR of the panel's stage, so the image blends in
MODEL_FAILED_MESSAGE = "Fall detection is not available: the fall model could not be used. Monitoring stopped."


def strategy_for_file(path: str) -> MonitoringStrategy:
    """Strategy of a video file: its own frame rate picks the 15- or the 30-frame model.

    Only the file's header is read, so it is quick enough for the GUI thread.

    Args:
        path: The video file.

    Returns:
        LowRiskStrategy for 20 FPS or less, HighRiskStrategy otherwise (or when it is unknown).
    """
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return LowRiskStrategy() if 1 < fps <= 20 else HighRiskStrategy()


class VideoThread(QThread):
    """Video thread: reads each frame, extracts the pose, blurs the face and draws.

    It is the first of the three threads of a monitoring session, all created, connected and
    stopped by the controller, none of which ever waits for another while working:

    1. **VideoThread** (this one): reads each frame, extracts the pose, blurs the face, draws,
       hands the frame to the interface and the pose to the fall detection thread;
    2. **FallDetectionThread**: builds the one-second window, runs the GRU and emits
       `fall_detected` when a fall starts. This thread only feeds it poses (`push`) and reads its
       state (`latest`, to draw in red, and `failed`);
    3. **AlertThread**: stores the fall and e-mails it. This thread never touches it.

    The source is a camera or a video file, and only two things differ between them (see `run`):

    * **Camera:** opened with the strategy's resolution and frame rate (the patient's risk level,
      or an administrator's test profile). Its frames are live, so each one is timed by the clock.
    * **Video file:** read as fast as it can be processed, so each frame is timed by its position
      in the video (frame number / FPS). The thread ends on its own when the file runs out.

    The constructor does no heavy work, because it runs in the GUI thread: opening the source and
    starting MediaPipe happen at the start of `run`, so the window never freezes while they load.
    To stop, call `requestInterruption()` and wait for `finished` instead of blocking the GUI thread.

    Frames reach the interface through a single slot that only holds the newest one (see
    `take_frame`): if the interface falls behind, old frames are dropped instead of piling up
    as queued signals, so the picture never lags behind the camera. Every frame is analysed
    before it is published, whether the interface shows it or not.

    Args:
        source: OpenCV index of a camera (int) or the path of a video file (str).
        strategy: Camera settings and model of this monitoring (for a file, see `strategy_for_file`).
        fall_detection_thread: The thread that receives the poses (started by the controller).
        parent: Parent object.
    """

    frame_available = Signal()           # a new FramePacket is waiting in `take_frame`
    source_failed = Signal(str)          # the source could not be opened or the pipeline failed

    def __init__(self, source: int | str, strategy: MonitoringStrategy,
                 fall_detection_thread: FallDetectionThread, parent=None):
        super().__init__(parent)
        self.setObjectName(THREAD_NAME)
        self.source = source
        self.strategy = strategy
        self.fall_detection_thread = fall_detection_thread
        if isinstance(source, int):
            self.source_label = f"camera {source}"
        else:
            self.source_label = f"video file {os.path.basename(source)}"
        self._last_landmarks = None      # kept while nobody is found, so the drawing does not flicker

        # The mailbox shared with the GUI thread: the newest frame, guarded by the lock.
        self._frame_lock = threading.Lock()
        self._latest_frame: FramePacket | None = None

    # ------------------------------------------------------------------ GUI thread
    def take_frame(self) -> FramePacket | None:
        """Called from the GUI thread: returns the newest frame and empties the mailbox."""
        with self._frame_lock:
            packet, self._latest_frame = self._latest_frame, None
        return packet

    # ------------------------------------------------------------------ video thread
    def run(self):
        """Opens the source, starts MediaPipe, processes frames until stopped, and releases everything."""
        threading.current_thread().name = THREAD_NAME   # shown in the log as the thread name
        fall_detection_thread = self.fall_detection_thread

        # 1. Open the source: a camera with the strategy's settings, or a file with its own FPS.
        cap = cv2.VideoCapture(self.source)
        if isinstance(self.source, int):                 # camera
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.strategy.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.strategy.height)
            cap.set(cv2.CAP_PROP_FPS, self.strategy.fps)
            frame_ms = None                              # live frames: timed by the clock
        else:                                            # video file: timed by the position in the video
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_ms = 1000 / (fps if fps > 1 else DEFAULT_FILE_FPS)

        extractor: MediaPipeExtractor | None = None
        try:
            if not cap.isOpened():
                logger.error("Could not open %s", self.source_label)
                self.source_failed.emit(f"Could not open {self.source_label}")
                return
            logger.info("Starting %s with %s strategy", self.source_label, self.strategy.name)

            # 2. Start MediaPipe (the fall model loads at the same time, in the other thread), then
            #    wait for the model, so no frame of a video file goes by before it can be analysed.
            extractor = MediaPipeExtractor()
            fall_detection_thread.wait_until_ready()

            # 3. One frame per turn, until "Stop" or the end of the source.
            frame_index = 0
            while not self.isInterruptionRequested():
                if fall_detection_thread.failed:
                    raise FallModelError("The fall model could not be loaded or stopped working")
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                timestamp_ms = time.monotonic() * 1000 if frame_ms is None else frame_index * frame_ms
                frame_index += 1
                self._process_frame(frame, timestamp_ms, extractor, fall_detection_thread)

        except FallModelError:
            # Never keep showing the video without a working model: it would look like monitoring.
            logger.exception("The video pipeline stopped: the fall model cannot be used")
            self.source_failed.emit(MODEL_FAILED_MESSAGE)
        except Exception:
            logger.exception("The video pipeline stopped because of an unexpected error")
            self.source_failed.emit("Detection stopped because of an unexpected error")
        finally:
            # 4. Release the source and MediaPipe. Before ending, let the fall detection thread
            #    finish loading its model, so the controller can then stop it at once.
            logger.info("Releasing resources...")
            cap.release()
            if extractor is not None:
                extractor.release()
            fall_detection_thread.wait_until_ready()

    def _process_frame(self, frame, timestamp_ms: float, extractor: MediaPipeExtractor,
                       fall_detection_thread: FallDetectionThread) -> None:
        """Runs the pipeline for one BGR frame and hands the results on."""
        started = time.perf_counter()

        # 1. Pose. If MediaPipe finds nobody, keep the last landmarks so the drawing does not flicker.
        skeleton = extractor.extract_pose(frame_bgr=frame)
        if skeleton:
            self._last_landmarks = skeleton.landmarks_2d
        landmarks = self._last_landmarks

        # 2. Privacy: blur the face before drawing, displaying or sending anything.
        if landmarks:
            censor_face(frame, landmarks)

        # 3. Fall detection happens in the fall detection thread: hand it the pose and move on.
        fall_detection_thread.push(timestamp_ms, skeleton.pose if skeleton else None)

        # 4. Drawing and telemetry, in red while the fall detection thread says the person is down.
        prediction = fall_detection_thread.latest
        is_fall = prediction is not None and prediction.is_fall
        inference_ms = (time.perf_counter() - started) * 1000
        confidence, centroid_y = 0.0, None
        skeleton_view = np.full(frame.shape, SKELETON_BACKGROUND, dtype=np.uint8)

        if landmarks:
            height, width, _ = frame.shape
            color = FALL_COLOR if is_fall else OK_COLOR

            box = person_bounds(landmarks, width, height, margin=25)
            if box:
                draw_person_box(frame, box, is_fall)
            draw_skeleton(frame, landmarks, color, size=2)
            draw_skeleton(skeleton_view, landmarks, color, size=4)

            # Crop the skeleton panel around the person.
            crop = person_bounds(landmarks, width, height, margin=60)
            if crop:
                x1, y1, x2, y2 = crop
                skeleton_view = skeleton_view[y1:y2, x1:x2]

            confidence = sum(lm.visibility for lm in landmarks) / len(landmarks)
            hips = landmarks[23:25]   # left and right hip
            if len(hips) == 2 and all(hip.visibility > 0.5 for hip in hips):
                centroid_y = (hips[0].y + hips[1].y) / 2

        # 5. Leave the frame in the mailbox (replacing one the interface has not taken yet) and
        #    ring the bell only if it was empty, so at most one signal is ever queued.
        telemetry = Telemetry(inference_ms=inference_ms, confidence=confidence, centroid_y=centroid_y)
        packet = FramePacket(to_qimage(frame), to_qimage(skeleton_view), telemetry)
        with self._frame_lock:
            notify = self._latest_frame is None
            self._latest_frame = packet
        if notify:
            self.frame_available.emit()
