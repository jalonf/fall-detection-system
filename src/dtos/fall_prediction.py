"""FallPrediction: the fall detection thread's state after the latest window of poses."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FallPrediction:
    """State of the fall detection thread after the latest window of poses.

    Attributes:
        is_fall: True while a fall is in progress (decided with hysteresis, see `FallDetectionThread`).
        probability: Probability (0-1) the model gave to the latest window.
    """

    is_fall: bool
    probability: float
