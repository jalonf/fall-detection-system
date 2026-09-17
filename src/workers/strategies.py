from abc import ABC, abstractmethod

import cv2


class MonitoringStrategy(ABC):
    @abstractmethod
    def apply_config(self, cap: cv2.VideoCapture) -> None:
        """Applies the corresponding resolution and FPS to the camera."""

    @abstractmethod
    def get_risk_level(self) -> str:
        pass


class LowRiskStrategy(MonitoringStrategy):
    def apply_config(self, cap: cv2.VideoCapture) -> None:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)

    def get_risk_level(self) -> str:
        return "LOW"


class HighRiskStrategy(MonitoringStrategy):
    def apply_config(self, cap: cv2.VideoCapture) -> None:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)

    def get_risk_level(self) -> str:
        return "HIGH"