from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from src.views.components.topbar import Topbar
from src.views.components.video_panel import VideoPanel
from src.views.components.system_status_card import SystemStatusCard
from src.views.components.event_log import EventLog
from src.views.components.stat_card import StatCard
from src.views.theme import Colors

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
    upload_requested = Signal(str)  # Señal para emitir la ruta del archivo de vídeo
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
        body_layout.setContentsMargins(24, 20, 24, 24)
        body_layout.setSpacing(20)

        video_area = QWidget()
        video_layout = QVBoxLayout(video_area)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_panel = VideoPanel(user_role=self.user_role)
        self.video_panel.start_requested.connect(self.start_requested.emit)
        self.video_panel.upload_requested.connect(self.upload_requested.emit)  # Conexión del botón de subida
        self.video_panel.stop_requested.connect(self.stop_requested.emit)
        
        video_layout.addWidget(self.video_panel, 1)
        body_layout.addWidget(video_area, 1)

        sidebar_panel = QWidget()
        sidebar_panel.setFixedWidth(340)
        sidebar_layout = QVBoxLayout(sidebar_panel)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(16)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.card_falls = StatCard("0", "FALLS TODAY", "stat_falls", Colors.DANGER)
        self.card_uptime = StatCard("00:00", "SESSION UPTIME", "stat_time", Colors.PRIMARY)
        stats_row.addWidget(self.card_falls)
        stats_row.addWidget(self.card_uptime)
        sidebar_layout.addLayout(stats_row)

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

    def set_monitoring_state(self, active: bool):
        self._is_monitoring = active
        self.video_panel.set_monitoring_state(active)
        self.topbar.set_monitoring_state(active)
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
        self.topbar.set_alert_state(self._pulse_state)
        self.system_status.set_alert_state(self._current_alert_msg, self._pulse_state)

    def clear_alert(self):
        self.alert_timer.stop()
        self.video_panel.reset_alert_state()
        self.set_monitoring_state(self._is_monitoring)

    def update_fall_count(self, count_str: str):
        self.card_falls.set_value(count_str)

    def update_uptime(self, time_str: str):
        self.card_uptime.set_value(time_str)

    def log_event(self, event_type: str, message: str):
        self.event_log.add_event(event_type, message)