"""Database access for user accounts, including password hashing."""

import logging

import bcrypt

from src.database.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Handles all database operations for the users."""

    def create_user(self, name, email, phone, password, role):
        """Encrypts the password and saves the user in the DB."""
        try:
            logger.info("Attempting to create new user with email: %s", email)
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
            logger.info("User successfully created in database with email: %s", user.email)
            return user
        except Exception as e:  # noqa: BLE001
            logger.error("Could not create user with email %s: %s", email, e)
            return None

    def get_user_by_email(self, email):
        """Finds a user by their email. Returns None if not found."""
        logger.debug("Querying user by email: %s", email)
        user = User.get_or_none(User.email == email)
        if user is None:
            logger.debug("No user found with email: %s", email)
        return user

    def authenticate(self, email, plain_password):
        """Returns the user whose e-mail and password these are, or None (one query).

        Args:
            email: The e-mail typed in.
            plain_password: The password typed in.
        """
        logger.debug("Verifying password for email: %s", email)
        user = self.get_user_by_email(email)
        if user is None:
            logger.warning("Password verification failed: user not found for email %s", email)
            return None
        if not bcrypt.checkpw(plain_password.encode("utf-8"), user.password.encode("utf-8")):
            logger.warning("Password verification failed: incorrect password for email %s", email)
            return None
        logger.debug("Password verification successful for email: %s", email)
        return user
