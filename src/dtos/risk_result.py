"""RiskResult: the patient's risk level calculated from the questionnaire."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskResult:
    """Result of a risk assessment.

    Attributes:
        level: "LOW", "MEDIUM" or "HIGH"; it selects the monitoring strategy.
        probability: Probability (0-1) of an accident at home or during leisure time.
    """

    level: str
    probability: float
