import cv2

from src.paths import FALL_MODELS_DIR


class MonitoringStrategy:
    """
    How to monitor a patient: camera resolution and FPS, and the model trained
    for those FPS. Each subclass only fills in the values.
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
    name = "LOW"
    width, height, fps = 640, 480, 15
    model_path = str(FALL_MODELS_DIR / "fall_gru_low_risk_15fps.keras")


class MediumRiskStrategy(MonitoringStrategy):
    name = "MEDIUM"
    width, height, fps = 1280, 720, 15
    model_path = str(FALL_MODELS_DIR / "fall_gru_low_risk_15fps.keras")


class HighRiskStrategy(MonitoringStrategy):
    name = "HIGH"
    width, height, fps = 1280, 720, 30
    model_path = str(FALL_MODELS_DIR / "fall_gru_high_risk_30fps.keras")


_STRATEGIES: dict[str, type[MonitoringStrategy]] = {
    "LOW": LowRiskStrategy,
    "MEDIUM": MediumRiskStrategy,
    "HIGH": HighRiskStrategy,
}


def strategy_for(risk_level: str) -> MonitoringStrategy:
    """Returns the monitoring strategy matching the risk level (defaults to LOW)."""
    strategy_cls = _STRATEGIES.get(risk_level.upper(), LowRiskStrategy)
    return strategy_cls()