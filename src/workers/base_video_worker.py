"""Video pipeline shared by the camera worker and the video-file worker."""

import collections
import logging
import threading
import time
from datetime import datetime

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

from src.ai.extractor import MediaPipeExtractor
from src.dtos.frame_packet import FramePacket
from src.notifications.email_notifier import EmailNotifier, fall_event_data
from src.repositories.fall_repository import FallRepository
from src.views.theme import Colors
from src.workers.frame_utils import (
    FALL_COLOR,
    OK_COLOR,
    censor_face,
    draw_person_box,
    draw_skeleton,
    encode_snapshot,
    person_bounds,
    to_qimage,
)
from src.workers.inference_worker import InferenceWorker
from src.workers.strategies import MonitoringStrategy

logger = logging.getLogger(__name__)

_STAGE_RGB = bytes.fromhex(Colors.STAGE.lstrip("#"))
SKELETON_BACKGROUND = tuple(reversed(_STAGE_RGB))   # BGR of the panel's stage, so the image blends in
POSE_VALUES = 99                                    # 33 landmarks x (x, y, z)


class BaseVideoWorker(QThread):
    """Processes frames: pose extraction, face blur, fall inference and drawing.

    Subclasses only decide where the frames come from (`_open_source`). Everything else
    lives here, so the fall logic exists once and runs in a single thread (the one
    executing `run`).

    The constructor does no heavy work, because it runs in the GUI thread: opening the
    source, starting MediaPipe and loading the model all happen at the start of `run`,
    so the window never freezes while they load. To stop, call `requestInterruption()`
    and wait for `finished` instead of blocking the GUI thread.

    Frames reach the interface through a single slot that only holds the newest one
    (see `take_frame`): if the interface falls behind, old frames are dropped instead of
    piling up as queued signals, so the picture never lags behind the camera.

    When a fall starts, the worker itself creates the `FallEvent` and e-mails the alert,
    with the capture attached, to `user` (the e-mail goes out in a short-lived thread so the
    video does not stall). The capture only lives in memory: it is never written to disk.
    `patient` and `user` are optional: without them nothing is stored or sent, and the fall
    is only reported through the signals.
    """

    frame_available = Signal()           # a new FramePacket is waiting in `take_frame`
    source_failed = Signal(str)          # the source could not be opened or the pipeline failed
    fall_detected = Signal(float)        # probability (0-1)
    notification_sent = Signal(bool)     # result of the alert e-mail

    source_label = "video source"        # for log and error messages, e.g. "camera 0"

    def __init__(self, user=None, patient=None, parent=None):
        super().__init__(parent)
        self.user = user
        self.patient = patient
        self.strategy: MonitoringStrategy | None = None
        self.extractor: MediaPipeExtractor | None = None
        self.inference_worker: InferenceWorker | None = None
        self.last_known_landmarks = None
        self.last_pose = None   # last model input seen, repeated while nobody is detected

        self.seq_len = 0
        self.sequence_buffer: collections.deque = collections.deque()
        self.current_is_fall = False

        self._frame_lock = threading.Lock()
        self._latest_frame: FramePacket | None = None

    # ------------------------------------------------------------------ source
    def _open_source(self) -> tuple[cv2.VideoCapture, MonitoringStrategy]:
        """Opens the frame source and picks the strategy. Runs in the worker thread."""
        raise NotImplementedError

    def _on_source_opened(self, cap: cv2.VideoCapture) -> None:
        """Hook called once everything is ready, just before the first frame."""

    # ------------------------------------------------------------------ thread
    def run(self):
        """Opens the source, loads the models and processes frames until stopped or the source ends."""
        cap, strategy = self._open_source()
        if not cap.isOpened():
            logger.error("Could not open %s", self.source_label)
            cap.release()
            self.source_failed.emit(f"Could not open {self.source_label}")
            return

        logger.info("Starting %s with %s strategy", self.source_label, strategy.name)
        try:
            self._setup(strategy)
            self._on_source_opened(cap)

            while not self.isInterruptionRequested():
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                self._process_frame(frame)
        except Exception:
            logger.exception("The video pipeline stopped because of an unexpected error")
            self.source_failed.emit("Detection stopped because of an unexpected error")
        finally:
            self._release(cap)

    def _setup(self, strategy: MonitoringStrategy) -> None:
        """Starts MediaPipe and the fall model for this strategy (the slow part of starting)."""
        self.strategy = strategy
        self.seq_len = strategy.fps   # the model sees one second of frames
        self.sequence_buffer = collections.deque(maxlen=self.seq_len)
        self.extractor = MediaPipeExtractor()
        self.inference_worker = InferenceWorker()
        self.inference_worker.load_model(strategy.model_path)
        self.inference_worker.start()

    def _models(self) -> tuple[MediaPipeExtractor, InferenceWorker]:
        """Returns the pose extractor and the fall model, created by `_setup`.

        Every frame is processed after `_setup`; asking for them earlier is a programming error.

        Raises:
            RuntimeError: If `_setup` has not created them yet.
        """
        if self.extractor is None or self.inference_worker is None:
            raise RuntimeError("The video pipeline was used before _setup() created its models")
        return self.extractor, self.inference_worker

    # ------------------------------------------------------------------ frames
    def take_frame(self) -> FramePacket | None:
        """Called from the GUI thread: returns the newest frame and empties the slot."""
        with self._frame_lock:
            packet, self._latest_frame = self._latest_frame, None
        return packet

    def _publish(self, packet: FramePacket) -> None:
        """Leaves `packet` in the slot, replacing a frame the interface has not taken yet.

        The signal is only emitted when the slot was empty, so at most one is ever queued.
        """
        with self._frame_lock:
            notify = self._latest_frame is None
            self._latest_frame = packet
        if notify:
            self.frame_available.emit()

    def _process_frame(self, frame) -> None:
        """Runs the whole pipeline for one BGR frame and emits the results."""
        started = time.perf_counter()
        extractor, inference_worker = self._models()

        # 1. Pose. If MediaPipe finds nobody, keep the last pose so the drawing does not flicker.
        skeleton = extractor.extract_pose(frame_bgr=frame)
        
        if skeleton:
            pose = skeleton.pose
            landmarks = skeleton.landmarks_2d
            self.last_known_landmarks = landmarks
        else:
            pose = None
            landmarks = self.last_known_landmarks

        # 2. Privacy: blur the face before drawing, displaying or storing anything.
        if landmarks:
            censor_face(frame, landmarks)

        # 3. Model: add the pose to the window and ask for a prediction once it is full.
        #    The prediction runs in another thread; here we only read its latest result.
        #    Every frame takes a slot, as in training: if MediaPipe finds nobody, the last
        #    pose is repeated (nothing is added until someone has been seen once).
        if pose is not None and pose.size == POSE_VALUES:
            self.last_pose = pose.flatten()
        if self.last_pose is not None:
            self.sequence_buffer.append(self.last_pose)
        if len(self.sequence_buffer) == self.seq_len:
            inference_worker.predict(np.expand_dims(np.array(self.sequence_buffer), axis=0))

        fall_probability = self._poll_fall()

        # 4. Drawing and telemetry. The skeleton panel gets its own image.
        telemetry = {"inference_ms": (time.perf_counter() - started) * 1000,
                     "centroid_y": None, "confidence": 0.0}
        skeleton_view = np.full(frame.shape, SKELETON_BACKGROUND, dtype=np.uint8)

        if landmarks:
            height, width, _ = frame.shape
            color = FALL_COLOR if self.current_is_fall else OK_COLOR

            box = person_bounds(landmarks, width, height, margin=25)
            if box:
                draw_person_box(frame, box, self.current_is_fall)
            draw_skeleton(frame, landmarks, color, size=2)
            draw_skeleton(skeleton_view, landmarks, color, size=4)

            # Crop the skeleton panel around the person.
            crop = person_bounds(landmarks, width, height, margin=60)
            if crop:
                x1, y1, x2, y2 = crop
                skeleton_view = skeleton_view[y1:y2, x1:x2]

            telemetry["confidence"] = sum(lm.visibility for lm in landmarks) / len(landmarks)
            hips = landmarks[23:25]   # left and right hip
            if len(hips) == 2 and all(hip.visibility > 0.5 for hip in hips):
                telemetry["centroid_y"] = (hips[0].y + hips[1].y) / 2

        # 5. Fall: handled after drawing, so the stored capture shows the red box and skeleton.
        if fall_probability is not None:
            self._handle_fall(frame, fall_probability)

        # 6. Hand everything to the interface (only the newest frame is kept).
        self._publish(FramePacket(to_qimage(frame), to_qimage(skeleton_view), telemetry))

    def _poll_fall(self) -> float | None:
        """Returns the probability when a fall has just started, otherwise None."""
        _, inference_worker = self._models()
        result = inference_worker.latest
        if result is None:
            return None

        is_fall, probability = result
        started = is_fall and not self.current_is_fall   # only the moment it changes to "fall"
        self.current_is_fall = is_fall
        return probability if started else None

    def _handle_fall(self, frame, probability: float) -> None:
        """A fall has just started: store the event, tell the UI, e-mail the alert with the capture."""
        snapshot = encode_snapshot(frame)   # JPEG bytes, memory only

        fall_event = None
        if self.patient:
            fall_event = FallRepository().create_fall_event(self.patient, probability)

        self.fall_detected.emit(probability)

        if self.user is not None:
            timestamp = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M:%S")
            event_data = fall_event_data(self.patient, self.user, probability, timestamp, snapshot)

            # Send the e-mail in a separate thread so the video does not freeze while waiting for the SMTP server.
            threading.Thread(
                target=self._send_alert,
                args=(self.user.email, event_data, fall_event),
                name="fall-alert-email",
            ).start()

    def _send_alert(self, recipient: str, event_data: dict, fall_event) -> None:
        """Runs in its own thread: the SMTP call can take a second or more."""
        ok = False
        try:
            ok = EmailNotifier(recipient).update(event_data)
            if ok and fall_event is not None:
                FallRepository().mark_notification_sent(fall_event)
        except Exception:
            logger.exception("Unexpected error while sending the alert e-mail")
        self.notification_sent.emit(bool(ok))

    def _release(self, cap) -> None:
        logger.info("Releasing resources...")
        cap.release()
        if self.extractor is not None:
            self.extractor.release()
        if self.inference_worker is not None:
            self.inference_worker.stop()
