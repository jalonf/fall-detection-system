"""RegistrationData: what the sign-up form sends to the controller, and the fields it can reject."""

from dataclasses import dataclass
from enum import Enum


class RegistrationField(Enum):
    """A sign-up field the controller can reject, so the form points at it (`AuthView.show_error`)."""

    EMAIL = "email"   # already in use
    ROLE = "role"     # not one of the roles offered when signing up


@dataclass(frozen=True)
class RegistrationData:
    """The completed sign-up form: the caregiver's account (patients are added afterwards).

    Attributes:
        name: Full name of the caregiver.
        email: E-mail used to sign in and to receive the fall alerts.
        phone: Phone number with country code.
        password: The password as typed (the repository hashes it).
        role: One of `domain.roles.SIGNUP_ROLES`.
    """

    name: str
    email: str
    phone: str
    password: str
    role: str
