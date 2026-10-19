from PySide6.QtCore import QDateTime, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.views.components.wordmark import Wordmark
from src.views.icons import icon
from src.views.theme import Colors, Size, Space


class Topbar(QFrame):
    """
    Application header: wordmark and section name on the left, a live clock and the
    signed-in user on the right. It is calm by design: it does not react to the
    monitoring state. Emits a signal when the user requests to sign out.
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

        # Presentation-only clock, refreshed once a second.
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._tick)
        self._clock_timer.start()
        self._tick()

    @staticmethod
    def _separator() -> QFrame:
        line = QFrame()
        line.setObjectName("topbarSep")
        line.setFixedSize(1, 28)
        return line

    def _build_session(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        avatar = QLabel(self.user_name[0].upper() if self.user_name else "U")
        avatar.setObjectName("avatar")
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        identity = QVBoxLayout()
        identity.setSpacing(1)
        identity.setContentsMargins(0, 0, 0, 0)
        identity.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        user_lbl = QLabel(self.user_name)
        user_lbl.setObjectName("userName")
        identity.addWidget(user_lbl)

        if self.user_role:
            role_lbl = QLabel(self.user_role)
            role_lbl.setObjectName("userRole")
            identity.addWidget(role_lbl)

        self.btn_logout = QPushButton("Sign out")
        self.btn_logout.setObjectName("ghost")
        self.btn_logout.setFixedHeight(Size.CONTROL)
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.setIcon(icon("logout", Colors.ON_GHOST, 16))
        self.btn_logout.setIconSize(QSize(16, 16))
        self.btn_logout.setToolTip("Sign out of this session")
        self.btn_logout.clicked.connect(self.logout_requested.emit)

        layout.addWidget(avatar)
        layout.addLayout(identity)
        layout.addSpacing(14)
        layout.addWidget(self.btn_logout)
        return container

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        row = QHBoxLayout()
        row.setContentsMargins(Space.PAGE, 0, Space.PAGE, 0)
        row.setSpacing(16)

        row.addWidget(Wordmark(self.app_name, self.app_tagline))
        row.addStretch()

        self.clock_label = QLabel("")
        self.clock_label.setObjectName("clock")
        self.clock_label.setToolTip("Local time")
        row.addWidget(self.clock_label)
        row.addSpacing(6)
        row.addWidget(self._separator())
        row.addSpacing(6)
        row.addWidget(self._build_session())
        outer.addLayout(row, 1)

    def _tick(self):
        self.clock_label.setText(QDateTime.currentDateTime().toString("yyyy-MM-dd  HH:mm:ss"))

    # ------------------------------------------------------------------ state
    # Kept so the owning view can keep calling them; the header shows no state indicator.
    def set_monitoring_state(self, active: bool):
        pass

    def set_alert_state(self, pulse_state: bool):
        pass
