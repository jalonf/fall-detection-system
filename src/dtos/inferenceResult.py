from src.dtos.squeleton import Skeleton


class InferenceResult:
    """
    Immutable container for the AI pipeline output at a specific timestamp.
    """
    def __init__(
        self,
        skeleton: Skeleton | None,
        pose_landmarks: list | None = None,
        is_fall: bool = False,
        fall_probability: float = 0.0,
        inference_time_ms: float = 0.0,
    ):
        """
        Explicit constructor for rendering telemetry.

        Args:
            skeleton (Optional[Skeleton]): Tracked 3D skeleton DTO (world-space, for the AI model).
            pose_landmarks (Optional[list]): Normalized 2D screen-space landmarks for overlay drawing.
            is_fall (bool, optional): Triggered alert flag. Defaults to False.
            fall_probability (float, optional): AI model confidence [0.0, 1.0]. Defaults to 0.0.
            inference_time_ms (float, optional): Hardware execution latency. Defaults to 0.0.
        """
        self.skeleton = skeleton
        self.pose_landmarks = pose_landmarks
        self.is_fall = is_fall
        self.fall_probability = fall_probability
        self.inference_time_ms = inference_time_ms

    def __repr__(self) -> str:
        """Explicit string representation for console logging."""
        status = "EMERGENCY [FALL]" if self.is_fall else "NORMAL"
        return (
            f"InferenceResult(status={status}, "
            f"prob={self.fall_probability:.2f}, "
            f"latency={self.inference_time_ms:.1f}ms, "
            f"skeleton_present={self.skeleton is not None})"
        )

    from dataclasses import dataclass