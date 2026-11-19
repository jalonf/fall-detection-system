from dataclasses import dataclass, field

# Roles that can be chosen when signing up.
USER_ROLES = ("Family / Caregiver", "Medical Staff", "Administrator")


@dataclass
class RegistrationData:
    """DTO that contains the register information."""
    name: str
    email: str
    phone: str
    password: str
    role: str
    patient_name: str
    medical_info: str
    # Answers to the health questionnaire (see src/dtos/questionnaire.py); the risk level is calculated from them.
    risk_answers: dict[str, float] = field(default_factory=dict)
