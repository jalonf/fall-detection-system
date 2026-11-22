"""Sign-up page: five steps (caregiver, account, patient, daily life, health) in a 600 px column."""

from __future__ import annotations

import re
from itertools import pairwise

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    QRegularExpression,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QPainter, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractButton,
    QGridLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.domain import password_policy
from src.domain.questionnaire import DAILY_LIFE, HEALTH, PROFILE
from src.domain.roles import SIGNUP_ROLES
from src.dtos.registration_data import RegistrationData
from src.views.components.auth.login_page import EMAIL_CHARACTERS, EMAIL_PATTERN
from src.views.components.auth.page_heading import PageHeading
from src.views.components.auth.password_checklist import PasswordChecklist
from src.views.components.auth.question_field import COLUMN, HALF, QuestionStep
from src.views.components.auth.stepper import Stepper
from src.views.components.common.button import make_button
from src.views.components.common.callout import Callout
from src.views.components.common.form_field import FormField
from src.views.components.common.inputs import PasswordEdit, make_line_edit
from src.views.components.common.painting import (
    transparent_scroll_area,
)
from src.views.components.common.segmented_control import SegmentedControl
from src.views.strings import Register
from src.views.theme import Colors, Motion, Space, make_label

PHONE_PATTERN = re.compile(r"^\+\d{1,3}(?:[\s.-]?\d){6,14}$")
PHONE_CHARACTERS = r"\+?[\d\s.-]*"
GUTTER = 18                       # room on each side of the 600 px column for the scroll bar
STEPS = len(Register.STEPS)

Error = tuple[QWidget, QWidget]   # (widget to scroll to, widget to focus)


class _Footer(QWidget):
    """64 px footer with an N150 divider on top."""

    def paintEvent(self, event) -> None:
        QPainter(self).fillRect(QRect(GUTTER, 0, self.width() - 2 * GUTTER, 1), QColor(Colors.N150))


def _row(*widgets: QWidget) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(Space.S4)
    for widget in widgets:
        widget.setFixedWidth(HALF)
        row.addWidget(widget, 0, Qt.AlignmentFlag.AlignTop)
    row.addStretch(1)
    return row


