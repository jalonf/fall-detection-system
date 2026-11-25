"""Sign-in and sign-up screen.

Contract (used by `AuthController`): the view emits `login_requested(email, password)` and
`register_requested(RegistrationData)`; the controller answers each request synchronously, before
the signal returns, with one of `show_error(message, field)`, `show_signed_in()` or
`show_account_created(risk_level)`. The answer is data, never a sentence the view has to parse.
The same instance is shown again after every logout, so it resets itself when shown again.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from src.dtos.registration_data import RegistrationData, RegistrationField
from src.views.components.auth.brand_panel import BrandPanel
from src.views.components.auth.login_page import LoginPage
from src.views.components.auth.page_transition import PageTransition
from src.views.components.auth.register_page import RegisterPage
from src.views.components.common.toast import ToastHost
from src.views.strings import Common, Toasts
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
    def show_error(self, message: str, field: RegistrationField | None = None) -> None:
        """The controller refused the request: shown inline on the page that sent it (no toast).

        Args:
            message: What went wrong, for the user.
            field: The sign-up field to point at, or None to show `message` in the form.
        """
        self._answered = True
        if self._pages.currentWidget() is self.register_page:
            self.register_page.show_server_error(message, field)
        else:
            self.login_page.show_server_error(message)

    def show_signed_in(self) -> None:
        """Sign-in succeeded. The form stays locked while the dashboard opens."""
        self._answered = True
        ToastHost.for_widget(self).success(Toasts.SIGNED_IN, title=Toasts.SIGNED_IN_TITLE)

    def show_account_created(self, risk_level: str) -> None:
        """Sign-up succeeded. The form stays locked while the dashboard opens.

        Args:
            risk_level: The patient's risk level ("LOW", "MEDIUM" or "HIGH").
        """
        self._answered = True
        ToastHost.for_widget(self).success(Toasts.ACCOUNT_CREATED.format(level=risk_level),
                                           title=Toasts.ACCOUNT_CREATED_TITLE)

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
        """Keeps the brand panel at 45 % of the width, between 440 and 860 px.

        On wide screens it keeps growing (up to 860 px), so the form area beside it does not turn
        into a wide empty white space around a small form.
        """
        super().resizeEvent(event)
        self._brand.set_target_width(max(440, min(860, round(self.width() * 0.45))))

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
