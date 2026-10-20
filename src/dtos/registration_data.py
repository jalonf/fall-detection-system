from dataclasses import dataclass

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
    risk_level: str