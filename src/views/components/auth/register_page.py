"""Sign-up page: the caregiver's account on one page, built like the sign-in page.

Same column, heading, full-width primary button and labelled divider over a secondary button as the
sign-in page, so moving between the two only changes the fields. Only the caregiver's account is
created here; the people they look after are added afterwards, on the Patients page, each with their
own health questionnaire.

The page scrolls when the window is too short for it; otherwise the column is centred.
"""

from __future__ import annotations

import re
from itertools import pairwise

from PySide6.QtCore import QRegularExpression, Qt, Signal, Slot
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.domain import password_policy
from src.domain.roles import SIGNUP_ROLES
from src.dtos.registration_data import RegistrationData, RegistrationField
from src.strings import Register, role_label
from src.views.components.auth.login_page import (
    COLUMN,
    COLUMN_MAX,
    EMAIL_CHARACTERS,
    EMAIL_PATTERN,
    labelled_divider,
)
from src.views.components.auth.page_heading import PageHeading
from src.views.components.auth.password_checklist import PasswordChecklist
from src.views.components.common.button import make_button
from src.views.components.common.callout import Callout
from src.views.components.common.form_field import FormField
from src.views.components.common.inputs import PasswordEdit, make_line_edit
from src.views.components.common.painting import transparent_scroll_area
from src.views.components.common.segmented_control import SegmentedControl
from src.views.theme import Size, Space

PHONE_PATTERN = re.compile(r"^\+\d{1,3}(?:[\s.-]?\d){6,14}$")
PHONE_CHARACTERS = r"\+?[\d\s.-]*"


def _pair(first: QWidget, second: QWidget) -> QHBoxLayout:
    """Two fields side by side, sharing the column's width."""
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(Space.S4)
    row.addWidget(first, 1, Qt.AlignmentFlag.AlignTop)
    row.addWidget(second, 1, Qt.AlignmentFlag.AlignTop)
    return row


