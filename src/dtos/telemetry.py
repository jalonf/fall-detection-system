"""Telemetry: the measurements of one processed frame, shown in the administrators' pose panel."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Telemetry:
    """Measurements of one processed frame.

    The field names are also the keys of the pose panel's metrics (`skeleton_panel.Metric.key`).

    Attributes:
        inference_ms: Time spent processing the frame (pose extraction and pipeline), in ms.
        confidence: Mean visibility of the landmarks (0-1); 0 when nobody is detected.
        centroid_y: Normalised height of the hips' midpoint (0 = top of the frame, 1 = bottom),
            or None when the hips are not visible enough.
    """

    inference_ms: float
    confidence: float = 0.0
    centroid_y: float | None = None
