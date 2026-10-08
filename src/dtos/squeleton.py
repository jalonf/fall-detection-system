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

