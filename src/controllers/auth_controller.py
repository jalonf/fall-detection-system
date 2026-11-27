"""Controller of the sign-in and sign-up screen."""

import logging

from PySide6.QtCore import QObject, Slot

from src.domain.roles import SIGNUP_ROLES
from src.dtos.registration_data import RegistrationData, RegistrationField
from src.repositories.user_repository import UserRepository
from src.strings import Messages

logger = logging.getLogger(__name__)

class AuthController(QObject):
    """Handles sign-in and sign-up for the AuthView.

    It is a QObject living in the GUI thread, like the monitoring controllers, so its
    handlers are real Qt slots. It answers every request synchronously, with `show_error`,
    `show_signed_in` or `show_account_created` on the view.

    Args:
        view: The AuthView whose `login_requested` / `register_requested` it handles.
        on_auth_success: Called with the User once they have signed in or signed up (the
            coordinator decides when the next screen opens).
    """
    def __init__(self, view, on_auth_success):
        super().__init__()
        self.view = view
        self.on_auth_success = on_auth_success
        
        # Connect native view signals to controller methods
        self.view.login_requested.connect(self.handle_login)
        self.view.register_requested.connect(self.handle_register)

        self.user_repo = UserRepository()

    @Slot(str, str)
    def handle_login(self, email, password):
        """Handles user login."""
        logger.info("The controller is about to handle the login process")
        if not email or not password:
            logger.warning("Login attempt failed: missing required fields")
            self.view.show_error(Messages.REQUIRED_FIELDS)
            return

        user = self.user_repo.authenticate(email, password)
        if user is not None:
            logger.info("User authentication successful")
            self.view.show_signed_in()
            self.on_auth_success(user)
        else:
            logger.warning("Authentication failed: invalid credentials provided")
            self.view.show_error(Messages.BAD_CREDENTIALS)

    @Slot(object)      # RegistrationData (a Python object, as in AuthView.register_requested)
    def handle_register(self, data: RegistrationData):
        """Creates the caregiver's account. Their patients are added afterwards, on the Patients page."""
        logger.info("The controller is about to handle the registration process for: %s", data.email)

        # Administrators are created with `python -m src.create_admin`, never from the sign-up form.
        if data.role not in SIGNUP_ROLES:
            logger.warning("Registration rejected: role %r cannot be chosen when signing up", data.role)
            self.view.show_error(Messages.INVALID_ROLE, RegistrationField.ROLE)
            return

        if self.user_repo.get_user_by_email(data.email):
            logger.warning("Registration failed: an account with this email already exists")
            self.view.show_error(Messages.EMAIL_TAKEN, RegistrationField.EMAIL)
            return

        new_user = self.user_repo.create_user(
            name=data.name,
            email=data.email,
            phone=data.phone,
            password=data.password,
            role=data.role
        )

        if new_user:
            logger.info("User account successfully created")
            self.view.show_account_created()
            self.on_auth_success(new_user)
        else:
            logger.error("Registration failed: the account could not be saved")
            self.view.show_error(Messages.REGISTRATION_FAILED)