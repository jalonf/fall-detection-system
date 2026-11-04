from dataclasses import dataclass

import numpy as np


@dataclass
class Skeleton:
    """DTO that contains the diferent types of coordinates of a frame."""
    pose: np.ndarray
    landmarks_2d: list
