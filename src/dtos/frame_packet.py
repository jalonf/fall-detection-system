"""FramePacket: what the interface shows for one processed frame."""

from dataclasses import dataclass

from PySide6.QtGui import QImage


@dataclass(frozen=True)
class FramePacket:
    """DTO with everything the interface shows for one processed frame."""
    frame: QImage       # camera image with the person box and skeleton drawn on it
    skeleton: QImage    # skeleton alone, cropped around the person
    telemetry: dict     # inference_ms, centroid_y, confidence