class RegisterPage(QWidget):
    """Five-step sign-up form: caregiver, account, patient, daily life and health.

    Signals:
        submitted(RegistrationData): The validated form.
        back_to_login_clicked: The user wants to go back to sign in.
    """
    submitted = Signal(RegistrationData)
    back_to_login_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._busy = False
        self._current = 0
        self._completed = 0
        self._pending_scroll: Error | None = None
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.setInterval(0)
        self._scroll_timer.timeout.connect(self._scroll_to_pending)
        self._scroll_animation: QPropertyAnimation | None = None

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)
        column = QWidget()
        column.setFixedWidth(COLUMN + 2 * GUTTER)
        outer.addWidget(column)
        outer.addStretch(1)

        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, Space.S8, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        self.pages = QStackedWidget()
        self.scroll_areas: list[QScrollArea] = []
        for page in (self._build_caregiver(), self._build_account(), self._build_patient(),
                     self._build_daily_life(), self._build_health()):
            self.pages.addWidget(self._wrap(page))
        layout.addWidget(self.pages, 1)
        layout.addWidget(self._build_footer())

        self._wire_tab_order()
        self._go(0)

    # ------------------------------------------------------------------ construction
    def _build_header(self) -> QWidget:
        header = QWidget()
        outer = QVBoxLayout(header)
        # The ghost button's 10 px padding sits outside the column, so its icon lines up with the title.
        outer.setContentsMargins(GUTTER - 10, 0, GUTTER, 0)
        outer.setSpacing(0)
        self.back_link = make_button(Register.BACK_TO_SIGN_IN, "ghost", "sm", "chevron-left")
        self.back_link.clicked.connect(self.back_to_login_clicked)
        outer.addWidget(self.back_link, 0, Qt.AlignmentFlag.AlignLeft)
        outer.addSpacing(Space.S4)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)
        outer.addLayout(layout)
        layout.addWidget(PageHeading("user-plus", Register.TITLE, Register.SUBTITLE))
        layout.addSpacing(Space.S6)
        self.stepper = Stepper(Register.STEPS)
        self.stepper.step_clicked.connect(self._on_step_clicked)
        layout.addWidget(self.stepper)

        self.error = Callout("", "danger")       # server errors that belong to no field
        self.error_box = QWidget()
        error_layout = QVBoxLayout(self.error_box)
        error_layout.setContentsMargins(0, Space.S4, 0, 0)
        error_layout.addWidget(self.error)
        self.error_box.hide()
        layout.addWidget(self.error_box)
        return header

    def _wrap(self, page: QWidget) -> QScrollArea:
        holder = QWidget()
        holder_layout = QVBoxLayout(holder)
        holder_layout.setContentsMargins(0, Space.S6, 0, Space.S6)
        holder_layout.setSpacing(0)
        page.setFixedWidth(COLUMN)
        holder_layout.addWidget(page)
        holder_layout.addStretch(1)
        holder.setFixedWidth(COLUMN)
        area = transparent_scroll_area(holder)
        area.setWidgetResizable(True)
        area.setViewportMargins(GUTTER, 0, 0, 0)
        area.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.scroll_areas.append(area)
        return area

    @staticmethod
    def _page() -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        return page, layout

    def _build_caregiver(self) -> QWidget:
        page, layout = self._page()
        self.name = make_line_edit("", "user")
        self.name_field = FormField(Register.FULL_NAME, self.name)
        self.phone = make_line_edit(Register.PHONE_PLACEHOLDER, "phone")
        self.phone.setValidator(QRegularExpressionValidator(QRegularExpression(PHONE_CHARACTERS), self.phone))
        self.phone_field = FormField(Register.PHONE, self.phone)
        layout.addLayout(_row(self.name_field, self.phone_field))
        layout.addSpacing(Space.S5)
        self.role = SegmentedControl(SIGNUP_ROLES, accessible_name=Register.ROLE)
        self.role_field = FormField(Register.ROLE, self.role)
        layout.addWidget(self.role_field)
        self.name.textChanged.connect(self._clear(self.name_field))
        self.phone.textChanged.connect(self._clear(self.phone_field))
        self.role.selection_changed.connect(self._clear(self.role_field))
        return page

    def _build_account(self) -> QWidget:
        page, layout = self._page()
        self.email = make_line_edit(Register.EMAIL_PLACEHOLDER, "mail")
        self.email.setValidator(QRegularExpressionValidator(QRegularExpression(EMAIL_CHARACTERS), self.email))
        self.email_field = FormField(Register.EMAIL, self.email, help_text=Register.EMAIL_HELP)
        layout.addWidget(self.email_field)
        layout.addSpacing(Space.S5)
        self.password = PasswordEdit()
        self.password_field = FormField(Register.PASSWORD, self.password)
        self.confirm = PasswordEdit()
        self.confirm_field = FormField(Register.CONFIRM_PASSWORD, self.confirm)
        layout.addLayout(_row(self.password_field, self.confirm_field))
        layout.addSpacing(Space.S3)
        self.checklist = PasswordChecklist()
        layout.addWidget(self.checklist)
        self.email.textChanged.connect(self._clear(self.email_field))
        self.password.textChanged.connect(self.checklist.set_password)
        self.password.textChanged.connect(self._clear(self.password_field))
        self.confirm.textChanged.connect(self._clear(self.confirm_field))
        return page

    def _build_patient(self) -> QWidget:
        page, layout = self._page()
        self.patient = make_line_edit("", "user")
        self.patient_field = FormField(Register.PATIENT_NAME, self.patient)
        layout.addWidget(self.patient_field)
        layout.addSpacing(Space.S5)
        self.profile = QuestionStep(PROFILE)
        layout.addWidget(self.profile)
        layout.addSpacing(Space.S5)
        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText(Register.MEDICAL_NOTES_PLACEHOLDER)
        self.notes.setFixedHeight(88)
        self.notes.setTabChangesFocus(True)
        self.notes_field = FormField(Register.MEDICAL_NOTES, self.notes, optional=True)
        layout.addWidget(self.notes_field)
        self.patient.textChanged.connect(self._clear(self.patient_field))
        return page

    def _build_daily_life(self) -> QWidget:
        page, layout = self._page()
        self.daily = QuestionStep(DAILY_LIFE)
        layout.addWidget(self.daily)
        return page

    def _build_health(self) -> QWidget:
        page, layout = self._page()
        self.health = QuestionStep(HEALTH)
        layout.addWidget(self.health)
        layout.addSpacing(Space.S6)
        layout.addWidget(Callout(Register.RISK_CALLOUT))
        return page

    def _build_footer(self) -> QWidget:
        footer = _Footer()
        footer.setFixedHeight(64)
        grid = QGridLayout(footer)
        grid.setContentsMargins(GUTTER, 1, GUTTER, 0)
        grid.setHorizontalSpacing(Space.S4)
        self.back = make_button(Register.BACK, "secondary", "lg")
        self.back.setFixedWidth(120)
        policy = self.back.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.back.setSizePolicy(policy)
        self.step_label = make_label("", "caption", "tertiary")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next = make_button(Register.CONTINUE, "primary", "lg")
        self.next.reserve_width(Register.CONTINUE, Register.CREATE, Register.CREATING)
        self.next.setMinimumWidth(160)
        grid.addWidget(self.back, 0, 0, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self.step_label, 0, 1)
        grid.addWidget(self.next, 0, 2, Qt.AlignmentFlag.AlignRight)
        side = max(160, self.next.sizeHint().width())
        grid.setColumnMinimumWidth(0, side)
        grid.setColumnMinimumWidth(2, side)
        grid.setColumnStretch(1, 1)
        self.back.clicked.connect(self._on_back)
        self.next.clicked.connect(self._on_next)
        return footer

    def _wire_tab_order(self) -> None:
        """Explicit order for the fixed fields; questions keep their (top-to-bottom) creation order."""
        chains = (
            [self.back_link, self.name, self.phone, *self.role.buttons],
            [self.email, self.password, self.confirm],
            [self.back, self.next],
        )
        for chain in chains:
            for first, second in pairwise(chain):
                self.setTabOrder(first, second)

    def _clear(self, field: FormField):
        @Slot()
        def clear(*_args) -> None:
            if field.has_error():
                field.set_error(None)
        return clear

    # ------------------------------------------------------------------ navigation
    def _go(self, index: int) -> None:
        self._current = index
        self.pages.setCurrentIndex(index)
        self.stepper.set_current(index)
        self.stepper.set_completed(self._completed)
        self.back.setVisible(index > 0)
        last = index == STEPS - 1
        if not self._busy:
            self.next.setText(Register.CREATE if last else Register.CONTINUE)
        self.step_label.setText(Register.STEP_OF.format(current=index + 1, total=STEPS))

    @Slot()
    def _on_back(self) -> None:
        if self._busy or self._current == 0:
            return
        self._go(self._current - 1)
        self.focus_first()

    @Slot()
    def _on_next(self) -> None:
        if self._busy:
            return
        self.error_box.hide()
        if self._current < STEPS - 1:
            errors = self._validate(self._current)
            if errors:
                self._report(errors)
                return
            self._completed = max(self._completed, self._current + 1)
            self._go(self._current + 1)
            self.scroll_areas[self._current].verticalScrollBar().setValue(0)
            self.focus_first()
            return
        self._create_account()

    @Slot(int)
    def _on_step_clicked(self, index: int) -> None:
        if self._busy:
            return
        if index > self._current:
            errors = self._validate(self._current)
            if errors:
                self._report(errors)
                return
            self._completed = max(self._completed, self._current + 1)
        self._go(index)
        self.focus_first()

    def _create_account(self) -> None:
        all_errors = [(step, self._validate(step)) for step in range(STEPS)]
        failing = [(step, errors) for step, errors in all_errors if errors]
        if failing:
            step, errors = failing[0]
            self._go(step)
            self._report(errors)
            return
        self._completed = STEPS
        self.stepper.set_completed(STEPS)
        self.set_busy(True)
        self.submitted.emit(self.collect())

    # ------------------------------------------------------------------ validation
    def _validate(self, step: int) -> list[Error]:
        errors: list[Error] = []

        def fail(field: FormField, message: str, focus: QWidget | None = None) -> None:
            field.set_error(message)
            errors.append((field, focus or field.control))

        if step == 0:
            if not self.name.text().strip():
                fail(self.name_field, Register.NAME_REQUIRED)
            if not PHONE_PATTERN.match(self.phone.text().strip()):
                fail(self.phone_field, Register.PHONE_INVALID)
            if self.role.selected() < 0:
                fail(self.role_field, Register.ROLE_REQUIRED, self.role.focus_target())
        elif step == 1:
            if not EMAIL_PATTERN.match(self.email.text().strip()):
                fail(self.email_field, Register.EMAIL_INVALID)
            if not all(PasswordChecklist.requirements(self.password.text()).values()):
                fail(self.password_field, Register.PASSWORD_WEAK)
            elif password_policy.too_long(self.password.text()):
                fail(self.password_field, Register.PASSWORD_TOO_LONG)
            if self.confirm.text() != self.password.text() or not self.confirm.text():
                fail(self.confirm_field, Register.PASSWORD_MISMATCH)
        elif step == 2:
            if not self.patient.text().strip():
                fail(self.patient_field, Register.PATIENT_REQUIRED)
            errors += self.profile.validate()
        elif step == 3:
            errors += self.daily.validate()
        elif step == 4:
            errors += self.health.validate()
        return errors

    def _report(self, errors: list[Error]) -> None:
        """Errors are shown inline under each field; scroll to the first one and focus it."""
        self._pending_scroll = errors[0]
        self._scroll_timer.start()   # after the page has been laid out

    @Slot()
    def _scroll_to_pending(self) -> None:
        if self._pending_scroll is None:
            return
        target, focus = self._pending_scroll
        self._pending_scroll = None
        area = self.scroll_areas[self._current]
        bar = area.verticalScrollBar()
        start = bar.value()
        area.ensureWidgetVisible(target, 0, Space.S6)
        end = bar.value()
        focus.setFocus(Qt.FocusReason.OtherFocusReason)
        if start != end:
            bar.setValue(start)
            self._scroll_animation = QPropertyAnimation(bar, b"value", self)
            self._scroll_animation.setDuration(Motion.BASE)
            self._scroll_animation.setEasingCurve(QEasingCurve(Motion.OUT))
            self._scroll_animation.setStartValue(start)
            self._scroll_animation.setEndValue(end)
            self._scroll_animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    # ------------------------------------------------------------------ API
    def collect(self) -> RegistrationData:
        """Builds the DTO sent to the controller from the validated form.

        Returns:
            The account, the patient and the answers to the health questionnaire.
        """
        answers: dict[str, float] = {}
        for step in (self.profile, self.daily, self.health):
            answers.update(step.answers())
        return RegistrationData(
            name=self.name.text().strip(),
            email=self.email.text().strip(),
            phone=self.phone.text().strip(),
            password=self.password.text(),
            role=SIGNUP_ROLES[self.role.selected()],
            patient_name=self.patient.text().strip(),
            medical_info=self.notes.toPlainText().strip(),
            risk_answers=answers,
        )

    def focus_first(self) -> None:
        """Focuses the first field of the current step."""
        first = {0: self.name, 1: self.email, 2: self.patient}.get(self._current)
        if first is not None:
            first.setFocus(Qt.FocusReason.OtherFocusReason)
        else:
            self.setFocus(Qt.FocusReason.OtherFocusReason)

    def set_busy(self, busy: bool) -> None:
        """Locks the form while the controller creates the account.

        Args:
            busy: True to lock it (and show the spinner), False to unlock it.
        """
        self._busy = busy
        self.pages.setEnabled(not busy)
        self.back_link.setEnabled(not busy)
        self.back.setEnabled(not busy)
        self.stepper.setEnabled(not busy)
        self.next.set_loading(busy, Register.CREATING)
        if not busy:
            self._go(self._current)

    def is_busy(self) -> bool:
        """True while a sign-up request is being handled."""
        return self._busy

    def show_server_error(self, message: str) -> None:
        """The controller refused the sign-up: point at the field, or explain it in the callout."""
        self.set_busy(False)
        lowered = message.lower()
        if "email" in lowered:
            self._go(1)
            self.email_field.set_error(Register.EMAIL_IN_USE)
            self._pending_scroll = (self.email_field, self.email)
            self._scroll_timer.start()
            self.email.selectAll()
        elif "role" in lowered:
            self._go(0)
            self.role_field.set_error(Register.ROLE_REQUIRED)
            self._pending_scroll = (self.role_field, self.role.focus_target())
            self._scroll_timer.start()
        else:
            self.error.set_message(message)
            self.error_box.show()

    def reset(self) -> None:
        """Clears every field and error and goes back to the first step."""
        self.setUpdatesEnabled(False)
        try:
            self._busy = False
            self.error_box.hide()
            self.next.set_loading(False)
            self.pages.setEnabled(True)
            self.back_link.setEnabled(True)
            self.back.setEnabled(True)
            self.stepper.setEnabled(True)
            for edit in (self.name, self.phone, self.email, self.password, self.confirm, self.patient):
                edit.clear()
            self.password.set_revealed(False)
            self.confirm.set_revealed(False)
            self.notes.clear()
            self.role.clear()
            for field in (self.name_field, self.phone_field, self.role_field, self.email_field,
                          self.password_field, self.confirm_field, self.patient_field):
                field.set_error(None)
            for step in (self.profile, self.daily, self.health):
                step.reset()
            for area in self.scroll_areas:
                area.verticalScrollBar().setValue(0)
            self._completed = 0
            self._go(0)
        finally:
            self.setUpdatesEnabled(True)

    # ------------------------------------------------------------------ keyboard
    def keyPressEvent(self, event) -> None:
        """Enter presses the focused button or goes to the next step; Esc does nothing."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.accept()
            if self._busy:
                return
            focused = self.focusWidget()
            if isinstance(focused, QAbstractButton) and focused is not self.next:
                focused.click()
            else:
                self._on_next()
            return
        if event.key() == Qt.Key.Key_Escape:
            event.accept()
            return
        super().keyPressEvent(event)

