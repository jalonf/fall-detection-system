import logging

from PySide6.QtCore import QObject, Slot

from src.database.models.patient import Patient
from src.dtos.frame_packet import FramePacket
from src.workers.base_video_worker import BaseVideoWorker
from src.workers.video_worker import VideoWorker

logger = logging.getLogger(__name__)


class BaseMonitorController(QObject):
    """
    Logic shared by the monitoring controllers: it starts and stops the camera /
    video-file workers and shows what they report. The workers themselves store the
    fall event and send the alert e-mail.

    It is a QObject living in the GUI thread, so every worker signal connected to its
    slots is delivered as a queued call in the GUI thread, never in the worker's thread.

    Stopping never blocks the interface: `stop_camera` only asks the worker to stop, and
    the view is reset when the worker's `finished` signal arrives (the same path covers
    the end of a video file and a camera that disconnects). Only `shutdown`, used when
    logging out or closing the window, waits for the worker.

    Subclasses extend `_show_frame` to show more of each processed frame, and `_camera_worker`
    to change how the camera is monitored.
    """

    # The workers store each fall and e-mail the caregiver. False in test mode (administrators).
    SENDS_ALERTS = True

    def __init__(self, view, current_user, patient: Patient | None, on_logout_callback):
        super().__init__()
        self.view = view
        self.user = current_user
        self.patient = patient
        self.worker: BaseVideoWorker | None = None
        self._waiting_first_frame = False
        self._closed = False

        self.view.start_requested.connect(self.start_camera)
        self.view.stop_requested.connect(self.stop_camera)
        self.view.logout_requested.connect(on_logout_callback)

        user_name = getattr(self.user, "name", "Unknown")
        logger.info("%s initialized for user: %s", type(self).__name__, user_name)

    # ------------------------------------------------------------------ start / stop
    @Slot(int)
    def start_camera(self, camera_index):
        if self.worker is not None:
            logger.warning("Attempted to start camera stream, but a worker is already active.")
            return

        self._start(self._camera_worker(camera_index), f"Starting camera {camera_index}...")

    def _camera_worker(self, camera_index: int) -> BaseVideoWorker:
        """The patient's risk level picks the camera settings; falls are stored and e-mailed."""
        return VideoWorker(camera_index=camera_index, user=self.user, patient=self.patient)

    @Slot()
    def stop_camera(self):
        """Asks the worker to stop. Returns at once; `_on_worker_finished` resets the view."""
        if self.worker is None or self.worker.isInterruptionRequested():
            return

        logger.info("Stopping camera worker...")
        self.worker.requestInterruption()
        self.view.set_stopping()

    def shutdown(self):
        """Stops the worker and waits for it. For logging out and closing the window."""
        self._closed = True
        worker, self.worker = self.worker, None
        if worker is None:
            return

        logger.info("Shutting down camera worker...")
        worker.requestInterruption()
        worker.wait()

    def _start(self, worker: BaseVideoWorker, message: str):
        """Connects the worker to the view, starts it and logs `message`."""
        self.worker = worker
        self._waiting_first_frame = True
        self._connect_worker(worker)
        worker.start()
        self.view.set_monitoring_state(True)
        self.view.log_event("INFO", message)

    def _connect_worker(self, worker: BaseVideoWorker):
        worker.frame_available.connect(self._on_frame_available)
        worker.source_failed.connect(self._on_source_failed)
        worker.fall_detected.connect(self._on_fall)
        worker.notification_sent.connect(self._on_notification_sent)
        worker.finished.connect(self._on_worker_finished)

    # ------------------------------------------------------------------ worker signals
    def _active_sender(self) -> BaseVideoWorker | None:
        """
        The running worker when the signal being handled comes from it, otherwise None. Signals
        still queued from a worker that was already shut down are ignored; if that worker has
        been destroyed, `sender()` is None, so `self.worker` being None must be checked too.
        Returning the worker (not a bool) lets callers use it without `self.worker` being Optional.
        """
        worker = self.worker
        return worker if worker is not None and self.sender() is worker else None

    @Slot()
    def _on_frame_available(self):
        worker = self._active_sender()
        if worker is None:
            return

        packet = worker.take_frame()
        if packet is None:
            return
        if self._waiting_first_frame:
            self._waiting_first_frame = False
            self.view.log_event("INFO", "Stream connected")
        self._show_frame(packet)

    def _show_frame(self, packet: FramePacket):
        """Shows one processed frame. Subclasses extend this."""
        self.view.update_video_frame(packet.frame)

    @Slot()
    def _on_worker_finished(self):
        worker = self._active_sender()
        if worker is None:
            return

        worker.wait()   # `finished` is emitted just before the thread ends: let it end
        self.worker = None
        self.view.set_monitoring_state(False)
        self.view.log_event("INFO", "Stream disconnected")
        self.view.clear_video()

    @Slot(str)
    def _on_source_failed(self, message: str):
        if self._active_sender() is not None:
            self.view.log_event("ERROR", message)

    @Slot(float)
    def _on_fall(self, probability: float):
        """The worker reported a fall (it already stored it and is sending the e-mail)."""
        logger.warning("Fall detected (%.0f%%)", probability * 100)
        if self._closed:
            return
        self.view.trigger_fall_alert(f"Fall detected ({probability:.0%})")
        if self.SENDS_ALERTS:
            self.view.log_event("INFO", "Sending notification e-mail...")

    @Slot(bool)
    def _on_notification_sent(self, ok: bool):
        if self._closed:   # the e-mail can finish after logging out, when the view is gone
            return
        self.view.log_event(
            "INFO", "Notification e-mail sent" if ok else "The notification e-mail could not be sent"
        )
