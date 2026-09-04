from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


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
        layout.setContentsMargins(10, 0, 10, 0)
        layout.addStretch(1)

        title = QLabel("Welcome back")
        title.setObjectName("formTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(6)

        sub = QLabel("Sign in to your account to continue")
        sub.setObjectName("formSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)
        layout.addSpacing(32) 

        layout.addLayout(self._field("Email address", "login_email", "name@example.com"))
        layout.addSpacing(16)
        layout.addLayout(self._field("Password", "login_password", "••••••••", password=True))
        layout.addSpacing(32)

        self.btn_login = QPushButton("Sign In")
        self.btn_login.setObjectName("primary")
        self.btn_login.setFixedHeight(42)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_login.clicked.connect(self._emit_login)
        layout.addWidget(self.btn_login)
        layout.addSpacing(24)

        switch = QHBoxLayout()
        switch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch.setSpacing(6)
        q = QLabel("Don't have an account?")
        q.setStyleSheet("color: #6B7280; font-size: 13px;")
        link = QLabel("Sign up")
        link.setObjectName("link")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        
        link.mousePressEvent = lambda e: self.switch_page_requested.emit()
        
        switch.addWidget(q)
        switch.addWidget(link)
        layout.addLayout(switch)
        layout.addStretch(1) 

    def _field(self, label_text, attr_name, placeholder, password=False):
        col = QVBoxLayout()
        col.setSpacing(6)
        col.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label_text)
        lbl.setObjectName("fieldLabel")
        col.addWidget(lbl)
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(40)
        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        setattr(self, attr_name, edit)
        col.addWidget(edit)
        return col

    def _emit_login(self):
        self.login_requested.emit(
            self.login_email.text().strip(),
            self.login_password.text()
        )