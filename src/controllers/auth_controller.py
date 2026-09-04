from PySide6.QtCore import QTimer
from src.database.repositories.user_repository import UserRepository

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

    def handle_login(self, email, password):
        if not email or not password:
            self.view.show_error("Please fill in all required fields.")
            return

        if self.user_repo.verify_password(email, password):
            self.view.show_success("Welcome back! Authentication successful.")
            
            user = self.user_repo.get_user_by_email(email)
            QTimer.singleShot(1500, lambda: self.on_auth_success(user))
        else:
            self.view.show_error("Invalid email or password. Please try again.")

    def handle_register(self, name, email, phone, password, confirm, role):
        """Handles new user registration."""

        new_user = self.user_repo.create_user(
            name=name, email=email, phone=phone, 
            password=password, role=role
        )
        
        if new_user:
            self.view.show_success("Account created successfully! Welcome.")
            QTimer.singleShot(1500, lambda: self.on_auth_success(new_user))
        else:
            self.view.show_error("Registration failed. Email might already be in use.")