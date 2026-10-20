import re

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.dtos.registration_data import RegistrationData
from src.views.components.auth_header import AuthHeader
from src.views.icons import attach_leading_icon, attach_password_toggle, icon
from src.views.theme import Colors, Size, set_prop, style_combo

_EMAIL_HELP = "Used for fall alerts and system notifications."

_STEPS = (
    ("Caregiver information", "Who will be monitoring?"),
    ("Account access", "How you'll sign in and receive alerts."),
    ("Patient information", "Who is being monitored?"),
)


class RegisterForm(QWidget):
    """
    Component responsible for rendering the registration form interface.
    Presented as a three-step wizard so users only face a few fields at a time.
    Handles user input validation and emits signals for account creation.
    """

    register_requested = Signal(RegistrationData)
    switch_page_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._err_inputs = {}
        self._current_step = 0
        self._build_ui()

    @staticmethod
    def _row(*columns):
        row = QHBoxLayout()
        row.setSpacing(16)
        row.setAlignment(Qt.AlignmentFlag.AlignTop)
        for column in columns:
            row.addLayout(column, 1)
        return row

    @staticmethod
    def _combo_field(label_text, combo):
        col = QVBoxLayout()
        col.setSpacing(5)
        col.setContentsMargins(0, 0, 0, 0)
        col.setAlignment(Qt.AlignmentFlag.AlignTop)
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        col.addWidget(label)
        col.addWidget(combo)
        return col

    @staticmethod
    def _new_page():
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(14)
        return page, page_layout

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("authScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.viewport().setAutoFillBackground(False)

        inner = QWidget()
        inner.setObjectName("authPage")

        layout = QVBoxLayout(inner)
        layout.setContentsMargins(6, 0, 14, 20)
        layout.setSpacing(0)

        layout.addStretch(1)

        layout.addWidget(AuthHeader("Create an account", "Set up your monitoring access"))
        layout.addSpacing(28)

        meta = QHBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        self.step_title = QLabel("")
        self.step_title.setObjectName("stepTitle")
        self.step_counter = QLabel("")
        self.step_counter.setObjectName("stepCounter")
        meta.addWidget(self.step_title)
        meta.addStretch()
        meta.addWidget(self.step_counter)
        layout.addLayout(meta)
        layout.addSpacing(10)

        bars = QHBoxLayout()
        bars.setContentsMargins(0, 0, 0, 0)
        bars.setSpacing(6)
        self._bars = []
        for _ in _STEPS:
            bar = QFrame()
            bar.setObjectName("stepBar")
            bar.setFixedHeight(4)
            bar.setProperty("state", "todo")
            bars.addWidget(bar, 1)
            self._bars.append(bar)
        layout.addLayout(bars)
        layout.addSpacing(12)

        self.step_hint = QLabel("")
        self.step_hint.setObjectName("stepHint")
        layout.addWidget(self.step_hint)
        layout.addSpacing(20)

        self.pages = QStackedWidget()

        page, page_layout = self._new_page()
        name_layout, self.reg_name, self.reg_name_err = self._field(
            "Full name", "John Doe", icon_name="user"
        )
        phone_layout, self.reg_phone, self.reg_phone_err = self._field(
            "Phone", "+1 234 567 8900", icon_name="phone"
        )
        page_layout.addLayout(self._row(name_layout, phone_layout))

        self.reg_role = QComboBox()
        self.reg_role.addItems([
            "Family / Caregiver",
            "Medical Staff",
            "Administrator"
        ])
        self.reg_role.setFixedHeight(Size.FIELD)
        style_combo(self.reg_role)
        page_layout.addLayout(self._combo_field("User role", self.reg_role))
        page_layout.addStretch(1)
        self.pages.addWidget(page)

        page, page_layout = self._new_page()
        email_layout, self.reg_email, self.reg_email_err = self._field(
            "Email address",
            "name@example.com",
            help_text=_EMAIL_HELP,
            icon_name="mail"
        )
        page_layout.addLayout(email_layout)

        password_layout, self.reg_password, self.reg_password_err = self._field(
            "Password", "••••••••", password=True, icon_name="lock"
        )
        confirm_layout, self.reg_confirm, self.reg_confirm_err = self._field(
            "Confirm password", "••••••••", password=True, icon_name="lock"
        )
        page_layout.addLayout(self._row(password_layout, confirm_layout))
        page_layout.addStretch(1)
        self.pages.addWidget(page)

        page, page_layout = self._new_page()
        patient_layout, self.reg_patient_name, self.reg_patient_name_err = self._field(
            "Patient full name", "Jane Doe", icon_name="user"
        )
        self.reg_risk_level = QComboBox()
        self.reg_risk_level.addItems(["LOW", "HIGH"])
        self.reg_risk_level.setFixedHeight(Size.FIELD)
        style_combo(self.reg_risk_level)
        risk_layout = self._combo_field("Baseline risk level", self.reg_risk_level)
        page_layout.addLayout(self._row(patient_layout, risk_layout))

        medical_layout, self.reg_medical_info, self.reg_medical_info_err = self._field(
            "Medical notes (optional)",
            "e.g. Vertigo, reduced mobility",
            icon_name="note"
        )
        page_layout.addLayout(medical_layout)
        page_layout.addStretch(1)
        self.pages.addWidget(page)

        layout.addWidget(self.pages)

        self._step_errors = (
            (self.reg_name_err, self.reg_phone_err),
            (self.reg_email_err, self.reg_password_err, self.reg_confirm_err),
            (self.reg_patient_name_err, self.reg_medical_info_err),
        )

        layout.addSpacing(26)

        nav = QHBoxLayout()
        nav.setContentsMargins(0, 0, 0, 0)
        nav.setSpacing(12)

        self.btn_back = QPushButton("Back")
        self.btn_back.setObjectName("ghost")
        self.btn_back.setFixedHeight(Size.FIELD)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setIcon(icon("arrow_left", Colors.ON_GHOST, 16))
        self.btn_back.setIconSize(QSize(16, 16))
        self.btn_back.clicked.connect(self._prev_step)
        nav.addWidget(self.btn_back, 1)

        self.btn_next = QPushButton("Continue")
        self.btn_next.setObjectName("primary")
        self.btn_next.setFixedHeight(Size.FIELD)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self._next_step)
        nav.addWidget(self.btn_next, 1)

        self.btn_register = QPushButton("Create account")
        self.btn_register.setObjectName("primary")
        self.btn_register.setFixedHeight(Size.FIELD)
        self.btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register.clicked.connect(self._emit_register)
        nav.addWidget(self.btn_register, 1)

        for button in (self.btn_back, self.btn_next, self.btn_register):
            button.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

        layout.addLayout(nav)
        layout.addSpacing(18)

        switch = QHBoxLayout()
        switch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch.setSpacing(4)

        question = QLabel("Already have an account?")
        question.setObjectName("authHint")

        link = QPushButton("Sign in")
        link.setObjectName("linkButton")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        link.clicked.connect(lambda: self._handle_sign_in(None))

        switch.addWidget(question)
        switch.addWidget(link)
        layout.addLayout(switch)

        layout.addStretch(1)

        self._scroll.setWidget(inner)
        main_layout.addWidget(self._scroll)

        self._go_to_step(0)

    def _field(
        self,
        label_text,
        placeholder,
        password=False,
        help_text=None,
        icon_name=None
    ):
        col = QVBoxLayout()
        col.setSpacing(5)
        col.setContentsMargins(0, 0, 0, 0)
        col.setAlignment(Qt.AlignmentFlag.AlignTop)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        col.addWidget(label)

        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(Size.FIELD)

        if icon_name:
            attach_leading_icon(edit, icon_name)

        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            attach_password_toggle(edit)

        edit.returnPressed.connect(self._on_enter)

        col.addWidget(edit)

        message = QLabel(help_text if help_text else "")
        message.setObjectName("fieldMessage")
        message.setWordWrap(True)
        message.setAlignment(
            Qt.AlignmentFlag.AlignLeft |
            Qt.AlignmentFlag.AlignTop
        )
        message.setProperty("kind", "help" if help_text else "error")
        message.setVisible(bool(help_text))

        size_policy = message.sizePolicy()
        size_policy.setRetainSizeWhenHidden(False)
        message.setSizePolicy(size_policy)

        col.addWidget(message)

        self._err_inputs[message] = edit
        return col, edit, message

    def _go_to_step(self, index):
        last = len(_STEPS) - 1
        index = max(0, min(index, last))
        self._current_step = index
        self.pages.setCurrentIndex(index)

        for i, bar in enumerate(self._bars):
            set_prop(bar, "state", "done" if i < index else ("current" if i == index else "todo"))

        title, hint = _STEPS[index]
        self.step_title.setText(title)
        self.step_hint.setText(hint)
        self.step_counter.setText(f"Step {index + 1} of {len(_STEPS)}")

        self.btn_back.setVisible(index > 0)
        self.btn_next.setVisible(index < last)
        self.btn_register.setVisible(index == last)
        self._scroll.verticalScrollBar().setValue(0)

    def _next_step(self):
        if self._validate_inputs(only_step=self._current_step):
            self._go_to_step(self._current_step + 1)

    def _prev_step(self):
        self._go_to_step(self._current_step - 1)

    def _on_enter(self):
        if self._current_step < len(_STEPS) - 1:
            self._next_step()
        else:
            self._emit_register()

    def _step_has_error(self, index):
        return any(
            lbl.property("kind") == "error" and not lbl.isHidden()
            for lbl in self._step_errors[index]
        )

    def _go_to_first_error_step(self):
        for index in range(len(_STEPS)):
            if self._step_has_error(index):
                self._go_to_step(index)
                return

    def _handle_sign_in(self, event=None):
        self.reset_form()
        self.switch_page_requested.emit()

    def _restore_email_help(self):
        set_prop(self.reg_email_err, "kind", "help")
        self.reg_email_err.setText(_EMAIL_HELP)
        self.reg_email_err.setVisible(True)

    def _hide_error_labels(self):
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

    def reset_form(self):
        self.reg_name.clear()
        self.reg_phone.clear()
        self.reg_email.clear()
        self.reg_password.clear()
        self.reg_confirm.clear()
        self.reg_patient_name.clear()
        self.reg_medical_info.clear()
        self.reg_role.setCurrentIndex(0)
        self.reg_risk_level.setCurrentIndex(0)

        self._restore_email_help()
        self._hide_error_labels()
        for edit in self._err_inputs.values():
            set_prop(edit, "invalid", False)
        self._go_to_step(0)

    def _clear_errors(self):
        self._restore_email_help()
        self._hide_error_labels()
        for edit in self._err_inputs.values():
            set_prop(edit, "invalid", False)

    def _show_field_error(self, err_lbl, message):
        set_prop(err_lbl, "kind", "error")
        err_lbl.setText(message)
        err_lbl.setVisible(True)
        edit = self._err_inputs.get(err_lbl)
        if edit is not None:
            set_prop(edit, "invalid", True)

    def _validate_inputs(self, only_step=None):
        self._clear_errors()

        is_valid = True

        def wants(step):
            return only_step is None or only_step == step

        name = self.reg_name.text().strip()
        email = self.reg_email.text().strip()
        phone = self.reg_phone.text().strip()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()
        patient_name = self.reg_patient_name.text().strip()

        if wants(0) and not name:
            self._show_field_error(
                self.reg_name_err,
                "Caregiver name is required."
            )
            is_valid = False

        if wants(1) and not re.match(
            r"^[a-zA-Z0-9_.+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$",
            email
        ):
            self._show_field_error(
                self.reg_email_err,
                "Enter a valid email address."
            )
            is_valid = False

        if wants(0) and not re.match(
            r"^\+\d{1,3}(?:[\s.-]?\d){6,14}$",
            phone
        ):
            self._show_field_error(
                self.reg_phone_err,
                "Include international prefix (+1) and a valid number."
            )
            is_valid = False

        if wants(2) and not patient_name:
            self._show_field_error(
                self.reg_patient_name_err,
                "Patient name is required."
            )
            is_valid = False

        if wants(1) and not re.match(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$",
            password
        ):
            self._show_field_error(
                self.reg_password_err,
                "Min 8 chars, 1 uppercase, 1 number, 1 special symbol."
            )
            is_valid = False

        if wants(1) and (not confirm or confirm != password):
            self._show_field_error(
                self.reg_confirm_err,
                "Passwords do not match."
            )
            is_valid = False

        return is_valid

    def _emit_register(self):
        if self._validate_inputs():
            reg_data = RegistrationData(
                name=self.reg_name.text().strip(),
                email=self.reg_email.text().strip(),
                phone=self.reg_phone.text().strip(),
                password=self.reg_password.text(),
                role=self.reg_role.currentText(),
                patient_name=self.reg_patient_name.text().strip(),
                medical_info=self.reg_medical_info.text().strip(),
                risk_level=self.reg_risk_level.currentText()
            )
            self.register_requested.emit(reg_data)
        else:
            self._go_to_first_error_step()