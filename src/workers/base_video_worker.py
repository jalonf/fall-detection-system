"""Video pipeline shared by the camera worker and the video-file worker."""

import collections
import logging
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from src.ai.extractor import MediaPipeExtractor
from src.notifications.email_notifier import EmailNotifier, fall_event_data
from src.repositories.fall_repository import FallRepository
from src.views.theme import Colors
from src.workers.frame_utils import (
    FALL_COLOR,
    OK_COLOR,
    censor_face,
    draw_person_box,
    draw_skeleton,
    person_bounds,
    save_snapshot,
    to_qimage,
)
from src.workers.inference_worker import InferenceWorker
from src.workers.strategies import MonitoringStrategy

logger = logging.getLogger(__name__)

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "snapshots"

_STAGE_RGB = bytes.fromhex(Colors.STAGE.lstrip("#"))
SKELETON_BACKGROUND = tuple(reversed(_STAGE_RGB))   # BGR of the panel's stage, so the image blends in
POSE_VALUES = 99                                    # 33 landmarks x (x, y, z)


class BaseVideoWorker(QThread):
    """
    Processes frames: pose extraction, face blur, fall inference and drawing.

    Subclasses only decide where the frames come from (`run`) and which strategy's
    model to load. Everything else lives here, so the fall logic exists
    once and runs in a single thread (the one executing `run`).

    When a fall starts, the worker itself stores the capture, creates the `FallEvent`
    and e-mails the alert to `user` (the e-mail goes out in a short-lived thread so the
    video does not stall). `patient` and `user` are optional: without them nothing is
    stored or sent, and the fall is only reported through the signals.
    """

    frame_ready = Signal(QImage)
    skeleton_frame_ready = Signal(QImage)
    telemetry_data_ready = Signal(dict)
    fall_detected = Signal(float, str)   # probability (0-1) and the capture path ('' if none)
    notification_sent = Signal(bool)     # result of the alert e-mail

    def __init__(self, user=None, patient=None, parent=None):
        super().__init__(parent)
        self.user = user
        self.patient = patient
        self._is_running = True
        self.extractor = MediaPipeExtractor()
        self.inference_worker = InferenceWorker()
        self.last_known_landmarks = None
        self.last_pose = None   # last model input seen, repeated while nobody is detected

        self.seq_len = 15
        self.sequence_buffer = collections.deque(maxlen=self.seq_len)
        self.current_is_fall = False


    def _load_model(self, strategy: MonitoringStrategy):
        """Loads the GRU model of `strategy` and starts inference."""
        self.seq_len = strategy.fps   # the model sees one second of frames
        self.sequence_buffer = collections.deque(self.sequence_buffer, maxlen=self.seq_len)
        self.inference_worker.load_model(strategy.model_path)

        if not self.inference_worker.isRunning():
            self.inference_worker.start()

    def _process_frame(self, frame) -> None:
        """Runs the whole pipeline for one BGR frame and emits the results."""
        started = time.perf_counter()

        # 1. Pose. If MediaPipe finds nobody, keep the last pose so the drawing does not flicker.
        pose, landmarks = self.extractor.extract_pose(frame_bgr=frame)
        landmarks = landmarks or self.last_known_landmarks
        self.last_known_landmarks = landmarks

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
            self.inference_worker.predict(np.expand_dims(np.array(self.sequence_buffer), axis=0))
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

        # 6. Send everything to the interface.
        self.telemetry_data_ready.emit(telemetry)
        self.frame_ready.emit(to_qimage(frame))
        self.skeleton_frame_ready.emit(to_qimage(skeleton_view))

    def _poll_fall(self) -> float | None:
        """Returns the probability when a fall has just started, otherwise None."""
        result = self.inference_worker.latest
        if result is None:
            return None

        is_fall, probability = result
        started = is_fall and not self.current_is_fall   # only the moment it changes to "fall"
        self.current_is_fall = is_fall
        return probability if started else None

    def _handle_fall(self, frame, probability: float) -> None:
        """A fall has just started: store the capture and the event, tell the UI, e-mail the alert."""
        snapshot_path = save_snapshot(frame, SNAPSHOT_DIR)

        fall_event = None
        if self.patient:
            fall_event = FallRepository().create_fall_event(
                self.patient, probability, snapshot_path=snapshot_path
            )

        self.fall_detected.emit(probability, snapshot_path or "")

        if self.user is not None:
            timestamp = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M:%S")
            event_data = fall_event_data(self.patient, self.user, probability, timestamp, snapshot_path)

            # Send the e-mail in a separate thread so the video does not freeze while waiting for Resend.
            threading.Thread(
                target=self._send_alert,
                args=(self.user.email, event_data, fall_event),
                name="fall-alert-email",
            ).start()

    def _send_alert(self, recipient: str, event_data: dict, fall_event) -> None:
        """Runs in its own thread: the Resend call can take a second or more."""
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
        self.extractor.release()
        self.inference_worker.stop()

    def stop(self):
        self._is_running = False
        self.wait()
