"""Monitoring strategies (Strategy pattern): camera settings and fall model per risk level."""

import cv2

from src.paths import FALL_MODELS_DIR


class MonitoringStrategy:
    """How to monitor a patient: camera resolution and FPS, and the model trained for those FPS.

    Each subclass only fills in the values.

    Attributes:
        name: Risk level ("LOW", "MEDIUM" or "HIGH").
        width: Camera width in pixels.
        height: Camera height in pixels.
        fps: Frames per second; also the model's window (one second of frames).
        model_path: The `.keras` model trained for those FPS.
    """

    name: str
    width: int
    height: int
    fps: int
    model_path: str

    def configure_camera(self, camera_index: int) -> cv2.VideoCapture:
        """Opens the camera already configured for this strategy."""
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        return cap


class LowRiskStrategy(MonitoringStrategy):
    """LOW risk: 640 x 480 at 15 FPS, with the 15-frame model."""
    name = "LOW"
    width, height, fps = 640, 480, 15
    model_path = str(FALL_MODELS_DIR / "fall_gru_low_risk_15fps.keras")


class MediumRiskStrategy(MonitoringStrategy):
    """MEDIUM risk: 1280 x 720 at 15 FPS, with the 15-frame model."""
    name = "MEDIUM"
    width, height, fps = 1280, 720, 15
    model_path = str(FALL_MODELS_DIR / "fall_gru_low_risk_15fps.keras")


class HighRiskStrategy(MonitoringStrategy):
    """HIGH risk: 1280 x 720 at 30 FPS, with the 30-frame model."""
    name = "HIGH"
    width, height, fps = 1280, 720, 30
    model_path = str(FALL_MODELS_DIR / "fall_gru_high_risk_30fps.keras")


_STRATEGIES: dict[str, type[MonitoringStrategy]] = {
    "LOW": LowRiskStrategy,
    "MEDIUM": MediumRiskStrategy,
    "HIGH": HighRiskStrategy,
}
RISK_LEVELS = tuple(_STRATEGIES)   # ("LOW", "MEDIUM", "HIGH")


def strategy_for(risk_level: str) -> MonitoringStrategy:
    """Returns the monitoring strategy matching the risk level (defaults to LOW)."""
    strategy_cls = _STRATEGIES.get(risk_level.upper(), LowRiskStrategy)
    return strategy_cls()