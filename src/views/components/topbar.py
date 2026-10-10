from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Topbar(QFrame):
    """
    Component for the application header, branding, and user session controls.
    Emits a signal when the user requests to sign out.
    """
    
    logout_requested = Signal()
    
    def __init__(self, app_name, app_tagline, user_name, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("topbar")
        self.setFixedHeight(64)
        self.user_name = user_name
        self.app_name = app_name
        self.app_tagline = app_tagline
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        # Contenedor izquierdo para marca y logotipo
        brand_container = QWidget()
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(12)
        brand_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        logo_mark = QLabel(self.app_name[0].upper())
        logo_mark.setObjectName("brandMark")
        logo_mark.setFixedSize(32, 32)
        logo_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_mark.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand_text.setContentsMargins(0, 0, 0, 0)
        brand_text.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        logo = QLabel(self.app_name)
        logo.setObjectName("appTitle")
        
        tagline = QLabel(self.app_tagline)
        tagline.setObjectName("appSubtitle")
        
        brand_text.addWidget(logo)
        brand_text.addWidget(tagline)

        brand_layout.addWidget(logo_mark)
        brand_layout.addLayout(brand_text)
        layout.addWidget(brand_container)

        layout.addStretch()

        # Contenedor derecho para el perfil de usuario y cierre de sesión
        user_container = QWidget()
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(10)
        user_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        avatar = QLabel(self.user_name[0].upper() if self.user_name else "U")
        avatar.setObjectName("avatar")
        avatar.setFixedSize(30, 30)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        user_lbl = QLabel(self.user_name)
        user_lbl.setObjectName("userName")

        self.btn_logout = QPushButton("Sign Out")
        self.btn_logout.setObjectName("ghost")
        self.btn_logout.setFixedHeight(32)
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.clicked.connect(self.logout_requested.emit)

        user_layout.addWidget(avatar)
        user_layout.addWidget(user_lbl)
        user_layout.addSpacing(8)
        user_layout.addWidget(self.btn_logout)

        layout.addWidget(user_container)

    def set_monitoring_state(self, active: bool):
        pass

    def set_alert_state(self, pulse_state: bool):
        pass