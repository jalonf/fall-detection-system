from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from src.views.components.event_log import EventLog
from src.views.components.squeleton_panel import SkeletonPanel
from src.views.components.system_status_card import SystemStatusCard
from src.views.components.topbar import Topbar
from src.views.components.video_panel import VideoPanel

APP_NAME = "Safeguard"
APP_TAGLINE = "Fall Detection System"

class MonitorView(QWidget):
    """
    Main monitoring view orchestrator.
    Assembles independent UI components and manages global state 
    and data flow between them. Exposes system-level signals to controller.
    """
    
    logout_requested = Signal()
    start_requested = Signal(int)
    upload_requested = Signal(str)
    stop_requested = Signal()
    
    def __init__(self, user_name="User", user_role="Family / Caregiver", parent=None):
        super().__init__(parent)
        self.setObjectName("monitorScreen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.user_name = user_name
        self.user_role = user_role
        self._is_monitoring = False
        self._current_alert_msg = ""
        
        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self._pulse_alert)
        self._pulse_state = False
        
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        
        self.topbar = Topbar(APP_NAME, APP_TAGLINE, self.user_name)
        self.topbar.logout_requested.connect(self.logout_requested.emit)
        root.addWidget(self.topbar)

        body_wrapper = QWidget()
        body_wrapper.setObjectName("monitorBody")
        body_layout = QHBoxLayout(body_wrapper)
        body_layout.setContentsMargins(20, 16, 20, 20)
        body_layout.setSpacing(16)

        video_area = QWidget()
        video_layout = QVBoxLayout(video_area)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_panel = VideoPanel(user_role=self.user_role)
        self.video_panel.start_requested.connect(self.start_requested.emit)
        self.video_panel.upload_requested.connect(self.upload_requested.emit)
        self.video_panel.stop_requested.connect(self.stop_requested.emit)
        
        video_layout.addWidget(self.video_panel, 1)
        body_layout.addWidget(video_area, 1)

        sidebar_panel = QWidget()
        sidebar_panel.setFixedWidth(320)
        sidebar_layout = QVBoxLayout(sidebar_panel)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(12)
    
        self.skeleton_panel = SkeletonPanel()
        sidebar_layout.addWidget(self.skeleton_panel)
        
        self.system_status = SystemStatusCard()
        sidebar_layout.addWidget(self.system_status)

        self.event_log = EventLog()
        sidebar_layout.addWidget(self.event_log, 1)

        body_layout.addWidget(sidebar_panel, 0)
        root.addWidget(body_wrapper, 1)

    def update_video_frame(self, qimage):
        self.video_panel.update_frame(qimage)

    def clear_video(self):
        self.video_panel.clear_video()
        self.skeleton_panel.clear_video()

    def set_monitoring_state(self, active: bool):
        self._is_monitoring = active
        self.video_panel.set_monitoring_state(active)
        self.system_status.set_monitoring_state(active)

    def trigger_fall_alert(self, message="Possible fall detected"):
        self._current_alert_msg = message
        self.event_log.add_event("ALERT", message)
        
        self._pulse_state = False
        self.alert_timer.start(350)
        QTimer.singleShot(4000, self.clear_alert)

    def _pulse_alert(self):
        self._pulse_state = not self._pulse_state
        self.video_panel.set_alert_state(self._pulse_state)
        self.system_status.set_alert_state(self._current_alert_msg, self._pulse_state)

    def clear_alert(self):
        self.alert_timer.stop()
        self.video_panel.reset_alert_state()
        self.set_monitoring_state(self._is_monitoring)

    def update_uptime(self, time_str: str):
        pass

    def log_event(self, event_type: str, message: str):
        self.event_log.add_event(event_type, message)