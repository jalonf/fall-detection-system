"""PatientFormData: what the new patient form sends to the controller."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PatientFormData:
    """The completed new patient form.

    Attributes:
        name: Full name of the patient.
        medical_notes: Optional medical notes ("" when left empty).
        risk_answers: Answers to the health questionnaire (`domain.questionnaire`), keyed by model
            feature; the patient's risk level is calculated from them.
    """

    name: str
    medical_notes: str = ""
    risk_answers: dict[str, float] = field(default_factory=dict)
