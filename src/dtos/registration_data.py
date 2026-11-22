"""RegistrationData: what the sign-up form sends to the controller."""

from dataclasses import dataclass, field


@dataclass
class RegistrationData:
    """DTO that contains the register information."""
    name: str
    email: str
    phone: str
    password: str
    role: str                 # one of `roles.SIGNUP_ROLES`
    patient_name: str
    medical_info: str
    # Answers to the health questionnaire (see src/dtos/questionnaire.py); the risk level is calculated from them.
    risk_answers: dict[str, float] = field(default_factory=dict)
