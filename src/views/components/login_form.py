from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QCheckBox
)

class LoginForm(QWidget):
    """
    Component responsible for rendering the login form interface.
    Captures user credentials to access the fall detection monitoring system.
    """
    
    # Declare native signals
    login_requested = Signal(str, str, bool)
    switch_page_requested = Signal()
    
    login_email: QLineEdit
    login_password: QLineEdit
    remember: QCheckBox
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("authPage")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        title = QLabel("Welcome back")
        title.setObjectName("formTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(8)

        sub = QLabel("Sign in to your account to continue")
        sub.setObjectName("formSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)
        layout.addSpacing(32) 

        layout.addLayout(self._field("Email address", "login_email", "name@example.com"))
        layout.addSpacing(16)
        layout.addLayout(self._field("Password", "login_password", "••••••••", password=True))
        layout.addSpacing(16)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        self.remember = QCheckBox("Remember me")
        forgot = QLabel("Forgot password?")
        forgot.setObjectName("link")
        forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        row.addWidget(self.remember)
        row.addStretch()
        row.addWidget(forgot)
        layout.addLayout(row)
        layout.addSpacing(28)

        self.btn_login = QPushButton("Sign In")
        self.btn_login.setObjectName("success")
        self.btn_login.setFixedHeight(46)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Connect button click to internal method
        self.btn_login.clicked.connect(self._emit_login)
        layout.addWidget(self.btn_login)
        layout.addSpacing(24)

        switch = QHBoxLayout()
        switch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch.setSpacing(6)
        q = QLabel("Don't have an account?")
        q.setStyleSheet("color: #64748B; font-size: 13px;")
        link = QLabel("Sign up")
        link.setObjectName("link")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Emit signal to request page switch
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
        edit.setFixedHeight(44)
        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        setattr(self, attr_name, edit)
        col.addWidget(edit)
        return col

    def _emit_login(self):
        # Emit signal with captured data
        self.login_requested.emit(
            self.login_email.text().strip(),
            self.login_password.text(),
            self.remember.isChecked()
        )