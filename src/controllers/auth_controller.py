"""Controller of the sign-in and sign-up screen."""

import logging

from PySide6.QtCore import QObject, QTimer, Slot

from src.ai.risk_assessor import RiskAssessor
from src.database.connection import db
from src.domain.roles import SIGNUP_ROLES
from src.dtos.registration_data import RegistrationData
from src.repositories.patient_repository import PatientRepository
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

class AuthController(QObject):
    """Handles sign-in and sign-up for the AuthView.

    It is a QObject living in the GUI thread, like the monitoring controllers, so its
    handlers are real Qt slots. It answers every request synchronously, with `show_error`
    or `show_success` on the view.

    Args:
        view: The AuthView whose `login_requested` / `register_requested` it handles.
        on_auth_success: Called with the User once they have signed in or signed up.
    """
    def __init__(self, view, on_auth_success):
        super().__init__()
        self.view = view
        self.on_auth_success = on_auth_success
        
        # Connect native view signals to controller methods
        self.view.login_requested.connect(self.handle_login)
        self.view.register_requested.connect(self.handle_register)

        self.user_repo = UserRepository()
        self.patient_repo = PatientRepository()
        self.risk_assessor = RiskAssessor()

    @Slot(str, str)
    def handle_login(self, email, password):
        """Handles user login."""
        logger.info("The controller is about to handle the login process")
        if not email or not password:
            logger.warning("Login attempt failed: missing required fields")
            self.view.show_error("Please fill in all required fields.")
            return

        if self.user_repo.verify_password(email, password):
            logger.info("User authentication successful")
            self.view.show_success("Welcome back! Authentication successful.")
            
            user = self.user_repo.get_user_by_email(email)
            QTimer.singleShot(1500, lambda: self.on_auth_success(user))
        else:
            logger.warning("Authentication failed: invalid credentials provided")
            self.view.show_error("Invalid email or password. Please try again.")

    def _assess_risk(self, answers: dict[str, float]) -> str:
        """Risk level of the patient. If it cannot be calculated, the strictest monitoring is used."""
        try:
            return self.risk_assessor.assess(answers).level
        except Exception:   # whatever the cause (missing model, bad answers), registration goes on
            logger.exception("The risk level could not be calculated; using HIGH to be safe")
            return "HIGH"

    @Slot(object)      # RegistrationData (a Python object, as in AuthView.register_requested)
    def handle_register(self, data: RegistrationData):
        """Handles new user registration and creates the associated patient."""
        logger.info("The controller is about to handle the registration process for: %s", data.email)

        # Administrators are created with `python -m src.create_admin`, never from the sign-up form.
        if data.role not in SIGNUP_ROLES:
            logger.warning("Registration rejected: role %r cannot be chosen when signing up", data.role)
            self.view.show_error("Please choose a valid user role.")
            return

        if self.user_repo.get_user_by_email(data.email):
            logger.warning("Registration failed: an account with this email already exists")
            self.view.show_error("Registration failed. This email is already in use.")
            return

        risk_level = self._assess_risk(data.risk_answers)

        # The user and its patient are saved together: if the patient fails, the user is undone too.
        with db.atomic() as transaction:
            new_user = self.user_repo.create_user(
                name=data.name,
                email=data.email,
                phone=data.phone,
                password=data.password,
                role=data.role
            )
            patient = new_user and self.patient_repo.create_patient(
                user=new_user,
                name=data.patient_name,
                medical_notes=data.medical_info,
                risk_level=risk_level
            )
            if not patient:
                transaction.rollback()

        if patient:
            logger.info("User account and associated patient successfully created")
            self.view.show_success(f"Account created! The patient's risk level is {risk_level}.")
            QTimer.singleShot(1500, lambda: self.on_auth_success(new_user))
        else:
            logger.error("Registration failed: the account could not be saved")
            self.view.show_error("Registration failed. Please try again.")