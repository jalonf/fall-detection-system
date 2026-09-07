import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class RegisterForm(QWidget):
    """
    Component responsible for rendering the registration form interface.
    Handles user input validation and emits signals for account creation.
    """
    
    register_requested = Signal(str, str, str, str, str, str, str)
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
        form.setContentsMargins(16, 12, 16, 12)  # Reduced vertical padding to avoid excessive whitespace
        form.setSpacing(6)                       # Compact global spacing
        form.addStretch(1)

        title = QLabel("Create an account")
        title.setObjectName("formTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(title)
        
        sub = QLabel("Set up your monitoring access")
        sub.setObjectName("formSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(sub)
        form.addSpacing(2)

        # --- SECTION 1: CAREGIVER & ACCOUNT INFORMATION ---
        sec1_lbl = QLabel("Caregiver Information")
        sec1_lbl.setStyleSheet("font-weight: 700; color: #1E3A8A; font-size: 13px; margin-top: 2px; margin-bottom: 0px;")
        form.addWidget(sec1_lbl)

        # Row 1: Name & Phone
        row_cg_1 = QHBoxLayout()
        row_cg_1.setSpacing(12)
        
        left_1 = QVBoxLayout()
        left_1.setAlignment(Qt.AlignmentFlag.AlignTop)
        c_name_layout, self.reg_name, self.reg_name_err = self._field("Full Name", "John Doe")
        left_1.addLayout(c_name_layout)
        
        right_1 = QVBoxLayout()
        right_1.setAlignment(Qt.AlignmentFlag.AlignTop)
        c_phone_layout, self.reg_phone, self.reg_phone_err = self._field("Phone", "+1 234 567 8900")
        right_1.addLayout(c_phone_layout)
        
        row_cg_1.addLayout(left_1, 1)
        row_cg_1.addLayout(right_1, 1)
        form.addLayout(row_cg_1)

        # Email field with integrated help text
        email_layout, self.reg_email, self.reg_email_err = self._field(
            "Email address", 
            "name@example.com", 
            help_text="This email will be used to receive fall alerts and system notifications."
        )
        form.addLayout(email_layout)

        # Row 2: Password & Confirm
        row_cg_2 = QHBoxLayout()
        row_cg_2.setSpacing(12)
        
        left_2 = QVBoxLayout()
        left_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        pass_layout, self.reg_password, self.reg_password_err = self._field("Password", "••••••••", password=True)
        left_2.addLayout(pass_layout)
        
        right_2 = QVBoxLayout()
        right_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        conf_layout, self.reg_confirm, self.reg_confirm_err = self._field("Confirm", "••••••••", password=True)
        right_2.addLayout(conf_layout)
        
        row_cg_2.addLayout(left_2, 1)
        row_cg_2.addLayout(right_2, 1)
        form.addLayout(row_cg_2)

        # User Role Dropdown
        role_label = QLabel("User Role")
        role_label.setObjectName("fieldLabel")
        form.addWidget(role_label)
        self.reg_role = QComboBox()
        self.reg_role.addItems(["Family / Caregiver", "Medical Staff", "Administrator"])
        self.reg_role.setFixedHeight(36)  # Compact height
        form.addWidget(self.reg_role)
        form.addSpacing(2)

        # --- SECTION 2: PATIENT INFORMATION ---
        sec2_lbl = QLabel("Patient Information")
        sec2_lbl.setStyleSheet("font-weight: 700; color: #1E3A8A; font-size: 13px; margin-top: 4px; margin-bottom: 0px;")
        form.addWidget(sec2_lbl)

        # Row 3: Patient Name & Medical Notes/Information (Replaced patient phone)
        row_pat = QHBoxLayout()
        row_pat.setSpacing(12)
        
        left_pat = QVBoxLayout()
        left_pat.setAlignment(Qt.AlignmentFlag.AlignTop)
        pat_name_layout, self.reg_patient_name, self.reg_patient_name_err = self._field("Patient Full Name", "Jane Doe")
        left_pat.addLayout(pat_name_layout)
        
        right_pat = QVBoxLayout()
        right_pat.setAlignment(Qt.AlignmentFlag.AlignTop)
        pat_med_layout, self.reg_medical_info, self.reg_medical_info_err = self._field("Medical Notes (Optional)", "e.g., Vertigo, reduced mobility")
        right_pat.addLayout(pat_med_layout)
        
        row_pat.addLayout(left_pat, 1)
        row_pat.addLayout(right_pat, 1)
        form.addLayout(row_pat)
        
        form.addSpacing(4)

        # Submit Button
        self.btn_register = QPushButton("Create account")
        self.btn_register.setObjectName("primary")
        self.btn_register.setFixedHeight(40)
        self.btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register.clicked.connect(self._emit_register)
        form.addWidget(self.btn_register)
        form.addSpacing(4)

        # Footer: Sign In Link
        switch = QHBoxLayout()
        switch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch.setSpacing(6)
        q = QLabel("Already have an account?")
        q.setStyleSheet("color: #6B7280; font-size: 13px;")
        link = QLabel("Sign in")
        link.setObjectName("link")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Connected to a proper helper method to satisfy type checking and return types
        link.mousePressEvent = self._handle_sign_in
        
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

    def _field(self, label_text, placeholder, password=False, help_text=None):
        """
        Generates a standard form field layout and returns the layout, input widget, and error label.
        """
        col = QVBoxLayout()
        col.setSpacing(2)
        col.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(label_text)
        lbl.setObjectName("fieldLabel")
        col.addWidget(lbl)
        
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(36)
        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        col.addWidget(edit)
        
        err_lbl = QLabel(help_text if help_text else "")
        if help_text:
            err_lbl.setStyleSheet("color: #4B5563; font-size: 11px; margin-top: 1px;")
            err_lbl.setVisible(True)
        else:
            err_lbl.setStyleSheet("color: #DC2626; font-size: 11px; margin-top: 1px;")
            err_lbl.setVisible(False)
            
        err_lbl.setWordWrap(True)
        err_lbl.setMinimumHeight(18)
        err_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        sp = err_lbl.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        err_lbl.setSizePolicy(sp)
        col.addWidget(err_lbl)
        
        return col, edit, err_lbl

    def _handle_sign_in(self, event):
        """Resets the form and triggers the page switch to login."""
        self.reset_form()
        self.switch_page_requested.emit()

    def reset_form(self):
        """Resets all input fields and clears/restores error and helper messages."""
        self.reg_name.clear()
        self.reg_phone.clear()
        self.reg_email.clear()
        self.reg_password.clear()
        self.reg_confirm.clear()
        self.reg_patient_name.clear()
        self.reg_medical_info.clear()
        self.reg_role.setCurrentIndex(0)

        # Restore email help text and styling
        self.reg_email_err.setText("This email will be used to receive fall alerts and system notifications.")
        self.reg_email_err.setStyleSheet("color: #4B5563; font-size: 11px; margin-top: 1px;")
        self.reg_email_err.setVisible(True)

        # Hide all other error labels
        error_labels = [
            self.reg_name_err, self.reg_phone_err, 
            self.reg_password_err, self.reg_confirm_err,
            self.reg_patient_name_err, self.reg_medical_info_err
        ]
        for lbl in error_labels:
            lbl.setVisible(False)
            lbl.setText("")

    def _clear_errors(self):
        """Clears all inline error messages and hides the error labels."""
        self.reg_email_err.setText("This email will be used to receive fall alerts and system notifications.")
        self.reg_email_err.setStyleSheet("color: #4B5563; font-size: 11px; margin-top: 1px;")
        self.reg_email_err.setVisible(True)

        error_labels = [
            self.reg_name_err, self.reg_phone_err, 
            self.reg_password_err, self.reg_confirm_err,
            self.reg_patient_name_err, self.reg_medical_info_err
        ]
        for lbl in error_labels:
            lbl.setVisible(False)
            lbl.setText("")

    def _show_field_error(self, err_lbl: QLabel, message: str):
        """Displays a specific error message on the target label."""
        err_lbl.setStyleSheet("color: #DC2626; font-size: 11px; margin-top: 1px;")
        err_lbl.setText(message)
        err_lbl.setVisible(True)

    def _validate_inputs(self) -> bool:
        """
        Validates all user inputs based on format and security requirements.
        """
        self._clear_errors()
        is_valid = True
        
        name = self.reg_name.text().strip()
        email = self.reg_email.text().strip()
        phone = self.reg_phone.text().strip()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()
        patient_name = self.reg_patient_name.text().strip()

        if not name:
            self._show_field_error(self.reg_name_err, "Caregiver name is required.")
            is_valid = False
            
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$", email):
            self._show_field_error(self.reg_email_err, "Enter a valid email address.")
            is_valid = False
            
        if not re.match(r"^\+\d{1,3}(?:[\s.-]?\d){6,14}$", phone):
            self._show_field_error(self.reg_phone_err, "Include international prefix (+1) and a valid number.")
            is_valid = False
            
        if not patient_name:
            self._show_field_error(self.reg_patient_name_err, "Patient name is required.")
            is_valid = False

        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$", password):
            self._show_field_error(self.reg_password_err, "Min 8 chars, 1 uppercase, 1 number, 1 special symbol.")
            is_valid = False
            
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
                self.reg_role.currentText(),
                self.reg_patient_name.text().strip(),
                self.reg_medical_info.text().strip()
            )