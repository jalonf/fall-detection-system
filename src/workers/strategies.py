import cv2


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

    def open_camera(self, camera_index: int) -> cv2.VideoCapture:
        """Opens the camera already configured for this strategy."""
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        return cap


class LowRiskStrategy(MonitoringStrategy):
    name = "LOW"
    width, height, fps = 640, 480, 15
    model_path = "assets/fall_gru_low_risk_15fps.keras"


class HighRiskStrategy(MonitoringStrategy):
    name = "HIGH"
    width, height, fps = 1280, 720, 30
    model_path = "assets/fall_gru_high_risk_30fps.keras"


def strategy_for(risk_level: str) -> MonitoringStrategy:
    """HIGH risk gets the high-quality camera; anything else, the low one."""
    return HighRiskStrategy() if risk_level == "HIGH" else LowRiskStrategy()
