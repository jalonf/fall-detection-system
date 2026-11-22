"""Skeleton: the pose MediaPipe extracts from one frame."""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Skeleton:
    """The pose of the person in one frame, in the two forms the pipeline needs.

    Attributes:
        pose: Model input: 33 landmarks x (x, y, z) in metres, centred on the hips.
        landmarks_2d: MediaPipe's normalised screen-space landmarks (x, y in 0-1 and visibility),
            used to draw the skeleton, crop the person and blur the face.
    """

    pose: np.ndarray
    landmarks_2d: list[Any]
