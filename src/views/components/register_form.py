import re
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QComboBox, QScrollArea,
    QSizePolicy
)

class RegisterForm(QWidget):
    """
    Component responsible for rendering the registration form interface.
    Handles user input validation and emits signals for account creation.
    """
    
    register_requested = Signal(str, str, str, str, str, str)
    switch_page_requested = Signal()

    def __init__(self, parent=None):
        """Initializes the RegisterForm widget and builds the UI layout."""
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        """Constructs the main user interface components and layouts."""
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

        # Row 1: Name and Phone Fields
        two_col = QHBoxLayout()
        two_col.setSpacing(12) 
        
        left = QVBoxLayout()
        left.setAlignment(Qt.AlignmentFlag.AlignTop)
        name_layout, self.reg_name, self.reg_name_err = self._field("Full Name", "John Doe")
        left.addLayout(name_layout)
        
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignTop)
        phone_layout, self.reg_phone, self.reg_phone_err = self._field("Phone", "+1 234 567 8900")
        right.addLayout(phone_layout)
        
        two_col.addLayout(left, 1)
        two_col.addLayout(right, 1)
        form.addLayout(two_col)

        # Row 2: Email Field
        email_layout, self.reg_email, self.reg_email_err = self._field("Email address", "name@example.com")
        form.addLayout(email_layout)

        # Row 3: Password and Confirmation Fields
        two_col2 = QHBoxLayout()
        two_col2.setSpacing(12)
        
        l2 = QVBoxLayout()
        l2.setAlignment(Qt.AlignmentFlag.AlignTop)
        pass_layout, self.reg_password, self.reg_password_err = self._field("Password", "••••••••", password=True)
        l2.addLayout(pass_layout)
        
        r2 = QVBoxLayout()
        r2.setAlignment(Qt.AlignmentFlag.AlignTop)
        conf_layout, self.reg_confirm, self.reg_confirm_err = self._field("Confirm", "••••••••", password=True)
        r2.addLayout(conf_layout)
        
        two_col2.addLayout(l2, 1)
        two_col2.addLayout(r2, 1)
        form.addLayout(two_col2)

        # Row 4: User Role Dropdown
        role_label = QLabel("User Role")
        role_label.setObjectName("fieldLabel")
        form.addWidget(role_label)
        form.addSpacing(4)
        self.reg_role = QComboBox()
        self.reg_role.addItems(["Family / Caregiver", "Medical Staff", "Administrator"])
        self.reg_role.setFixedHeight(40)
        form.addWidget(self.reg_role)
        form.addSpacing(28)

        # Submit Button
        self.btn_register = QPushButton("Create account")
        self.btn_register.setObjectName("primary")
        self.btn_register.setFixedHeight(42)
        self.btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register.clicked.connect(self._emit_register)
        form.addWidget(self.btn_register)
        form.addSpacing(20)

        # Footer: Sign In Link
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

        # Scroll Area Setup
        scroll = QScrollArea()
        scroll.setObjectName("authScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

    def _field(self, label_text, placeholder, password=False):
        """
        Generates a standard form field layout and returns the layout, input widget, and error label.
        """
        col = QVBoxLayout()
        col.setSpacing(4)
        col.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(label_text)
        lbl.setObjectName("fieldLabel")
        col.addWidget(lbl)
        
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(40)
        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        col.addWidget(edit)
        
        err_lbl = QLabel("")
        err_lbl.setStyleSheet("color: #DC2626; font-size: 11px; margin-top: 2px;")
        err_lbl.setVisible(False)
        err_lbl.setWordWrap(True)
        
        err_lbl.setMinimumHeight(32)
        err_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        sp = err_lbl.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        err_lbl.setSizePolicy(sp)
        col.addWidget(err_lbl)
        
        return col, edit, err_lbl

    def _clear_errors(self):
        """Clears all inline error messages and hides the error labels."""
        error_labels = [
            self.reg_name_err, self.reg_phone_err, 
            self.reg_email_err, self.reg_password_err, self.reg_confirm_err
        ]
        for lbl in error_labels:
            lbl.setVisible(False)
            lbl.setText("")

    def _show_field_error(self, err_lbl: QLabel, message: str):
        """Displays a specific error message on the target label."""
        err_lbl.setText(message)
        err_lbl.setVisible(True)

    def _validate_inputs(self) -> bool:
        """
        Validates all user inputs based on format and security requirements.
        """
        self._clear_errors()
        is_valid = True
        
        # 1. Extract and clean field values
        name = self.reg_name.text().strip()
        email = self.reg_email.text().strip()
        phone = self.reg_phone.text().strip()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()

        # 2. Validate Name
        if not name:
            self._show_field_error(self.reg_name_err, "Name is required.")
            is_valid = False
            
        # 3. Validate Email
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$", email):
            self._show_field_error(self.reg_email_err, "Enter a valid email address.")
            is_valid = False
            
        # 4. Validate Phone
        if not re.match(r"^\+\d{1,3}(?:[\s.-]?\d){6,14}$", phone):
            self._show_field_error(self.reg_phone_err, "Include international prefix (+1) and a valid number.")
            is_valid = False
            
        # 5. Validate Password
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$", password):
            self._show_field_error(self.reg_password_err, "Min 8 chars, 1 uppercase, 1 number, 1 special symbol.")
            is_valid = False
            
        # 6. Validate Password Confirmation
        if not confirm or confirm != password:
            self._show_field_error(self.reg_confirm_err, "Passwords do not match.")
            is_valid = False

        return is_valid

    def _emit_register(self):
        """Triggers the validation process and emits the registration signal if successful."""
        if self._validate_inputs():
            self.register_requested.emit(
                self.reg_name.text().strip(),
                self.reg_email.text().strip(),
                self.reg_phone.text().strip(),
                self.reg_password.text(),
                self.reg_confirm.text(),
                self.reg_role.currentText()
            )