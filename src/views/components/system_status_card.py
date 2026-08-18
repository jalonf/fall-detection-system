from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from src.views.theme import apply_shadow, Colors

class SystemStatusCard(QFrame):
    """Component indicating the AI processing engine status."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCardNormal")
        self.setStyleSheet("""
            QFrame#statusCardNormal { 
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                border-left: 4px solid #94A3B8;
            }
        """)
        apply_shadow(self, blur=10, y=2, alpha=4)
        self._build_ui()

    def _build_ui(self):
        sc_layout = QVBoxLayout(self)
        sc_layout.setContentsMargins(18, 14, 18, 14)
        sc_layout.setSpacing(6)

        sc_header_layout = QHBoxLayout()
        sc_title = QLabel("SYSTEM STATUS")
        sc_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        
        self.sys_status_dot = QFrame()
        self.sys_status_dot.setFixedSize(8, 8)
        self.sys_status_dot.setStyleSheet("background-color: #94A3B8; border-radius: 4px;")
        
        self.detection_status = QLabel("Deactivated")
        self.detection_status.setStyleSheet("font-size: 12px; font-weight: 700; color: #475569;")
        
        sc_header_layout.addWidget(sc_title)
        sc_header_layout.addStretch()
        sc_header_layout.addWidget(self.sys_status_dot)
        sc_header_layout.addWidget(self.detection_status)
        sc_layout.addLayout(sc_header_layout)

        self.detection_detail = QLabel("System is ready. Awaiting video stream.")
        self.detection_detail.setStyleSheet("color: #64748B; font-size: 12px;")
        self.detection_detail.setWordWrap(True)
        sc_layout.addWidget(self.detection_detail)

    def set_monitoring_state(self, active: bool):
        if active:
            self.sys_status_dot.setStyleSheet("background-color: #10B981; border-radius: 4px;")
            self.detection_status.setText("Activated")
            self.detection_status.setStyleSheet("font-size: 12px; font-weight: 700; color: #10B981;")
            self.setStyleSheet("QFrame#statusCardNormal { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; border-left: 4px solid #10B981; }")
            self.detection_detail.setText("AI processing active. Looking for anomalies.")
        else:
            self.sys_status_dot.setStyleSheet("background-color: #94A3B8; border-radius: 4px;")
            self.detection_status.setText("Deactivated")
            self.detection_status.setStyleSheet("font-size: 12px; font-weight: 700; color: #475569;")
            self.setStyleSheet("QFrame#statusCardNormal { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; border-left: 4px solid #94A3B8; }")
            self.detection_detail.setText("System is ready. Awaiting video stream.")

    def set_alert_state(self, message: str, pulse_state: bool):
        color = Colors.DANGER if pulse_state else "#7F1D1D"
        self.detection_status.setText("CRITICAL ALERT")
        self.detection_detail.setText(message)
        self.detection_status.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {color};")
        self.sys_status_dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        self.setStyleSheet(f"QFrame#statusCardNormal {{ background-color: #FEF2F2; border: 1px solid #FECACA; border-radius: 6px; border-left: 4px solid {color}; }}")