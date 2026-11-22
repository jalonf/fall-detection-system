"""Sign-in and sign-up screen.

Contract (used by `main.py` and `AuthController`): `login_requested(email, password)`,
`register_requested(RegistrationData)`, `show_error(message)` and `show_success(message)`.
The controller answers each request synchronously, with `show_error` or `show_success`, before the
signal returns. The same instance is shown again after every logout, so it resets itself when shown again.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from src.dtos.registration_data import RegistrationData
from src.views.components.auth.brand_panel import BrandPanel
from src.views.components.auth.login_page import LoginPage
from src.views.components.auth.page_transition import PageTransition
from src.views.components.auth.register_page import RegisterPage
from src.views.components.common.toast import ToastHost
from src.views.strings import Common, Toasts, risk_level_in, toast_rule_for
from src.views.theme import Colors

TOAST_TOP_INSET = 16


class _FormArea(QWidget):
    def paintEvent(self, event) -> None:
        QPainter(self).fillRect(self.rect(), QColor(Colors.N0))


class AuthView(QWidget):
    """Sign-in and sign-up screen: the brand panel on the left, the form pages on the right.

    Signals:
        login_requested(str, str): E-mail and password to sign in with.
        register_requested(RegistrationData): The completed sign-up form.
    """
    login_requested = Signal(str, str)
    register_requested = Signal(RegistrationData)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._hidden_by_app = False
        self._answered = True

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._brand = BrandPanel()
        layout.addWidget(self._brand)

        self._form = _FormArea()
        form_layout = QVBoxLayout(self._form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        self._pages = QStackedWidget()
        self.login_page = LoginPage()
        self.register_page = RegisterPage()
        self._pages.addWidget(self.login_page)
        self._pages.addWidget(self.register_page)
        form_layout.addWidget(self._pages)
        layout.addWidget(self._form, 1)
        self._transition = PageTransition(self._form)
        self._transition.finished.connect(self._focus_current_page)

        self.login_page.submitted.connect(self._on_login_submitted)
        self.login_page.create_account_clicked.connect(self._show_register)
        self.register_page.submitted.connect(self._on_register_submitted)
        self.register_page.back_to_login_clicked.connect(self._show_login)

    # ------------------------------------------------------------------ contract
    @Slot(str)
    def show_error(self, message: str) -> None:
        """Errors are shown inline on the page that caused them (no toast)."""
        self._answered = True
        if self._pages.currentWidget() is self.register_page:
            self.register_page.show_server_error(message)
        else:
            self.login_page.show_server_error(message)

    @Slot(str)
    def show_success(self, message: str) -> None:
        """Success keeps the form locked: `main.py` opens the dashboard 1.5 s later."""
        self._answered = True
        rule = toast_rule_for("success", message)
        toasts = ToastHost.for_widget(self)
        if rule is None:
            toasts.success(message)
            return
        toasts.notify(rule.kind, rule.message.format(level=risk_level_in(message), text=message), title=rule.title)

    # ------------------------------------------------------------------ pages
    @Slot(str, str)
    def _on_login_submitted(self, email: str, password: str) -> None:
        self._answered = False
        self.login_requested.emit(email, password)
        self._unlock_if_unanswered()

    @Slot(object)
    def _on_register_submitted(self, data: RegistrationData) -> None:
        self._answered = False
        self.register_requested.emit(data)
        self._unlock_if_unanswered()

    def _unlock_if_unanswered(self) -> None:
        """Unlocks the page with a generic error when the controller did not answer.

        If the controller raised instead of answering (a database error, a password bcrypt
        rejects...), PySide only prints the exception and the page would stay locked on
        "Signing in…" for good.
        """
        if not self._answered:
            self.show_error(Common.UNEXPECTED_ERROR)

    @Slot()
    def _show_register(self) -> None:
        if not self.login_page.is_busy() and not self._transition.is_running():
            self._transition.slide(self._pages, self.register_page, forward=True)

    @Slot()
    def _show_login(self) -> None:
        if not self.register_page.is_busy() and not self._transition.is_running():
            self._transition.slide(self._pages, self.login_page, forward=False)

    @Slot()
    def _focus_current_page(self) -> None:
        self._pages.currentWidget().focus_first()

    def _reset(self) -> None:
        self.setUpdatesEnabled(False)
        try:
            self.login_page.reset()
            self.register_page.reset()
            self._pages.setCurrentWidget(self.login_page)
        finally:
            self.setUpdatesEnabled(True)

    # ------------------------------------------------------------------ events
    def resizeEvent(self, event) -> None:
        """Keeps the brand panel at 40 % of the width, between 440 and 640 px."""
        super().resizeEvent(event)
        self._brand.set_target_width(max(440, min(640, round(self.width() * 0.40))))

    def showEvent(self, event) -> None:
        """Resets the forms after a sign-out and focuses the first field."""
        super().showEvent(event)
        if event.spontaneous():
            return
        ToastHost.for_widget(self).set_top_inset(TOAST_TOP_INSET)
        if self._hidden_by_app:      # back after signing out
            self._hidden_by_app = False
            self._reset()
            ToastHost.for_widget(self).success(Toasts.SIGNED_OUT, title=Toasts.SIGNED_OUT_TITLE)
        self._pages.currentWidget().focus_first()

    def hideEvent(self, event) -> None:
        """Remembers that the app hid the screen (a sign-in), so it resets when shown again."""
        super().hideEvent(event)
        if not event.spontaneous():
            self._hidden_by_app = True

    def keyPressEvent(self, event) -> None:
        """Ignores Esc, which has no meaning on these screens."""
        if event.key() == Qt.Key.Key_Escape:   # Esc does nothing on these screens
            event.accept()
            return
        super().keyPressEvent(event)
