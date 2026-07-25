from abc import ABC, abstractmethod
import numpy as np
from src.models_ai.dtos import InferenceResult


class BaseView(ABC):
    """
    Abstract interface for rendering frame data and AI inference results.
    """

    @abstractmethod
    def render(self,frame_bgr: np.ndarray, resullt: InferenceResult) -> None:
        """
        Renders the processed frame and overlays visual indicators.

        Args:
            frame_bgr (np.ndarray): The raw video frame.
            result (InferenceResult): Immutable DTO containing AI predictions and skeleton data.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Safely closes display windows and releases presentation resources."""
        pass