"""Password rules, shared by the sign-up form and `python -m src.create_admin`."""

MIN_LENGTH = 8
# bcrypt hashes at most 72 bytes of a password, and bcrypt 5 rejects longer ones with an error.
MAX_BYTES = 72


def requirements(password: str) -> dict[str, bool]:
    """Which rules the password meets (the keys match the sign-up form's checklist)."""
    return {
        "length": len(password) >= MIN_LENGTH,
        "upper": any(char.isupper() for char in password),
        "number": any(char.isdigit() for char in password),
        "symbol": any(not char.isalnum() and not char.isspace() for char in password),
    }


def too_long(password: str) -> bool:
    """Tells whether the password goes past bcrypt's 72-byte limit.

    Args:
        password: The password as typed.

    Returns:
        True when its UTF-8 encoding is longer than `MAX_BYTES`.
    """
    return len(password.encode("utf-8")) > MAX_BYTES
