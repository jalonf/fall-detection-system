"""Sign-in page: a 400 px column centred in the form area."""

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

from src.views.components.common.button import Button, make_button
from src.views.components.common.form_field import FormField
from src.views.components.common.inputs import PasswordEdit, make_line_edit
from src.views.components.common.toast import ToastHost
from src.views.strings import Login, Toasts, fields_need_attention
from src.views.theme import Space, make_label

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_CHARACTERS = r"[^\s@]*@?[^\s@]*"
COLUMN = 400


class LoginPage(QWidget):
    submitted = Signal(str, str)
    create_account_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._busy = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Space.S6, Space.S6, Space.S6, Space.S6)
        outer.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        column_widget = QWidget()
        column_widget.setFixedWidth(COLUMN)
        row.addWidget(column_widget)
        row.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(1)

        column = QVBoxLayout(column_widget)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        column.addWidget(make_label(Login.TITLE, "title-lg"))
        column.addSpacing(Space.S2)
        column.addWidget(make_label(Login.SUBTITLE, "body", "secondary", wrap=True))
        column.addSpacing(Space.S8)

        self.email = make_line_edit(Login.EMAIL_PLACEHOLDER, "mail")
        self.email.setValidator(QRegularExpressionValidator(QRegularExpression(EMAIL_CHARACTERS), self.email))
        self.email_field = FormField(Login.EMAIL, self.email)
        column.addWidget(self.email_field)
        column.addSpacing(Space.S5)

        self.password = PasswordEdit()
        self.password_field = FormField(Login.PASSWORD, self.password)
        column.addWidget(self.password_field)
        column.addSpacing(28)

        self.submit = make_button(Login.SUBMIT, "primary", "lg")
        self.submit.reserve_width(Login.SUBMIT, Login.SUBMITTING)
        self.submit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        column.addWidget(self.submit)
        column.addSpacing(Space.S6)

        link_row = QHBoxLayout()
        link_row.setSpacing(Space.S1)
        link_row.addStretch(1)
        link_row.addWidget(make_label(Login.NEW_HERE, "body", "secondary"))
        self.create_link = Button(Login.CREATE_ACCOUNT, "link", None)
        self.create_link.setFixedHeight(24)
        link_row.addWidget(self.create_link)
        link_row.addStretch(1)
        column.addLayout(link_row)

        self.submit.clicked.connect(self._submit)
        self.create_link.clicked.connect(self.create_account_clicked)
        self.email.textChanged.connect(self._clear_email_error)
        self.password.textChanged.connect(self._clear_password_error)

        self.setTabOrder(self.email, self.password)
        self.setTabOrder(self.password, self.submit)
        self.setTabOrder(self.submit, self.create_link)

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

    def show_server_error(self) -> None:
        """The controller rejected the credentials: unlock, mark the password and select it."""
        self.set_busy(False)
        self.password_field.set_error("")
        self.password.setFocus(Qt.FocusReason.OtherFocusReason)
        self.password.selectAll()

    def reset(self) -> None:
        self.set_busy(False)
        self.password.clear()
        self.password.set_revealed(False)
        self.email_field.set_error(None)
        self.password_field.set_error(None)

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
            ToastHost.for_widget(self).error(fields_need_attention(len(errors)), title=Toasts.VALIDATION_TITLE)
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
