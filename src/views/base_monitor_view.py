from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from src.views.components.event_log import EventLog
from src.views.components.system_status_card import SystemStatusCard
from src.views.components.topbar import Topbar
from src.views.components.video_panel import VideoPanel
from src.views.theme import APP_NAME, Size, Space


class BaseMonitorView(QWidget):
    """
    Shared shell of the monitoring screens: topbar, video column (stream + camera
    configuration + controls) and a fixed-width sidebar with system status and
    the event log.

    Subclasses set `SCREEN_NAME` / `APP_TAGLINE` and may add panels to the top of
    the sidebar by overriding `_add_sidebar_panels`.
    """

    logout_requested = Signal()
    start_requested = Signal(int)
    stop_requested = Signal()
    notify_requested = Signal()
    upload_requested = Signal(str)

    SCREEN_NAME = "monitorScreen"
    APP_TAGLINE = ""

    def __init__(self, user_name, user_role, parent=None):
        super().__init__(parent)
        self.setObjectName(self.SCREEN_NAME)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.user_name = user_name
        self.user_role = user_role
        self._is_monitoring = False
        self._current_alert_msg = ""

        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self._pulse_alert)
        self._pulse_state = False

        self._build_ui()

    # ------------------------------------------------------------------ build
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.topbar = Topbar(APP_NAME, self.APP_TAGLINE, self.user_name, user_role=self.user_role)
        self.topbar.logout_requested.connect(self.logout_requested.emit)
        root.addWidget(self.topbar)

        body_wrapper = QWidget()
        body_wrapper.setObjectName("monitorBody")
        body_wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        body_layout = QHBoxLayout(body_wrapper)
        body_layout.setContentsMargins(Space.PAGE, Space.GUTTER, Space.PAGE, Space.PAGE)
        body_layout.setSpacing(Space.GUTTER)

        # Left column: video stream, camera configuration and controls
        self.video_panel = VideoPanel(user_role=self.user_role)
        self.video_panel.start_requested.connect(self.start_requested.emit)
        self.video_panel.stop_requested.connect(self.stop_requested.emit)
        self.video_panel.upload_requested.connect(self.upload_requested.emit)
        self.video_panel.notify_requested.connect(self.notify_requested.emit)
        body_layout.addWidget(self.video_panel, 1)

        # Right column: fixed-width sidebar
        sidebar_panel = QWidget()
        sidebar_panel.setFixedWidth(Size.SIDEBAR)
        sidebar_layout = QVBoxLayout(sidebar_panel)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(Space.GAP)

        self._add_sidebar_panels(sidebar_layout)

        self.system_status = SystemStatusCard()
        sidebar_layout.addWidget(self.system_status)

        self.event_log = EventLog()
        sidebar_layout.addWidget(self.event_log, 1)

        body_layout.addWidget(sidebar_panel, 0)
        root.addWidget(body_wrapper, 1)

    def _add_sidebar_panels(self, sidebar_layout):
        """Hook: add extra panels above the system status card."""

    # ------------------------------------------------------------------ video
    def update_video_frame(self, qimage):
        self.video_panel.update_frame(qimage)

    def clear_video(self):
        self.video_panel.clear_video()

    # ------------------------------------------------------------------ state
    def set_monitoring_state(self, active: bool):
        self._is_monitoring = active
        self.video_panel.set_monitoring_state(active)
        self.system_status.set_monitoring_state(active)
        self.topbar.set_monitoring_state(active)

    def trigger_fall_alert(self, message="Possible fall detected"):
        self._current_alert_msg = message
        self.event_log.add_event("ALERT", message)
        self.video_panel.show_fall_banner(message)

        self._pulse_state = False
        self.alert_timer.start(350)
        QTimer.singleShot(4000, self.clear_alert)

    def _pulse_alert(self):
        self._pulse_state = not self._pulse_state
        self.video_panel.set_alert_state(self._pulse_state)
        self.system_status.set_alert_state(self._current_alert_msg, self._pulse_state)
        self.topbar.set_alert_state(self._pulse_state)

    def clear_alert(self):
        self.alert_timer.stop()
        self.video_panel.reset_alert_state()
        self.set_monitoring_state(self._is_monitoring)

    def update_fall_count(self, count_str: str):
        # Kept for API compatibility: callers may still invoke it.
        pass

    def log_event(self, event_type: str, message: str):
        self.event_log.add_event(event_type, message)
