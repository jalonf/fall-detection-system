import logging
import os

from src.repositories.patient_repository import PatientRepository
from src.workers.strategies import strategy_for
from src.workers.video_file_worker import VideoFileWorker
from src.workers.video_worker import VideoWorker

logger = logging.getLogger(__name__)


class BaseMonitorController:
    """
    Logic shared by the monitoring controllers: it starts and stops the camera /
    video-file workers and shows what they report. The workers themselves store the
    fall event and send the alert e-mail.

    Subclasses extend `_connect_worker` to wire extra signals to their view.
    """

    def __init__(self, view, current_user, patient, on_logout_callback):
        self.view = view
        self.user = current_user
        self.patient = patient
        self.worker = None

        self.view.start_requested.connect(self.start_camera)
        self.view.upload_requested.connect(self.start_video_file)
        self.view.stop_requested.connect(self.stop_camera)
        self.view.logout_requested.connect(on_logout_callback)

        user_name = getattr(self.user, "name", "Unknown")
        logger.info("%s initialized for user: %s", type(self).__name__, user_name)

    def start_camera(self, camera_index):
        if self.worker is not None:
            logger.warning("Attempted to start camera stream, but a worker is already active.")
            return

        self._start(
            VideoWorker(
                camera_index=camera_index,
                strategy=strategy_for(PatientRepository().get_risk_level(self.patient)),
                user=self.user,
                patient=self.patient,
            ),
            f"Stream connected (Source {camera_index})",
        )

    def start_video_file(self, file_path):
        if self.worker is not None:
            logger.warning("Attempted to process video file, but a worker is already active.")
            return

        worker = VideoFileWorker(video_path=file_path, user=self.user, patient=self.patient)
        worker.playback_finished.connect(self.stop_camera)
        self._start(worker, f"Processing video file: {os.path.basename(file_path)}")

    def stop_camera(self):
        if not self.worker:
            return

        logger.info("Stopping camera worker...")
        self.worker.stop()
        self.worker.wait()
        self.worker = None

        self.view.set_monitoring_state(False)
        self.view.log_event("INFO", "Stream disconnected")
        self.view.clear_video()

    def _start(self, worker, message: str):
        """Connects the worker to the view, starts it and logs `message`."""
        self.worker = worker
        self._connect_worker(worker)
        worker.start()
        self.view.set_monitoring_state(True)
        self.view.log_event("INFO", message)

    def _connect_worker(self, worker):
        """Wires the worker signals to the view. Subclasses extend this."""
        worker.frame_ready.connect(self.view.update_video_frame)
        worker.fall_detected.connect(self._on_fall)
        worker.notification_sent.connect(self._on_notification_sent)

    def _on_fall(self, probability: float):
        """The worker reported a fall (it already stored it and is sending the e-mail)."""
        logger.warning("Fall detected (%.0f%%)", probability * 100)
        self.view.trigger_fall_alert(f"Fall detected ({probability:.0%})")
        self.view.log_event("INFO", "Sending notification e-mail...")

    def _on_notification_sent(self, ok: bool):
        self.view.log_event(
            "INFO", "Notification e-mail sent" if ok else "The notification e-mail could not be sent"
        )