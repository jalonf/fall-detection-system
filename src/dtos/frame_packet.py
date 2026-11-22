"""FramePacket: what the interface shows for one processed frame."""

from dataclasses import dataclass

from PySide6.QtGui import QImage

from src.dtos.telemetry import Telemetry


@dataclass(frozen=True)
class FramePacket:
    """Everything the interface shows for one processed frame.

    Attributes:
        frame: Camera image with the person box and the skeleton drawn on it.
        skeleton: The skeleton alone, cropped around the person.
        telemetry: Measurements of the frame (administrators' pose panel).
    """

    frame: QImage
    skeleton: QImage
    telemetry: Telemetry
