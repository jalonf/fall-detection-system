import bcrypt
from src.database.models.user import User 

class UserRepository():
    """Handles all database operations for the users."""
    def create_user(self, name, email, phone, password, role):
        """Encrypts the password and saves the user in the DB."""
        try:
            # 1. Encrypt the password for security
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            # 2. Create the record in the database
            user = User.create(
                name=name,
                email=email,
                phone=phone,
                password=hashed_pw.decode('utf-8'),
                role=role
            )
            return user
        except Exception as e:
            # Peewee will raise an IntegrityError if the email already exists
            print(f"[Repo Error] Could not create user: {e}")
            return None
    