from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.views.icons import icon
from src.views.theme import Colors


class Topbar(QFrame):
    """
    Component for the application header, branding, and user session controls.
    Emits a signal when the user requests to sign out.
    """

    logout_requested = Signal()

    def __init__(self, app_name, app_tagline, user_name, parent=None, *, user_role=""):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("topbar")
        self.setFixedHeight(80)
        self.user_name = user_name
        self.user_role = user_role
        self.app_name = app_name
        self.app_tagline = app_tagline
        self._build_ui()

    @staticmethod
    def _separator() -> QFrame:
        line = QFrame()
        line.setObjectName("topbarSep")
        line.setFixedSize(1, 24)
        return line

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 20, 0)
        layout.setSpacing(16)

        # ---- Brand (left) ----
        brand_container = QWidget()
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(12)
        brand_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        brand_mark = QLabel()
        brand_mark.setObjectName("brandMark")

        base_dir = Path(__file__).resolve().parent.parent
        logo_path = base_dir / "assets" / "logo.png"

        if logo_path.exists():
            logo_pixmap = QPixmap(str(logo_path))
            
            logo_escaled = logo_pixmap.scaled(
                70, 70, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            brand_mark.setPixmap(logo_escaled)
            brand_mark.setStyleSheet("background: transparent;")

        brand_mark.setFixedSize(70, 70)
        brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        brand_text.setContentsMargins(0, 0, 0, 0)
        brand_text.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        logo = QLabel(self.app_name)
        logo.setObjectName("appTitle")
        
        tagline = QLabel(self.app_tagline)
        tagline.setObjectName("appSubtitle")

        brand_text.addWidget(logo)
        brand_text.addWidget(tagline)

        brand_layout.addWidget(brand_mark)
        brand_layout.addLayout(brand_text)
        layout.addWidget(brand_container)

        layout.addStretch()

        # ---- Session (right) ----
        user_container = QWidget()
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(12)
        user_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        avatar = QLabel(self.user_name[0].upper() if self.user_name else "U")
        avatar.setObjectName("avatar")
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        identity = QVBoxLayout()
        identity.setSpacing(2)
        identity.setContentsMargins(0, 0, 0, 0)
        identity.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        user_lbl = QLabel(self.user_name)
        user_lbl.setObjectName("userName")
        identity.addWidget(user_lbl)

        if self.user_role:
            role_lbl = QLabel(self.user_role)
            role_lbl.setObjectName("userRole")
            identity.addWidget(role_lbl)

        self.btn_logout = QPushButton("Sign Out")
        self.btn_logout.setObjectName("ghost")
        self.btn_logout.setFixedHeight(38)
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.setIcon(icon("logout", Colors.PRIMARY, 18))
        self.btn_logout.setIconSize(QSize(18, 18))
        self.btn_logout.clicked.connect(self.logout_requested.emit)

        user_layout.addWidget(avatar)
        user_layout.addLayout(identity)
        user_layout.addSpacing(24)
        user_layout.addWidget(self.btn_logout)

        layout.addWidget(user_container)

    def set_monitoring_state(self, active: bool):
        pass

    def set_alert_state(self, pulse_state: bool):
        pass