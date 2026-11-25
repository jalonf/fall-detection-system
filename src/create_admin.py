"""Creates an administrator (tester) account.

    python -m src.create_admin
    python -m src.create_admin --name "Ana García" --email ana@example.com

Administrators cannot sign up from the application: that form only offers the monitoring roles, so
nobody can give themselves the administration screen. They have no patient; in the application they
test the camera profiles and analyse video files without storing falls or sending e-mails.

The password is always typed at the prompt (never passed as an argument, so it does not end up in the
shell history) and follows the same rules as the sign-up form.
"""

import argparse
import getpass
import logging
import re
import sys

from src.database.connection import db, init_tables
from src.database.models.fall_event import FallEvent
from src.database.models.patient import Patient
from src.database.models.user import User
from src.domain import password_policy
from src.domain.roles import ADMINISTRATOR
from src.repositories.user_repository import UserRepository

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")   # same rule as the sign-in form


def _ask(prompt: str, value: str | None, valid, error: str) -> str:
    """Returns `value` when it is valid, otherwise asks until a valid answer is typed."""
    while True:
        value = (value if value is not None else input(prompt)).strip()
        if valid(value):
            return value
        print(f"  {error}")
        value = None


def _ask_password() -> str:
    while True:
        password = getpass.getpass("Password: ")
        unmet = [rule for rule, met in password_policy.requirements(password).items() if not met]
        if unmet:
            print(f"  The password needs: {', '.join(unmet)} "
                  f"(at least {password_policy.MIN_LENGTH} characters, an uppercase letter, a number and a symbol).")
            continue
        if password_policy.too_long(password):
            print(f"  The password is too long (at most {password_policy.MAX_BYTES} bytes).")
            continue
        if getpass.getpass("Confirm password: ") != password:
            print("  The passwords don't match.")
            continue
        return password


def main(argv: list[str] | None = None) -> int:
    """Creates an administrator account from the prompts (or the arguments).

    Args:
        argv: Command-line arguments; None reads `sys.argv`.

    Returns:
        The exit code: 0 when the account was created, 1 otherwise.
    """
    parser = argparse.ArgumentParser(prog="python -m src.create_admin", description="Create an administrator account.")
    parser.add_argument("--name", help="full name (asked when omitted)")
    parser.add_argument("--email", help="e-mail used to sign in (asked when omitted)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    print("Create an administrator (tester) account. It has no patient and runs every test without")
    print("storing falls or sending e-mails.\n")
    name = _ask("Full name: ", args.name, bool, "Enter a name.")
    email = _ask("E-mail: ", args.email, EMAIL_PATTERN.match, "Enter a valid e-mail address.")

    init_tables([User, Patient, FallEvent])
    users = UserRepository()
    try:
        existing = users.get_user_by_email(email)
        if existing is not None:
            print(f"There is already an account with {email} (role: {existing.role}). Nothing was created.")
            return 1

        password = _ask_password()
        user = users.create_user(name=name, email=email, phone=None, password=password, role=ADMINISTRATOR)
        if user is None:
            print("The account could not be created (see the error above).")
            return 1
        print(f"\nAdministrator account created for {email}. Sign in with it in the application.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled. Nothing was created.")
        sys.exit(1)
