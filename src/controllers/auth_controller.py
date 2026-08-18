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

    def handle_login(self, email, password, remember):
        print(f"Login with: {email}")
        if self.user_repo.verify_password(email, password):
            self.on_auth_success(email)
        else:
            print("Error: Invalid credentials")

    def handle_register(self, name, email, phone, password, confirm, role, terms):
        if password != confirm:
            print("Error: Passwords do not match")
            return
            
        if not terms:
            print("Error: You must accept the terms of use")
            return

        new_user = self.user_repo.create_user(
            name=name, email=email, phone=phone, 
            password=password, role=role
        )

        print(f"Register : {name} as {role}")
        
        if new_user:
            self.on_auth_success(email)
        else:
            print("Error: Registration failed")