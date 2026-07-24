from typing import Optional
import numpy as np

class Skeleton:
    """
    Represents the 3D anatomical structure of a person in a single frame.
    """
    def __init__(self, coordinates_3d: np.ndarray, visibility: np.ndarray, num_landmarks: int = 33):
        """
        Explicit constructor with immediate defensive programming validation.

        Args:
            coordinates_3d (np.ndarray): Shape (33, 3) -> [x, y, z] in meters.
            visibility (np.ndarray): Shape (33,) -> Confidence scores [0.0, 1.0].
            num_landmarks (int, optional): Expected landmark count. Defaults to 33.
            
        """
        self.num_landmarks = num_landmarks
        self.coordinates_3d = coordinates_3d
        self.visibility = visibility


    def normalize_center_of_mass(self) -> "Skeleton":
        """Updates the 3D coordinates to normalized coordinates using the hip center as the origin."""
        left_hip = self.coordinates_3d[23]
        right_hip = self.coordinates_3d[24]

        center_of_mass = (left_hip + right_hip) / 2

        self.coordinates_3d -= center_of_mass
        return self

    def to_array(self) -> np.ndarray:
        """Returns the coordinates array for temporal window stacking."""
        return self.coordinates_3d

    def __repr__(self) -> str:
        """Explicit string representation for console debugging."""
        return f"Skeleton(landmarks={self.num_landmarks}, normalized_shape={self.coordinates_3d.shape})"


class InferenceResult:
    """
    Immutable container for the AI pipeline output at a specific timestamp.
    """
    def __init__(self, skeleton: Optional[Skeleton], is_fall: bool= False, fall_probability: float = 0.0, inference_time_ms: float = 0.0):
        """
        Explicit constructor for rendering telemetry.

        Args:
            skeleton (Optional[Skeleton]): Tracked skeleton DTO, or None if no human detected.
            is_fall (bool, optional): Triggered alert flag. Defaults to False.
            fall_probability (float, optional): AI model confidence [0.0, 1.0]. Defaults to 0.0.
            inference_time_ms (float, optional): Hardware execution latency. Defaults to 0.0.
        """
        self.skeleton = skeleton
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