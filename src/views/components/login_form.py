from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.views.components.auth_header import AuthHeader
from src.views.icons import attach_leading_icon, attach_password_toggle
from src.views.theme import Size


class LoginForm(QWidget):
    """
    Component responsible for rendering the login form interface.
    Captures user credentials to access the fall detection monitoring system.
    """

    login_requested = Signal(str, str)
    switch_page_requested = Signal()

    login_email: QLineEdit
    login_password: QLineEdit

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("authPage")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(6, 0, 6, 0)
        
        layout.addStretch(1)

        layout.addWidget(AuthHeader("Welcome back", "Sign in to your account to continue"))
        layout.addSpacing(34)

        layout.addLayout(self._field("Email address", "login_email", "name@example.com", icon_name="mail"))
        layout.addSpacing(20)
        layout.addLayout(self._field("Password", "login_password", "••••••••", password=True, icon_name="lock"))
        layout.addSpacing(32)

        self.btn_login = QPushButton("Sign In")
        self.btn_login.setObjectName("primary")
        self.btn_login.setFixedHeight(Size.FIELD)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_login.clicked.connect(self._emit_login)
        layout.addWidget(self.btn_login)
        layout.addSpacing(28)

        switch = QHBoxLayout()
        switch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch.setSpacing(6)
        q = QLabel("Don't have an account?")
        q.setObjectName("authHint")
        link = QLabel("Sign up")
        link.setObjectName("link")
        link.setCursor(Qt.CursorShape.PointingHandCursor)

        link.mousePressEvent = lambda e: self.switch_page_requested.emit()

        switch.addWidget(q)
        switch.addWidget(link)
        layout.addLayout(switch)
        
        layout.addStretch(1)

    def _field(self, label_text, attr_name, placeholder, password=False, icon_name=None):
        col = QVBoxLayout()
        col.setSpacing(8)
        col.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label_text)
        lbl.setObjectName("fieldLabel")
        col.addWidget(lbl)
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(Size.FIELD)
        if icon_name:
            attach_leading_icon(edit, icon_name)
        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            attach_password_toggle(edit)
            
        edit.returnPressed.connect(self._emit_login)
        setattr(self, attr_name, edit)
        col.addWidget(edit)
        return col

    def _emit_login(self):
        self.login_requested.emit(
            self.login_email.text().strip(),
            self.login_password.text()
        )