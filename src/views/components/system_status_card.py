from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from src.views.theme import set_prop


class SystemStatusCard(QFrame):
    """Component indicating the AI processing engine status with a clean structured layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply("idle", "off")

    def _build_ui(self):
        sc_layout = QVBoxLayout(self)
        sc_layout.setContentsMargins(18, 16, 18, 16)
        sc_layout.setSpacing(8)

        sc_header_layout = QHBoxLayout()
        sc_header_layout.setSpacing(8)
        sc_title = QLabel("System status")
        sc_title.setObjectName("sectionTitle")

        self.sys_status_dot = QFrame()
        self.sys_status_dot.setFixedSize(8, 8)
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

    def _apply(self, state: str, pulse: str):
        for widget in (self, self.sys_status_dot, self.detection_status, self.detection_detail):
            set_prop(widget, "state", state)
            set_prop(widget, "pulse", pulse)

    def set_monitoring_state(self, active: bool):
        if active:
            self._apply("active", "off")
            self.detection_status.setText("Activated")
            self.detection_detail.setText("AI processing active. Looking for anomalies.")
        else:
            self._apply("idle", "off")
            self.detection_status.setText("Deactivated")
            self.detection_detail.setText("System is ready. Awaiting video stream.")

    def set_alert_state(self, message: str, pulse_state: bool):
        self._apply("alert", "on" if pulse_state else "off")
        self.detection_status.setText("Critical alert")
        self.detection_detail.setText(message)
