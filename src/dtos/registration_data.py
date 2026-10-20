from dataclasses import dataclass

# Roles anyone can pick when signing up. Administrators are not created from the form.
SELF_SERVICE_ROLES = ("Family / Caregiver", "Medical Staff")


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