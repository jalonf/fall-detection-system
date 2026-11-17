import logging

from src.workers.base_video_worker import BaseVideoWorker
from src.workers.strategies import strategy_for

logger = logging.getLogger(__name__)


class VideoWorker(BaseVideoWorker):
    """
    It is responsible for initializing the camera to display it on the interface,
    and processing the image to visualize the skeleton.

    The strategy comes from the patient's risk level; with it the camera is opened
    and (in the base class) the model is loaded.
    """

    def __init__(self, camera_index=0, user=None, patient=None, parent=None):
        strategy = strategy_for(patient.risk_level if patient else "LOW")
        super().__init__(
            cap=strategy.configure_camera(camera_index),
            strategy=strategy,
            user=user,
            patient=patient,
            parent=parent,
        )
        self.camera_index = camera_index

    def run(self):
        logger.info(f"Starting camera {self.camera_index} with {self.strategy.name} strategy")

        while self._is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                break

            self._process_frame(frame)

        self._release(self.cap)
