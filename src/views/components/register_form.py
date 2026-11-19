import re

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
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

from src.dtos.questionnaire import (
    CHECK,
    CHOICE,
    DAILY_LIFE,
    HEALTH,
    NUMBER,
    PROFILE,
    QUESTIONS,
)
from src.dtos.registration_data import USER_ROLES, RegistrationData
from src.views.components.auth_header import AuthHeader
from src.views.icons import attach_leading_icon, attach_password_toggle, icon
from src.views.theme import Colors, Size, set_prop, style_combo

_EMAIL_HELP = "Used for fall alerts and system notifications."

_STEPS = (
    ("Caregiver information", "Who will be monitoring?"),
    ("Account access", "How you'll sign in and receive alerts."),
    ("Patient information", "Who is being monitored?"),
    ("Daily life", "How the patient manages every day."),
    ("Health", "Conditions and medication. They set the patient's risk level."),
)

# Step of the wizard (index in _STEPS) where each group of questionnaire questions is shown.
_QUESTION_STEPS = {PROFILE: 2, DAILY_LIFE: 3, HEALTH: 4}


class RegisterForm(QWidget):
    """
    Component responsible for rendering the registration form interface.
    Presented as a five-step wizard so users only face a few fields at a time.
    The last steps are the health questionnaire (see `src/dtos/questionnaire.py`): its answers
    are sent with the registration and the patient's risk level is calculated from them.
    Handles user input validation and emits signals for account creation.
    """

    register_requested = Signal(RegistrationData)
    switch_page_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._err_inputs = {}
        self._answer_inputs = {}     # questionnaire widgets, by question key
        self._number_errors = {}     # error label of each numeric question, by question key
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
        self.reg_role.addItems(USER_ROLES)
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
        page_layout.addLayout(patient_layout)
        self._add_questions(page_layout, PROFILE)

        medical_layout, self.reg_medical_info, self.reg_medical_info_err = self._field(
            "Medical notes (optional)",
            "e.g. Vertigo, reduced mobility",
            icon_name="note"
        )
        page_layout.addLayout(medical_layout)
        page_layout.addStretch(1)
        self.pages.addWidget(page)

        for step in (DAILY_LIFE, HEALTH):
            page, page_layout = self._new_page()
            self._add_questions(page_layout, step)
            page_layout.addStretch(1)
            self.pages.addWidget(page)

        layout.addWidget(self.pages)

        self._step_errors = (
            (self.reg_name_err, self.reg_phone_err),
            (self.reg_email_err, self.reg_password_err, self.reg_confirm_err),
            (self.reg_patient_name_err, self.reg_medical_info_err, *self._number_error_labels(PROFILE)),
            self._number_error_labels(DAILY_LIFE),
            self._number_error_labels(HEALTH),
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

    def _add_questions(self, page_layout, step):
        """
        Adds the questionnaire questions of a step to the page: selects and numbers two per row,
        check boxes in two columns, and a heading where a new group of questions starts.
        """
        fields = []   # selects and numbers waiting to fill a row
        boxes = []    # check boxes waiting to fill the grid

        def flush():
            for i in range(0, len(fields), 2):
                pair = fields[i:i + 2]
                if len(pair) == 1:
                    pair.append(QVBoxLayout())   # empty column, so a lone field keeps the width of the others
                page_layout.addLayout(self._row(*pair))
            if boxes:
                grid = QGridLayout()
                grid.setHorizontalSpacing(16)
                grid.setVerticalSpacing(10)
                grid.setColumnStretch(0, 1)
                grid.setColumnStretch(1, 1)
                for i, box in enumerate(boxes):
                    grid.addWidget(box, i // 2, i % 2)
                page_layout.addLayout(grid)
            fields.clear()
            boxes.clear()

        for question in QUESTIONS:
            if question.step != step:
                continue

            if question.section:
                flush()
                heading = QLabel(question.section)
                heading.setObjectName("sectionLabel")
                heading.setIndent(0)
                page_layout.addWidget(heading)

            if question.kind == CHECK:
                widget = QCheckBox(question.text)
                widget.setCursor(Qt.CursorShape.PointingHandCursor)
                boxes.append(widget)
            elif question.kind == CHOICE:
                widget = QComboBox()
                for label, value in question.options:
                    widget.addItem(label, value)
                widget.setFixedHeight(Size.FIELD)
                style_combo(widget)
                fields.append(self._combo_field(question.text, widget))
            else:
                column, widget, error = self._field(question.text, f"{question.minimum} - {question.maximum}")
                widget.setValidator(QIntValidator(0, 999, widget))
                widget.setMaxLength(3)
                widget.setText("0" if question.minimum == 0 else "")
                self._number_errors[question.key] = error
                fields.append(column)

            self._answer_inputs[question.key] = widget
        flush()

    def _number_error_labels(self, step):
        return tuple(self._number_errors[q.key] for q in QUESTIONS if q.step == step and q.key in self._number_errors)

    def _reset_answers(self):
        """Back to the first option, unchecked, and 0 where 0 is a valid number (the other numbers stay empty)."""
        for question in QUESTIONS:
            widget = self._answer_inputs[question.key]
            if question.kind == CHOICE:
                widget.setCurrentIndex(0)
            elif question.kind == CHECK:
                widget.setChecked(False)
            else:
                widget.setText("0" if question.minimum == 0 else "")

    def _read_answers(self) -> dict[str, float]:
        """The questionnaire answers as the numbers the risk model uses."""
        answers = {}
        for question in QUESTIONS:
            widget = self._answer_inputs[question.key]
            if question.kind == CHOICE:
                answers[question.key] = float(widget.currentData())
            elif question.kind == CHECK:
                answers[question.key] = float(widget.isChecked())
            else:
                answers[question.key] = float(widget.text())
        return answers

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
            *self._number_errors.values(),
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
        self._reset_answers()

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

        for question in QUESTIONS:
            if question.kind != NUMBER or not wants(_QUESTION_STEPS[question.step]):
                continue
            text = self._answer_inputs[question.key].text().strip()
            if not text.isdigit() or not question.minimum <= int(text) <= question.maximum:
                self._show_field_error(
                    self._number_errors[question.key],
                    f"Enter a number between {question.minimum} and {question.maximum}."
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
                risk_answers=self._read_answers()
            )
            self.register_requested.emit(reg_data)
        else:
            self._go_to_first_error_step()