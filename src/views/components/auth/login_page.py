"""Sign-in page: a 480 px column centred in the form area.

It follows the sign-up page's structure (title, subtitle, full-width fields and buttons), with
"Create an account" as a full-width secondary button under a labelled divider. Errors from the
controller show inline in a danger callout above the fields; there are no error toasts.
"""

from __future__ import annotations

import re

from PySide6.QtCore import QRegularExpression, Qt, Signal, Slot
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractButton,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.views.components.auth.page_heading import PageHeading
from src.views.components.common.button import make_button
from src.views.components.common.callout import Callout
from src.views.components.common.form_field import FormField
from src.views.components.common.inputs import PasswordEdit, make_line_edit
from src.views.components.common.painting import Divider
from src.views.strings import Login
from src.views.theme import Colors, Space, make_label

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_CHARACTERS = r"[^\s@]*@?[^\s@]*"
COLUMN = 480


class LoginPage(QWidget):
    submitted = Signal(str, str)
    create_account_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._busy = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Space.S8, Space.S8, Space.S8, Space.S8)
        outer.addStretch(2)
        row = QHBoxLayout()
        row.addStretch(1)
        column_widget = QWidget()
        column_widget.setFixedWidth(COLUMN)
        row.addWidget(column_widget)
        row.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(3)

        column = QVBoxLayout(column_widget)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        column.addWidget(PageHeading("log-in", Login.TITLE, Login.SUBTITLE))
        column.addSpacing(Space.S8)

        self.error = Callout("", "danger")
        self._error_box = QWidget()             # the callout and its 20 px gap, shown together
        error_layout = QVBoxLayout(self._error_box)
        error_layout.setContentsMargins(0, 0, 0, Space.S5)
        error_layout.addWidget(self.error)
        column.addWidget(self._error_box)

        self.email = make_line_edit(Login.EMAIL_PLACEHOLDER, "mail")
        self.email.setValidator(QRegularExpressionValidator(QRegularExpression(EMAIL_CHARACTERS), self.email))
        self.email_field = FormField(Login.EMAIL, self.email)
        column.addWidget(self.email_field)
        column.addSpacing(Space.S5)

        self.password = PasswordEdit()
        self.password_field = FormField(Login.PASSWORD, self.password)
        column.addWidget(self.password_field)
        column.addSpacing(Space.S8)

        self.submit = make_button(Login.SUBMIT, "primary", "lg")
        self.submit.reserve_width(Login.SUBMIT, Login.SUBMITTING)
        self.submit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        column.addWidget(self.submit)
        column.addSpacing(Space.S6)

        divider = QHBoxLayout()
        divider.setSpacing(Space.S3)
        divider.addWidget(Divider(Colors.N200), 1, Qt.AlignmentFlag.AlignVCenter)
        divider.addWidget(make_label(Login.NEW_HERE, "caption", "tertiary"))
        divider.addWidget(Divider(Colors.N200), 1, Qt.AlignmentFlag.AlignVCenter)
        column.addLayout(divider)
        column.addSpacing(Space.S6)

        self.create_link = make_button(Login.CREATE_ACCOUNT, "secondary", "lg")
        self.create_link.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        column.addWidget(self.create_link)

        self.submit.clicked.connect(self._submit)
        self.create_link.clicked.connect(self.create_account_clicked)
        self.email.textChanged.connect(self._clear_email_error)
        self.password.textChanged.connect(self._clear_password_error)

        self.setTabOrder(self.email, self.password)
        self.setTabOrder(self.password, self.submit)
        self.setTabOrder(self.submit, self.create_link)
        self._set_error_visible(False)

    # ------------------------------------------------------------------ API
    def focus_first(self) -> None:
        target = self.password if self.email.text() and not self.password.text() else self.email
        target.setFocus(Qt.FocusReason.OtherFocusReason)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.email.setEnabled(not busy)
        self.password.setEnabled(not busy)
        self.create_link.setEnabled(not busy)
        self.submit.set_loading(busy, Login.SUBMITTING)

    def is_busy(self) -> bool:
        return self._busy

    def show_server_error(self, message: str) -> None:
        """The controller rejected the sign-in: unlock, explain why and select the password."""
        self.set_busy(False)
        self.error.set_message(message)
        self._set_error_visible(True)
        self.password_field.set_error("")
        self.password.setFocus(Qt.FocusReason.OtherFocusReason)
        self.password.selectAll()

    def reset(self) -> None:
        self.set_busy(False)
        self.password.clear()
        self.password.set_revealed(False)
        self.email_field.set_error(None)
        self.password_field.set_error(None)
        self._set_error_visible(False)

    def _set_error_visible(self, visible: bool) -> None:
        self._error_box.setVisible(visible)

    # ------------------------------------------------------------------ behaviour
    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.accept()
            if self._busy:
                return
            focused = self.focusWidget()
            if isinstance(focused, QAbstractButton) and focused is not self.submit:
                focused.click()
            elif focused is self.email:
                self.password.setFocus(Qt.FocusReason.TabFocusReason)
            else:
                self._submit()
            return
        if event.key() == Qt.Key.Key_Escape:
            event.accept()
            return
        super().keyPressEvent(event)

    @Slot()
    def _submit(self) -> None:
        if self._busy:
            return
        self._set_error_visible(False)
        email = self.email.text().strip()
        password = self.password.text()
        errors = []
        if not email:
            self.email_field.set_error(Login.EMAIL_REQUIRED)
            errors.append(self.email)
        elif not EMAIL_PATTERN.match(email):
            self.email_field.set_error(Login.EMAIL_INVALID)
            errors.append(self.email)
        if not password:
            self.password_field.set_error(Login.PASSWORD_REQUIRED)
            errors.append(self.password)
        if errors:
            errors[0].setFocus(Qt.FocusReason.OtherFocusReason)
            return
        self.set_busy(True)
        self.submitted.emit(email, password)

    @Slot()
    def _clear_email_error(self) -> None:
        if self.email_field.has_error():
            self.email_field.set_error(None)

    @Slot()
    def _clear_password_error(self) -> None:
        if self.password_field.has_error():
            self.password_field.set_error(None)
