"""FallAlert: the content of the fall-alert e-mail."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FallAlert:
    """What the caregiver is told about a fall.

    Attributes:
        patient_name: Who fell (the user's name when there is no patient).
        medical_notes: The patient's medical notes, or "N/A".
        probability: The model's probability (0-1) for the fall.
        timestamp: When it was detected, already formatted for the e-mail.
        snapshot: JPEG of the incident frame, kept only in memory (never written to disk), or None.
    """

    patient_name: str
    medical_notes: str
    probability: float
    timestamp: str
    snapshot: bytes | None = None
