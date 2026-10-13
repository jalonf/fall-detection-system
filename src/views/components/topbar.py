from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.views.icons import icon
from src.views.theme import Colors, Size, brand_logo


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
        self.setFixedHeight(Size.TOPBAR)
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

    def _build_brand(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Logo when the asset exists, otherwise a lettermark tile (styled in QSS).
        brand_mark = QLabel()
        brand_mark.setObjectName("brandMark")
        logo = brand_logo(Size.LOGO_TOPBAR)
        if logo is not None:
            brand_mark.setPixmap(logo)
            brand_mark.setProperty("hasLogo", True)
        else:
            brand_mark.setText(self.app_name[:1].upper())
        brand_mark.setFixedSize(Size.LOGO_TOPBAR, Size.LOGO_TOPBAR)
        brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text = QVBoxLayout()
        text.setSpacing(1)
        text.setContentsMargins(0, 0, 0, 0)
        text.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title = QLabel(self.app_name)
        title.setObjectName("appTitle")
        tagline = QLabel(self.app_tagline)
        tagline.setObjectName("appSubtitle")
        text.addWidget(title)
        text.addWidget(tagline)

        layout.addWidget(brand_mark)
        layout.addLayout(text)
        return container

    def _build_session(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

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
        self.btn_logout.setFixedHeight(Size.CONTROL)
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.setIcon(icon("logout", Colors.ON_GHOST, 18))
        self.btn_logout.setIconSize(QSize(18, 18))
        self.btn_logout.clicked.connect(self.logout_requested.emit)

        layout.addWidget(avatar)
        layout.addLayout(identity)
        layout.addSpacing(12)
        layout.addWidget(self._separator())
        layout.addSpacing(12)
        layout.addWidget(self.btn_logout)
        return container

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 20, 0)
        layout.setSpacing(16)

        layout.addWidget(self._build_brand())
        layout.addStretch()
        layout.addWidget(self._build_session())

    def set_monitoring_state(self, active: bool):
        pass

    def set_alert_state(self, pulse_state: bool):
        pass
