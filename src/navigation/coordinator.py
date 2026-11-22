"""The application's flow: which screen comes next (Application Controller / Coordinator pattern).

    sign-in ──(authenticated)──▶ dashboard of the user's role ──(sign out)──▶ sign-in

Views and controllers do not know about each other's screens: the controllers only report events
(`on_auth_success`, `on_logout_callback`) and the coordinator decides where to go. `_dashboard_for` is
the factory that builds the dashboard (view + controller) of each role, the only place where the role
decides the screen. `Navigator` performs the change and frees the screen that is left.
"""

from __future__ import annotations

import logging

from PySide6.QtWidgets import QMainWindow

from src.controllers.admin_controller import AdminController
from src.controllers.auth_controller import AuthController
from src.controllers.monitor_controller import MonitorController
from src.dtos.roles import is_admin
from src.navigation.navigator import Navigator, Screen
from src.repositories.patient_repository import PatientRepository
from src.views.admin_view import AdminView
from src.views.auth_view import AuthView
from src.views.monitor_view import MonitorView

logger = logging.getLogger(__name__)


class AppCoordinator:
    """Decides which screen comes next and builds it.

    Args:
        window: The main window; the navigator shows the screens in it.
    """
    def __init__(self, window: QMainWindow):
        self.navigator = Navigator(window)
        self._patients = PatientRepository()

        auth_view = AuthView()
        # The sign-in screen is built once and reused after every sign-out (it resets itself when shown).
        self._sign_in = Screen(auth_view, AuthController(auth_view, on_auth_success=self.open_dashboard),
                               persistent=True)
        self.navigator.show(self._sign_in)

    # ------------------------------------------------------------------ flow
    def open_dashboard(self, user) -> None:
        """The user has signed in (or signed up): open the dashboard of their role."""
        if self.navigator.current is not self._sign_in:
            logger.warning("Ignoring a second dashboard request for %s", user.email)
            return
        self.navigator.show(self._dashboard_for(user))

    def sign_out(self) -> None:
        """Back to the sign-in screen; the navigator stops the dashboard's camera first."""
        self.navigator.show(self._sign_in)

    def shutdown(self) -> None:
        """The window is closing: let the current screen release the camera."""
        self.navigator.shutdown()

    # ------------------------------------------------------------------ screens
    def _dashboard_for(self, user) -> Screen:
        """Factory of the dashboard of each role."""
        if is_admin(user):
            # Administrators are testers: no patient, everything runs in test mode.
            view = AdminView(user_name=user.name, user_role=user.role)
            return Screen(view, AdminController(view, current_user=user, on_logout_callback=self.sign_out))

        patient = self._patients.get_patient_by_caregiver(user)
        view = MonitorView(user_name=user.name, user_role=user.role, patient_name=getattr(patient, "name", None),
                           risk_level=getattr(patient, "risk_level", None))
        controller = MonitorController(view, current_user=user, patient=patient, on_logout_callback=self.sign_out)
        return Screen(view, controller)
