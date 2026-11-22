"""FallPrediction: the fall model's output for one window of poses."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FallPrediction:
    """Output of the fall model for the latest window of poses.

    Attributes:
        is_fall: True when the probability reaches the decision threshold.
        probability: Probability (0-1) that the window shows a fall.
    """

    is_fall: bool
    probability: float
