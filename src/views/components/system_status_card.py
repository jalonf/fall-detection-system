from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from src.views.theme import apply_shadow, Colors

class SystemStatusCard(QFrame):
    """Component indicating the AI processing engine status with a clean structured layout."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCardNormal")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        apply_shadow(self, blur=6, y=2, alpha=6)
        self._build_ui()

    def _build_ui(self):
        sc_layout = QVBoxLayout(self)
        sc_layout.setContentsMargins(16, 12, 16, 12)
        sc_layout.setSpacing(6)

        sc_header_layout = QHBoxLayout()
        sc_title = QLabel("SYSTEM STATUS")
        sc_title.setObjectName("sectionTitle")
        
        self.sys_status_dot = QFrame()
        self.sys_status_dot.setFixedSize(7, 7)
        self.sys_status_dot.setObjectName("statusDot")
        
        self.detection_status = QLabel("Deactivated")
        self.detection_status.setObjectName("detectionStatus")
        
        sc_header_layout.addWidget(sc_title)
        sc_header_layout.addStretch()
        sc_header_layout.addWidget(self.sys_status_dot)
        sc_header_layout.addWidget(self.detection_status)
        sc_layout.addLayout(sc_header_layout)

        self.detection_detail = QLabel("System is ready. Awaiting video stream.")
        self.detection_detail.setObjectName("detectionDetail")
        self.detection_detail.setWordWrap(True)
        sc_layout.addWidget(self.detection_detail)

    def set_monitoring_state(self, active: bool):
        if active:
            self.sys_status_dot.setStyleSheet("background-color: #059669; border-radius: 3px;")
            self.detection_status.setText("Activated")
            self.detection_status.setStyleSheet("color: #059669; font-weight: 600;")
            self.detection_detail.setText("AI processing active. Looking for anomalies.")
        else:
            self.sys_status_dot.setStyleSheet("background-color: #9CA3AF; border-radius: 3px;")
            self.detection_status.setText("Deactivated")
            self.detection_status.setStyleSheet("color: #6B7280; font-weight: 600;")
            self.detection_detail.setText("System is ready. Awaiting video stream.")

    def set_alert_state(self, message: str, pulse_state: bool):
        color = Colors.DANGER if pulse_state else "#991B1B"
        self.detection_status.setText("CRITICAL ALERT")
        self.detection_detail.setText(message)
        self.detection_status.setStyleSheet(f"color: {color}; font-weight: 700;")
        self.sys_status_dot.setStyleSheet(f"background-color: {color}; border-radius: 3px;")