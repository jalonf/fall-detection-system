import logging

import cv2

from src.workers.base_video_worker import BaseVideoWorker
from src.workers.strategies import LowRiskStrategy, MonitoringStrategy

logger = logging.getLogger(__name__)


class VideoWorker(BaseVideoWorker):
    """
    It is responsible for initializing the camera to display it on the interface,
    and processing the image to visualize the skeleton.
    """

    def __init__(self, camera_index=0, strategy: MonitoringStrategy | None = None,
                 user=None, patient=None, parent=None):
        super().__init__(user=user, patient=patient, parent=parent)
        self.camera_index = camera_index
        self._strategy = strategy or LowRiskStrategy()
        self._load_model_for_strategy()

    def set_strategy(self, strategy: MonitoringStrategy):
        """Allows changing the monitoring strategy dynamically."""
        self._strategy = strategy
        self._load_model_for_strategy()
        self.sequence_buffer.clear()

    def _load_model_for_strategy(self):
        risk = self._strategy.get_risk_level().lower()
        self._load_model(30 if "high" in risk else 15)

    def run(self):
        logger.info(f"Starting camera {self.camera_index} with {self._strategy.get_risk_level()} strategy")
        cap = cv2.VideoCapture(self.camera_index)
        self._strategy.apply_config(cap)

        while self._is_running and cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            self._process_frame(frame)

        self._release(cap)
