import bcrypt
from src.database.models.user import User 

class UserRepository():
    """Handles all database operations for the users."""

    def create_user(self, name, email, phone, password, role):
        """Encrypts the password and saves the user in the DB."""
        try:
           # Encrypt the password for security
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            user = User.create(
                name=name,
                email=email,
                phone=phone,
                password=hashed_pw.decode('utf-8'),
                role=role
            )
            return user
        except Exception as e:
        
            print(f"[Repo Error] Could not create user: {e}")
            return None

    def get_user_by_email(self,email):
        """Finds a user by their email. Returns None if not found."""
        user = User.get_or_none(User.email == email)

        return user

    def verify_password(self, email, plain_password):
        """Verifies if the entered password matches the hashed one."""
        user = self.get_user_by_email(email)
        if not user:
            return False
            
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            user.password.encode('utf-8')
        )