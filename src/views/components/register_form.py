from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QComboBox, QScrollArea
)

class RegisterForm(QWidget):
    """
    Component responsible for rendering the registration form interface.
    Allows new family members or medical staff to create an access account.
    """
    
    register_requested = Signal(str, str, str, str, str, str)  # Updated signature (no terms parameter)
    switch_page_requested = Signal()

    reg_name: QLineEdit
    reg_phone: QLineEdit
    reg_email: QLineEdit
    reg_password: QLineEdit
    reg_confirm: QLineEdit
    reg_role: QComboBox

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        inner = QWidget()
        inner.setObjectName("authPage")
        form = QVBoxLayout(inner)
        form.setContentsMargins(10, 24, 10, 24)
        form.setSpacing(0)
        form.addStretch(1)

        title = QLabel("Create an account")
        title.setObjectName("formTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(title)
        form.addSpacing(6)

        sub = QLabel("Set up your monitoring access")
        sub.setObjectName("formSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(sub)
        form.addSpacing(24)

        two_col = QHBoxLayout()
        two_col.setSpacing(12) 
        left = QVBoxLayout()
        left.addLayout(self._field("Full Name", "reg_name", "John Doe"))
        right = QVBoxLayout()
        right.addLayout(self._field("Phone", "reg_phone", "+1 234 567 8900"))
        two_col.addLayout(left, 1)
        two_col.addLayout(right, 1)
        form.addLayout(two_col)
        form.addSpacing(14)

        form.addLayout(self._field("Email address", "reg_email", "name@example.com"))
        form.addSpacing(14)

        two_col2 = QHBoxLayout()
        two_col2.setSpacing(12)
        l2 = QVBoxLayout()
        l2.addLayout(self._field("Password", "reg_password", "••••••••", password=True))
        r2 = QVBoxLayout()
        r2.addLayout(self._field("Confirm", "reg_confirm", "••••••••", password=True))
        two_col2.addLayout(l2, 1)
        two_col2.addLayout(r2, 1)
        form.addLayout(two_col2)
        form.addSpacing(14)

        role_label = QLabel("User Role")
        role_label.setObjectName("fieldLabel")
        form.addWidget(role_label)
        form.addSpacing(4)
        self.reg_role = QComboBox()
        self.reg_role.addItems(["Family / Caregiver", "Medical Staff", "Administrator"])
        self.reg_role.setFixedHeight(40)
        form.addWidget(self.reg_role)
        form.addSpacing(28)

        self.btn_register = QPushButton("Create account")
        self.btn_register.setObjectName("primary")
        self.btn_register.setFixedHeight(42)
        self.btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register.clicked.connect(self._emit_register)
        form.addWidget(self.btn_register)
        form.addSpacing(20)

        switch = QHBoxLayout()
        switch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch.setSpacing(6)
        q = QLabel("Already have an account?")
        q.setStyleSheet("color: #6B7280; font-size: 13px;")
        link = QLabel("Sign in")
        link.setObjectName("link")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        link.mousePressEvent = lambda e: self.switch_page_requested.emit()
        
        switch.addWidget(q)
        switch.addWidget(link)
        form.addLayout(switch)
        form.addStretch(1)

        scroll = QScrollArea()
        scroll.setObjectName("authScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

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

    def _emit_register(self):
        self.register_requested.emit(
            self.reg_name.text().strip(),
            self.reg_email.text().strip(),
            self.reg_phone.text().strip(),
            self.reg_password.text(),
            self.reg_confirm.text(),
            self.reg_role.currentText()
        )