class RegisterPage(QWidget):
    """Sign-up form: name, phone, role, e-mail and password.

    Signals:
        submitted(RegistrationData): The validated form.
        back_to_login_clicked: The user wants to go back to sign in.
    """
    submitted = Signal(RegistrationData)
    back_to_login_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._busy = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        content = QWidget()
        page = QVBoxLayout(content)
        page.setContentsMargins(Space.S8, Space.S6, Space.S8, Space.S6)
        page.addStretch(2)
        row = QHBoxLayout()
        row.addStretch(1)
        self._column_widget = QWidget()
        self._column_widget.setFixedWidth(COLUMN)
        row.addWidget(self._column_widget)
        row.addStretch(1)
        page.addLayout(row)
        page.addStretch(3)
        self.scroll = transparent_scroll_area(content)
        outer.addWidget(self.scroll)

        column = QVBoxLayout(self._column_widget)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        self.heading = PageHeading("user-plus", Register.TITLE, Register.SUBTITLE)
        column.addWidget(self.heading)
        column.addSpacing(Space.S8)

        self.error = Callout("", "danger")
        self._error_box = QWidget()             # the callout and its gap, shown together
        error_layout = QVBoxLayout(self._error_box)
        error_layout.setContentsMargins(0, 0, 0, Space.S5)
        error_layout.addWidget(self.error)
        self._error_box.hide()
        column.addWidget(self._error_box)

        self.name = make_line_edit("", "user")
        self.name_field = FormField(Register.FULL_NAME, self.name)
        self.phone = make_line_edit(Register.PHONE_PLACEHOLDER, "phone")
        self.phone.setValidator(QRegularExpressionValidator(QRegularExpression(PHONE_CHARACTERS), self.phone))
        self.phone_field = FormField(Register.PHONE, self.phone)
        column.addLayout(_pair(self.name_field, self.phone_field))
        column.addSpacing(Space.S5)

        self.role = SegmentedControl([role_label(role) for role in SIGNUP_ROLES], height=Size.H_LG, accessible_name=Register.ROLE)
        self.role_field = FormField(Register.ROLE, self.role)
        column.addWidget(self.role_field)
        column.addSpacing(Space.S5)

        self.email = make_line_edit(Register.EMAIL_PLACEHOLDER, "mail")
        self.email.setValidator(QRegularExpressionValidator(QRegularExpression(EMAIL_CHARACTERS), self.email))
        self.email_field = FormField(Register.EMAIL, self.email, help_text=Register.EMAIL_HELP)
        column.addWidget(self.email_field)
        column.addSpacing(Space.S5)

        self.password = PasswordEdit()
        self.password_field = FormField(Register.PASSWORD, self.password)
        self.confirm = PasswordEdit()
        self.confirm_field = FormField(Register.CONFIRM_PASSWORD, self.confirm)
        column.addLayout(_pair(self.password_field, self.confirm_field))
        column.addSpacing(Space.S3)
        self.checklist = PasswordChecklist()
        column.addWidget(self.checklist)
        column.addSpacing(Space.S8)

        self.submit = make_button(Register.CREATE, "primary", "lg")
        self.submit.reserve_width(Register.CREATE, Register.CREATING)
        self.submit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        column.addWidget(self.submit)
        column.addSpacing(Space.S6)
        column.addLayout(labelled_divider(Register.HAVE_ACCOUNT))
        column.addSpacing(Space.S6)
        self.sign_in = make_button(Register.SIGN_IN, "secondary", "lg")
        self.sign_in.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        column.addWidget(self.sign_in)

        self.submit.clicked.connect(self._submit)
        self.sign_in.clicked.connect(self.back_to_login_clicked)
        self.password.textChanged.connect(self.checklist.set_password)
        for field in (self.name_field, self.phone_field, self.email_field, self.password_field, self.confirm_field):
            field.control.textChanged.connect(self._clear(field))
        self.role.selection_changed.connect(self._clear(self.role_field))

        order = [self.name, self.phone, *self.role.buttons, self.email, self.password, self.confirm,
                 self.submit, self.sign_in]
        for first, second in pairwise(order):
            self.setTabOrder(first, second)

    @staticmethod
    def _clear(field: FormField):
        """Slot that removes `field`'s error as soon as the user changes it."""
        @Slot()
        def clear(*_args) -> None:
            if field.has_error():
                field.set_error(None)
        return clear

    # ------------------------------------------------------------------ API
    def focus_first(self) -> None:
        """Focuses the name."""
        self.name.setFocus(Qt.FocusReason.OtherFocusReason)

    def set_busy(self, busy: bool) -> None:
        """Locks the form while the controller creates the account.

        Args:
            busy: True to lock it (and show the spinner), False to unlock it.
        """
        self._busy = busy
        for widget in (self.name, self.phone, self.role, self.email, self.password, self.confirm, self.sign_in):
            widget.setEnabled(not busy)
        self.submit.set_loading(busy, Register.CREATING)

    def is_busy(self) -> bool:
        """True while a sign-up request is being handled."""
        return self._busy

    def collect(self) -> RegistrationData:
        """Builds the DTO sent to the controller from the validated form.

        Returns:
            The caregiver's account.
        """
        return RegistrationData(
            name=self.name.text().strip(),
            email=self.email.text().strip(),
            phone=self.phone.text().strip(),
            password=self.password.text(),
            role=SIGNUP_ROLES[self.role.selected()],
        )

    def show_server_error(self, message: str, field: RegistrationField | None = None) -> None:
        """The controller refused the sign-up: point at the field, or explain it in the callout.

        Args:
            message: What went wrong; shown in the callout when no field is given.
            field: The field the controller rejected, or None.
        """
        self.set_busy(False)
        if field is RegistrationField.EMAIL:
            self.email_field.set_error(Register.EMAIL_IN_USE)
            self._reveal(self.email_field, self.email)
            self.email.selectAll()
        elif field is RegistrationField.ROLE:
            self.role_field.set_error(Register.ROLE_REQUIRED)
            self._reveal(self.role_field, self.role.focus_target())
        else:
            self.error.set_message(message)
            self._error_box.show()
            self.scroll.verticalScrollBar().setValue(0)

    def reset(self) -> None:
        """Unlocks the form and clears every field and error."""
        self.set_busy(False)
        self._error_box.hide()
        for edit in (self.name, self.phone, self.email, self.password, self.confirm):
            edit.clear()
        self.password.set_revealed(False)
        self.confirm.set_revealed(False)
        self.role.clear()
        for field in (self.name_field, self.phone_field, self.role_field, self.email_field,
                      self.password_field, self.confirm_field):
            field.set_error(None)
        self.scroll.verticalScrollBar().setValue(0)

    # ------------------------------------------------------------------ behaviour
    def _validate(self) -> list[tuple[FormField, QWidget]]:
        """Marks every invalid field; returns (field, widget to focus) for each, top to bottom."""
        errors: list[tuple[FormField, QWidget]] = []

        def fail(field: FormField, message: str, focus: QWidget | None = None) -> None:
            field.set_error(message)
            errors.append((field, focus or field.control))

        if not self.name.text().strip():
            fail(self.name_field, Register.NAME_REQUIRED)
        if not PHONE_PATTERN.match(self.phone.text().strip()):
            fail(self.phone_field, Register.PHONE_INVALID)
        if self.role.selected() < 0:
            fail(self.role_field, Register.ROLE_REQUIRED, self.role.focus_target())
        if not EMAIL_PATTERN.match(self.email.text().strip()):
            fail(self.email_field, Register.EMAIL_INVALID)
        if not all(PasswordChecklist.requirements(self.password.text()).values()):
            fail(self.password_field, Register.PASSWORD_WEAK)
        elif password_policy.too_long(self.password.text()):
            fail(self.password_field, Register.PASSWORD_TOO_LONG)
        if self.confirm.text() != self.password.text() or not self.confirm.text():
            fail(self.confirm_field, Register.PASSWORD_MISMATCH)
        return errors

    @Slot()
    def _submit(self) -> None:
        if self._busy:
            return
        self._error_box.hide()
        errors = self._validate()
        if errors:
            self._reveal(*errors[0])
            return
        self.set_busy(True)
        self.submitted.emit(self.collect())

    def _reveal(self, field: QWidget, focus: QWidget) -> None:
        """Scrolls the field into view (when the page scrolls at all) and focuses it."""
        self.scroll.ensureWidgetVisible(field, 0, Space.S6)
        focus.setFocus(Qt.FocusReason.OtherFocusReason)

    def resizeEvent(self, event) -> None:
        """Lets the form grow a little on wide screens, like the sign-in page."""
        super().resizeEvent(event)
        width = self.width()
        self._column_widget.setFixedWidth(max(COLUMN, min(COLUMN_MAX, round(width * 0.52))))
        self.heading.fit_to(width)

    def keyPressEvent(self, event) -> None:
        """Enter presses the focused button, moves to the next field or, from the last one, submits."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.accept()
            if self._busy:
                return
            focused = QApplication.focusWidget()
            if isinstance(focused, QAbstractButton):
                focused.click()
            elif isinstance(focused, QLineEdit) and focused is not self.confirm:
                self.focusNextChild()
            else:
                self._submit()
            return
        if event.key() == Qt.Key.Key_Escape:
            event.accept()
            return
        super().keyPressEvent(event)
