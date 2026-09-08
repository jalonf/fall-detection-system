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
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setObjectName("authScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        inner = QWidget()
        inner.setObjectName("authPage")

        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(0)

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        layout.addStretch(1)

        title = QLabel("Create an account")
        title.setObjectName("formTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(4)

        subtitle = QLabel("Set up your monitoring access")
        subtitle.setObjectName("formSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # -------------------------------------------------
        # CAREGIVER INFORMATION
        # -------------------------------------------------

        section = QLabel("Caregiver information")
        section.setObjectName("sectionTitle")
        layout.addWidget(section)

        layout.addSpacing(8)

        # Name / Phone
        row = QHBoxLayout()
        row.setSpacing(16)
        row.setAlignment(Qt.AlignmentFlag.AlignTop)

        name_layout, self.reg_name, self.reg_name_err = self._field(
            "Full name",
            "John Doe"
        )

        phone_layout, self.reg_phone, self.reg_phone_err = self._field(
            "Phone",
            "+1 234 567 8900"
        )

        row.addLayout(name_layout, 1)
        row.addLayout(phone_layout, 1)

        layout.addLayout(row)

        layout.addSpacing(10)

        # Email
        email_layout, self.reg_email, self.reg_email_err = self._field(
            "Email address",
            "name@example.com",
            help_text="Used for fall alerts and system notifications."
        )

        layout.addLayout(email_layout)

        layout.addSpacing(10)

        # Password / Confirm
        row = QHBoxLayout()
        row.setSpacing(16)
        row.setAlignment(Qt.AlignmentFlag.AlignTop)

        password_layout, self.reg_password, self.reg_password_err = self._field(
            "Password",
            "••••••••",
            password=True
        )

        confirm_layout, self.reg_confirm, self.reg_confirm_err = self._field(
            "Confirm password",
            "••••••••",
            password=True
        )

        row.addLayout(password_layout, 1)
        row.addLayout(confirm_layout, 1)

        layout.addLayout(row)

        layout.addSpacing(10)

        # Role
        role_label = QLabel("User role")
        role_label.setObjectName("fieldLabel")
        layout.addWidget(role_label)

        layout.addSpacing(4)

        self.reg_role = QComboBox()
        self.reg_role.addItems([
            "Family / Caregiver",
            "Medical Staff",
            "Administrator"
        ])
        self.reg_role.setFixedHeight(40)

        layout.addWidget(self.reg_role)

        layout.addSpacing(18)

        # -------------------------------------------------
        # PATIENT INFORMATION
        # -------------------------------------------------

        section = QLabel("Patient information")
        section.setObjectName("sectionTitle")
        layout.addWidget(section)

        layout.addSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(16)
        row.setAlignment(Qt.AlignmentFlag.AlignTop)

        patient_layout, self.reg_patient_name, self.reg_patient_name_err = self._field(
            "Patient full name",
            "Jane Doe"
        )

        medical_layout, self.reg_medical_info, self.reg_medical_info_err = self._field(
            "Medical notes (optional)",
            "e.g. Vertigo, reduced mobility"
        )

        row.addLayout(patient_layout, 1)
        row.addLayout(medical_layout, 1)

        layout.addLayout(row)

        layout.addSpacing(20)

        # -------------------------------------------------
        # REGISTER BUTTON
        # -------------------------------------------------

        self.btn_register = QPushButton("Create account")
        self.btn_register.setObjectName("primary")
        self.btn_register.setFixedHeight(42)
        self.btn_register.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.btn_register.clicked.connect(self._emit_register)

        layout.addWidget(self.btn_register)

        layout.addSpacing(14)

        # -------------------------------------------------
        # LOGIN LINK
        # -------------------------------------------------

        switch = QHBoxLayout()
        switch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch.setSpacing(6)

        question = QLabel("Already have an account?")
        question.setStyleSheet(
            "color: #6B7280; font-size: 13px;"
        )

        link = QLabel("Sign in")
        link.setObjectName("link")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        link.mousePressEvent = self._handle_sign_in

        switch.addWidget(question)
        switch.addWidget(link)

        layout.addLayout(switch)

        layout.addStretch(1)

        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

    def _field(
        self,
        label_text,
        placeholder,
        password=False,
        help_text=None
    ):
        col = QVBoxLayout()
        col.setSpacing(4)
        col.setContentsMargins(0, 0, 0, 0)
        col.setAlignment(Qt.AlignmentFlag.AlignTop)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        col.addWidget(label)

        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(40)

        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)

        col.addWidget(edit)

        # Error / help message
        message = QLabel(help_text if help_text else "")
        message.setWordWrap(True)
        message.setAlignment(
            Qt.AlignmentFlag.AlignLeft |
            Qt.AlignmentFlag.AlignTop
        )

        if help_text:
            message.setStyleSheet(
                "color: #6B7280; "
                "font-size: 11px;"
            )
            message.setVisible(True)
        else:
            message.setStyleSheet(
                "color: #DC2626; "
                "font-size: 11px;"
            )
            message.setVisible(False)

        size_policy = message.sizePolicy()
        size_policy.setRetainSizeWhenHidden(False)
        message.setSizePolicy(size_policy)

        col.addWidget(message)

        return col, edit, message

    def _handle_sign_in(self, event):
        self.reset_form()
        self.switch_page_requested.emit()

    def reset_form(self):
        self.reg_name.clear()
        self.reg_phone.clear()
        self.reg_email.clear()
        self.reg_password.clear()
        self.reg_confirm.clear()
        self.reg_patient_name.clear()
        self.reg_medical_info.clear()
        self.reg_role.setCurrentIndex(0)

        self.reg_email_err.setText(
            "Used for fall alerts and system notifications."
        )
        self.reg_email_err.setStyleSheet(
            "color: #6B7280; font-size: 11px;"
        )
        self.reg_email_err.setVisible(True)

        error_labels = [
            self.reg_name_err,
            self.reg_phone_err,
            self.reg_password_err,
            self.reg_confirm_err,
            self.reg_patient_name_err,
            self.reg_medical_info_err,
        ]

        for label in error_labels:
            label.setVisible(False)
            label.setText("")

    def _clear_errors(self):
        self.reg_email_err.setText(
            "Used for fall alerts and system notifications."
        )
        self.reg_email_err.setStyleSheet(
            "color: #6B7280; font-size: 11px;"
        )
        self.reg_email_err.setVisible(True)

        error_labels = [
            self.reg_name_err,
            self.reg_phone_err,
            self.reg_password_err,
            self.reg_confirm_err,
            self.reg_patient_name_err,
            self.reg_medical_info_err,
        ]

        for label in error_labels:
            label.setVisible(False)
            label.setText("")

    def _show_field_error(self, err_lbl, message):
        err_lbl.setStyleSheet(
            "color: #DC2626; font-size: 11px;"
        )
        err_lbl.setText(message)
        err_lbl.setVisible(True)

    def _validate_inputs(self):
        self._clear_errors()

        is_valid = True

        name = self.reg_name.text().strip()
        email = self.reg_email.text().strip()
        phone = self.reg_phone.text().strip()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()
        patient_name = self.reg_patient_name.text().strip()

        if not name:
            self._show_field_error(
                self.reg_name_err,
                "Caregiver name is required."
            )
            is_valid = False

        if not re.match(
            r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$",
            email
        ):
            self._show_field_error(
                self.reg_email_err,
                "Enter a valid email address."
            )
            is_valid = False

        if not re.match(
            r"^\+\d{1,3}(?:[\s.-]?\d){6,14}$",
            phone
        ):
            self._show_field_error(
                self.reg_phone_err,
                "Include international prefix (+1) and a valid number."
            )
            is_valid = False

        if not patient_name:
            self._show_field_error(
                self.reg_patient_name_err,
                "Patient name is required."
            )
            is_valid = False

        if not re.match(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$",
            password
        ):
            self._show_field_error(
                self.reg_password_err,
                "Min 8 chars, 1 uppercase, 1 number, 1 special symbol."
            )
            is_valid = False

        if not confirm or confirm != password:
            self._show_field_error(
                self.reg_confirm_err,
                "Passwords do not match."
            )
            is_valid = False

        return is_valid

    def _emit_register(self):
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