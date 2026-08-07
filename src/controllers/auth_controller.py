class AuthController:
    """
    Controller responsible for handling authentication-related logic, 
    including user login and registration attempts, linking actions 
    from the authentication view to the application flow.
    """
    def __init__(self, view, on_auth_success):
        """
        Args:
            view: The authentication view instance containing user inputs and triggers.
            on_auth_success (callable): Callback function executed upon successful authentication.
        """
        self.view = view
        self.on_auth_success = on_auth_success
        
        self.view.on_login_attempt = self.handle_login
        self.view.on_register_attempt = self.handle_register

    def handle_login(self, email, password, remember):
        """
        Processes login requests from the view, validating credentials 
        and triggering success callbacks if valid.
        
        Args:
            email (str): User email address.
            password (str): User password.
            remember (bool): Flag indicating whether to remember the session.
        """
        print(f"Login with: {email}")
        if email and password:
            self.on_auth_success(email)
        else:
            print("Error: Invalid credentials")

    def handle_register(self, name, email, phone, password, confirm, role, terms):
        """
        Processes user registration requests, ensuring password confirmation 
        and agreement to terms before authorizing access.
        
        Args:
            name (str): Full name of the user.
            email (str): User email address.
            phone (str): Contact phone number.
            password (str): Account password.
            confirm (str): Password confirmation string.
            role (str): Assigned user role.
            terms (bool): Acceptance status of terms of use and privacy policy.
        """
        print(f"Register : {name} as {role}")
        if password == confirm and terms:
            self.on_auth_success(email)

