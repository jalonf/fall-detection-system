"""The application's flow: which screen comes next (Application Controller / Coordinator pattern).

    sign-in ──(authenticated)──▶ dashboard of the user's role ──(sign out)──▶ sign-in

Views and controllers do not know about each other's screens: they only report events
(`on_auth_success` from the sign-in controller, `logout_requested` from the dashboard) and the
coordinator decides where to go and when. `_dashboard_for` is the factory that builds the dashboard
of each role (the view and one controller per page), the only place where the role decides the
screen. `Navigator` performs the change and frees the screen that is left.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow

from src.controllers.admin_controller import AdminController
from src.controllers.auth_controller import AuthController
from src.controllers.monitor_controller import MonitorController
from src.controllers.patients_controller import PatientsController
from src.domain.roles import is_admin
from src.navigation.navigator import Navigator, Screen
from src.views.auth_view import AuthView
from src.views.dashboard_view import AdminDashboardView, CaregiverDashboardView

logger = logging.getLogger(__name__)

# How long the "Signed in" toast is seen before the dashboard fades in.
SIGN_IN_HOLD_MS = 600


class AppCoordinator:
    """Decides which screen comes next and builds it.

    Args:
        window: The main window; the navigator shows the screens in it.
    """
    def __init__(self, window: QMainWindow):
        self.navigator = Navigator(window)
        self._auth_view = AuthView()
        # The sign-in screen is built once and reused after every sign-out (it resets itself when left).
        self._sign_in = Screen(self._auth_view, (AuthController(self._auth_view, on_auth_success=self.open_dashboard),),
                               persistent=True)
        self._signing_in = False

    def start(self) -> None:
        """Shows the first screen (call it once the window is visible)."""
        self.navigator.show(self._sign_in)

    # ------------------------------------------------------------------ flow
    def open_dashboard(self, user) -> None:
        """The user has signed in (or signed up): open the dashboard of their role after a short pause."""
        if self.navigator.current is not self._sign_in or self._signing_in:
            logger.warning("Ignoring a second dashboard request for %s", user.email)
            return
        self._signing_in = True
        QTimer.singleShot(SIGN_IN_HOLD_MS, self.navigator, lambda: self._show_dashboard(user))

    def _show_dashboard(self, user) -> None:
        self._signing_in = False
        if self.navigator.current is self._sign_in:
            self.navigator.show(self._dashboard_for(user))

    def sign_out(self) -> None:
        """Back to the sign-in screen; the navigator stops the dashboard's camera first."""
        self.navigator.show(self._sign_in)
        self._auth_view.show_signed_out()

    def shutdown(self) -> None:
        """The window is closing: let the current screen release the camera."""
        self.navigator.shutdown()

    # ------------------------------------------------------------------ screens
    def _dashboard_for(self, user) -> Screen:
        """Factory of the dashboard of each role: the view, and a controller for each of its pages."""
        if is_admin(user):
            # Administrators are testers: no patient, everything runs in test mode.
            view = AdminDashboardView(user_name=user.name, user_role=user.role)
            controllers = (AdminController(view.monitoring, current_user=user),)
        else:
            # Caregivers and medical staff: monitoring and their patients (with none yet, the Patients tab opens).
            view = CaregiverDashboardView(user_name=user.name, user_role=user.role)
            monitor = MonitorController(view.monitoring, current_user=user)
            patients = PatientsController(view.patients, user)
            patients.refresh()      # fills the Patients page and, through it, the monitoring page's selector
            controllers = (monitor, patients)
        view.logout_requested.connect(self.sign_out)
        return Screen(view, controllers)
