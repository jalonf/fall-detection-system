import logging

from PySide6.QtCore import QTimer

from src.database.database_manager import db
from src.dtos.registration_data import SELF_SERVICE_ROLES, RegistrationData
from src.repositories.patient_repository import PatientRepository
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

class AuthController:
    """
    Controller responsible for handling authentication-related logic.
    Connects its methods to the signals emitted by the AuthView.
    """
    def __init__(self, view, on_auth_success):
        self.view = view
        self.on_auth_success = on_auth_success
        
        # Connect native view signals to controller methods
        self.view.login_requested.connect(self.handle_login)
        self.view.register_requested.connect(self.handle_register)

        self.user_repo = UserRepository()
        self.patient_repo = PatientRepository()

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

    def handle_register(self, data: RegistrationData):
        """Handles new user registration and creates the associated patient."""
        logger.info("The controller is about to handle the registration process for: %s", data.email)

        if data.role not in SELF_SERVICE_ROLES:
            logger.warning("Registration rejected: role %r cannot be chosen when signing up", data.role)
            self.view.show_error("That role cannot be chosen when signing up.")
            return

        if self.user_repo.get_user_by_email(data.email):
            logger.warning("Registration failed: an account with this email already exists")
            self.view.show_error("Registration failed. This email is already in use.")
            return

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
                risk_level=data.risk_level
            )
            if not patient:
                transaction.rollback()

        if patient:
            logger.info("User account and associated patient successfully created")
            self.view.show_success("Account created successfully! Welcome.")
            QTimer.singleShot(1500, lambda: self.on_auth_success(new_user))
        else:
            logger.error("Registration failed: the account could not be saved")
            self.view.show_error("Registration failed. Please try again.")