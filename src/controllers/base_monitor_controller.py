"""Logic shared by the monitoring controllers (caregivers and administrators)."""

import logging

from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QImage

from src.database.models.patient import Patient
from src.domain.monitoring_profiles import MonitoringStrategy, strategy_for
from src.dtos.frame_packet import FramePacket
from src.strings import Messages
from src.threads.alert_thread import AlertThread
from src.threads.fall_detection_thread import FallDetectionThread
from src.threads.video_thread import VideoThread

logger = logging.getLogger(__name__)


class BaseMonitorController(QObject):
    """Creates, connects and stops the threads of each monitoring, and shows what they report.

    Every monitoring ("Start" → "Stop", or the end of a video file) has three threads, all owned
    by this controller, so none of them creates or stops another:

    * `VideoThread`: reads the camera or the video file and processes each frame;
    * `FallDetectionThread`: receives the poses from the video thread and emits `fall_detected`;
    * `AlertThread`: stores each fall and e-mails it (not in test mode).

    When the fall detection thread reports a fall, this controller shows it and gives it to the
    alert thread together with the frame on screen as the capture. This controller is a QObject
    living in the GUI thread, so every signal of those threads connected to its slots runs here,
    in the GUI thread.

    Stopping never blocks the interface: `stop_camera` only asks the video thread to stop, and
    the other threads are closed and the view reset when its `finished` signal arrives (the same
    path covers the end of a video file and a camera that disconnects). Only `shutdown`, used when
    signing out or closing the window, waits for it.

    Subclasses extend `_show_frame` to show more of each processed frame, and `_camera_strategy`
    to change how the camera is monitored.

    Signing out is not handled here: the dashboard around the monitoring page reports it to the
    coordinator, which stops this controller (`shutdown`) before leaving the screen.

    Args:
        view: The monitoring page it drives.
        current_user: The signed-in user (the alert e-mails go to them).
        patient: Their patient, or None (then nothing is stored).
    """

    # Each fall is stored and e-mailed to the caregiver. False in test mode (administrators).
    SENDS_ALERTS = True

    def __init__(self, view, current_user, patient: Patient | None):
        super().__init__()
        self.view = view
        self.user = current_user
        self.patient = patient
        # The threads of the current monitoring (None while not monitoring), created in `_start`.
        self.video_thread: VideoThread | None = None
        self.fall_detection_thread: FallDetectionThread | None = None
        self.alert_thread: AlertThread | None = None
        self._waiting_first_frame = False
        self._closed = False
        self._last_frame: QImage | None = None   # the frame on screen: the capture of a fall

        self.view.start_requested.connect(self.start_camera)
        self.view.stop_requested.connect(self.stop_camera)

        user_name = getattr(self.user, "name", "Unknown")
        logger.info("%s initialized for user: %s", type(self).__name__, user_name)

    # ------------------------------------------------------------------ start / stop
    @Slot(int)
    def start_camera(self, camera_index):
        """Starts monitoring a camera, unless a source is already running.

        Args:
            camera_index: OpenCV index of the camera chosen in the view.
        """
        if self.video_thread is not None:
            logger.warning("Attempted to start the camera, but a monitoring is already running.")
            return

        self._start(camera_index, self._camera_strategy(), Messages.STARTING_CAMERA.format(index=camera_index))

    def _camera_strategy(self) -> MonitoringStrategy:
        """The patient's risk level picks the camera settings and the model."""
        return strategy_for(getattr(self.patient, "risk_level", None) or "LOW")

    @Slot()
    def stop_camera(self):
        """Asks the video thread to stop. Returns at once; `_on_video_thread_finished` does the rest."""
        if self.video_thread is None or self.video_thread.isInterruptionRequested():
            return

        logger.info("Stopping the video thread...")
        self.video_thread.requestInterruption()
        self.view.set_stopping()

    def shutdown(self):
        """Stops every thread, waiting for the video thread. For logging out and closing the window.

        Falls already handed to the alert thread are still stored and e-mailed in the background.
        """
        self._closed = True
        video_thread, self.video_thread = self.video_thread, None
        if video_thread is not None:
            logger.info("Shutting down the video thread...")
            video_thread.requestInterruption()
            video_thread.wait()
        self._stop_other_threads()

    def _start(self, source: int | str, strategy: MonitoringStrategy, message: str):
        """Starts a monitoring: creates its three threads, connects their signals and starts them.

        Args:
            source: Camera index (int) or video file path (str).
            strategy: Camera settings and model of this monitoring.
            message: What to write in the event log.
        """
        self._waiting_first_frame = True
        self._last_frame = None   # a fall's capture never comes from an earlier monitoring

        # 1. Create the threads: the fall detector, the video thread that feeds it, and the alerts.
        self.fall_detection_thread = FallDetectionThread(strategy.model_path, strategy.fps)
        self.video_thread = VideoThread(source, strategy, self.fall_detection_thread)
        if self.SENDS_ALERTS:
            self.alert_thread = AlertThread(self.user, self.patient)

        # 2. Connect their signals before starting them, so no signal is lost. This controller
        #    lives in the GUI thread, so the methods all run there.
        self.video_thread.frame_available.connect(self._on_frame_available)        # new frame in the mailbox
        self.video_thread.source_failed.connect(self._on_source_failed)             # camera or model failed
        self.video_thread.finished.connect(self._on_video_thread_finished)          # the monitoring ended
        self.fall_detection_thread.fall_detected.connect(self._on_fall)             # a fall has just started
        if self.alert_thread is not None:
            self.alert_thread.notification_sent.connect(self._on_notification_sent)   # e-mail result

        # 3. Start them: the fall detector first (it loads its model while MediaPipe loads in the
        #    video thread). The alert thread starts by itself with the first fall.
        self.fall_detection_thread.start()
        self.video_thread.start()
        self.view.set_monitoring_state(True)
        self.view.log_event("INFO", message)

    def _stop_other_threads(self):
        """Stops the fall detection thread and closes the alert thread, once the video thread has ended.

        The video thread waits for the fall model to be loaded before it ends, so stopping the
        fall detection thread is immediate. The alert thread is closed without waiting: falls it
        already has are still stored and e-mailed in the background.
        """
        fall_detection_thread, self.fall_detection_thread = self.fall_detection_thread, None
        if fall_detection_thread is not None:
            fall_detection_thread.stop()
        alert_thread, self.alert_thread = self.alert_thread, None
        if alert_thread is not None:
            alert_thread.shutdown()

    # ------------------------------------------------------------------ thread signals
    def _active_sender(self) -> VideoThread | None:
        """Returns the running video thread when it sent the signal being handled, otherwise None.

        Signals still queued from a video thread that was already shut down are ignored; if it
        has been destroyed, `sender()` is None, so `self.video_thread` being None is checked too.
        Returning the thread (not a bool) lets callers use it without it being Optional.
        """
        video_thread = self.video_thread
        return video_thread if video_thread is not None and self.sender() is video_thread else None

    @Slot()
    def _on_frame_available(self):
        video_thread = self._active_sender()
        if video_thread is None:
            return

        packet = video_thread.take_frame()
        if packet is None:
            return
        if self._waiting_first_frame:
            self._waiting_first_frame = False
            self.view.log_event("INFO", Messages.STREAM_CONNECTED)
        self._show_frame(packet)

    def _show_frame(self, packet: FramePacket):
        """Shows one processed frame. Subclasses extend this."""
        self._last_frame = packet.frame
        self.view.update_video_frame(packet.frame)

    @Slot()
    def _on_video_thread_finished(self):
        video_thread = self._active_sender()
        if video_thread is None:
            return

        video_thread.wait()   # `finished` is emitted just before the thread ends: let it end
        self.video_thread = None
        self._stop_other_threads()   # no more poses or falls can come
        self.view.set_monitoring_state(False)
        self.view.log_event("INFO", Messages.STREAM_DISCONNECTED)
        self.view.clear_video()

    @Slot(str)
    def _on_source_failed(self, message: str):
        if self._active_sender() is not None:
            self.view.log_event("ERROR", message)

    @Slot(float)
    def _on_fall(self, probability: float):
        """A fall has just started: show it and, unless in test mode, store it and e-mail it."""
        # Ignore falls still queued from a monitoring that has already ended.
        if self._closed or self.fall_detection_thread is None or self.sender() is not self.fall_detection_thread:
            return
        logger.warning("Fall detected (%.0f%%)", probability * 100)
        self.view.trigger_fall_alert(Messages.FALL_DETECTED.format(probability=probability))
        if self.alert_thread is None:
            return
        if self.alert_thread.handle(probability, self._last_frame):
            self.view.log_event("INFO", Messages.SENDING_EMAIL)
        else:
            self.view.log_event("INFO", Messages.EMAIL_SKIPPED)

    @Slot(bool)
    def _on_notification_sent(self, ok: bool):
        if self._closed:   # the e-mail can finish after logging out, when the view is gone
            return
        self.view.log_event(
            "INFO", Messages.EMAIL_SENT if ok else Messages.EMAIL_FAILED
        )
