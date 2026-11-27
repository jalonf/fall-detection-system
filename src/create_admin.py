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
from src.strings import Register, role_label

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
        password = getpass.getpass("Contraseña: ")
        unmet = [rule for rule, met in password_policy.requirements(password).items() if not met]
        if unmet:
            labels = dict(Register.CHECKLIST)
            print(f"  A la contraseña le falta: {', '.join(labels[rule].lower() for rule in unmet)}.")
            continue
        if password_policy.too_long(password):
            print(f"  La contraseña es demasiado larga (máximo {password_policy.MAX_BYTES} bytes).")
            continue
        if getpass.getpass("Repite la contraseña: ") != password:
            print("  Las contraseñas no coinciden.")
            continue
        return password


def main(argv: list[str] | None = None) -> int:
    """Creates an administrator account from the prompts (or the arguments).

    Args:
        argv: Command-line arguments; None reads `sys.argv`.

    Returns:
        The exit code: 0 when the account was created, 1 otherwise.
    """
    parser = argparse.ArgumentParser(prog="python -m src.create_admin", description="Crea una cuenta de administrador.")
    parser.add_argument("--name", help="nombre completo (se pregunta si se omite)")
    parser.add_argument("--email", help="correo para iniciar sesión (se pregunta si se omite)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    print("Crea una cuenta de administrador (pruebas). No tiene paciente y hace todas las pruebas sin")
    print("guardar caídas ni enviar correos.\n")
    name = _ask("Nombre completo: ", args.name, bool, "Introduce un nombre.")
    email = _ask("Correo: ", args.email, EMAIL_PATTERN.match, "Introduce un correo válido.")

    init_tables([User, Patient, FallEvent])
    users = UserRepository()
    try:
        existing = users.get_user_by_email(email)
        if existing is not None:
            print(f"Ya existe una cuenta con {email} (rol: {role_label(existing.role)}). No se ha creado nada.")
            return 1

        password = _ask_password()
        user = users.create_user(name=name, email=email, phone=None, password=password, role=ADMINISTRATOR)
        if user is None:
            print("No se pudo crear la cuenta (consulta el error anterior).")
            return 1
        print(f"\nCuenta de administrador creada para {email}. Ya puedes iniciar sesión en la aplicación.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nCancelado. No se ha creado nada.")
        sys.exit(1)
