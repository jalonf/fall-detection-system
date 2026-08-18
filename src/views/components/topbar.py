from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from src.views.theme import Colors

class Topbar(QFrame):
    """
    Component for the application header, branding, and user session controls.
    Emits a signal when the user requests to sign out.
    """
    
    logout_requested = Signal()
    
    def __init__(self, app_name, app_tagline, user_name, parent=None):
        super().__init__(parent)
        self.setObjectName("topbar")
        self.setFixedHeight(70)
        self.user_name = user_name
        self.app_name = app_name
        self.app_tagline = app_tagline
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(36, 0, 36, 0)
        layout.setSpacing(0)

        logo_mark = QLabel(self.app_name[0].upper())
        logo_mark.setObjectName("brandMark")
        logo_mark.setFixedSize(36, 36)
        logo_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_mark.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        brand_text.setContentsMargins(0, 0, 0, 0)
        logo = QLabel(self.app_name)
        logo.setObjectName("appTitle")
        tagline = QLabel(self.app_tagline)
        tagline.setObjectName("appSubtitle")
        brand_text.addWidget(logo)
        brand_text.addWidget(tagline)

        layout.addWidget(logo_mark)
        layout.addSpacing(12)
        layout.addLayout(brand_text)
        layout.addStretch()

        self.status_badge = QFrame()
        self.status_badge.setObjectName("statusBadgeIdle")
        badge_layout = QHBoxLayout(self.status_badge)
        badge_layout.setContentsMargins(12, 0, 14, 0)
        badge_layout.setSpacing(8)
        self.status_dot = QFrame()
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet("background-color: #94A3B8; border-radius: 4px;")
        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("statusText")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B; background: transparent;")
        badge_layout.addWidget(self.status_dot)
        badge_layout.addWidget(self.status_label)
        layout.addWidget(self.status_badge)

        sep = QFrame()
        sep.setObjectName("topbarSep")
        sep.setFixedSize(1, 26)
        layout.addSpacing(18)
        layout.addWidget(sep)
        layout.addSpacing(18)

        avatar = QLabel(self.user_name[0].upper() if self.user_name else "U")
        avatar.setObjectName("avatar")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_lbl = QLabel(self.user_name)
        user_lbl.setObjectName("userName")

        layout.addWidget(avatar)
        layout.addSpacing(10)
        layout.addWidget(user_lbl)
        layout.addSpacing(24)

        self.btn_logout = QPushButton("Sign Out")
        self.btn_logout.setObjectName("ghost")
        self.btn_logout.setFixedHeight(34)
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.clicked.connect(self.logout_requested.emit)
        layout.addWidget(self.btn_logout)

    def set_monitoring_state(self, active: bool):
        if active:
            self.status_dot.setStyleSheet(f"background-color: {Colors.PRIMARY}; border-radius: 4px;")
            self.status_label.setText("Monitoring")
            self.status_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {Colors.PRIMARY}; background: transparent;")
            self._swap_object_name(self.status_badge, "statusBadgeActive")
        else:
            self.status_dot.setStyleSheet("background-color: #94A3B8; border-radius: 4px;")
            self.status_label.setText("Idle")
            self.status_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B; background: transparent;")
            self._swap_object_name(self.status_badge, "statusBadgeIdle")

    def set_alert_state(self, pulse_state: bool):
        color = Colors.DANGER if pulse_state else "#7F1D1D"
        self._swap_object_name(self.status_badge, "statusBadgeAlert")
        self.status_dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        self.status_label.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {color}; background: transparent;")

    def _swap_object_name(self, widget, name: str):
        widget.setObjectName(name)
        widget.style().unpolish(widget)
        widget.style().polish(widget)