"""PatientSummary: one row of the Patients page, and one choice of the monitoring patient selector."""

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class PatientSummary:
    """A caregiver's patient as the interface shows it.

    Attributes:
        id: Database id of the patient (what the views send back to the controllers).
        name: Full name.
        risk_level: "LOW", "MEDIUM" or "HIGH".
        medical_notes: Medical notes, or "".
        added_at: When the patient was added.
        fall_count: Falls stored for the patient.
        last_fall_at: When the latest stored fall happened, or None.
    """

    id: int
    name: str
    risk_level: str
    medical_notes: str
    added_at: datetime.datetime
    fall_count: int = 0
    last_fall_at: datetime.datetime | None = None
