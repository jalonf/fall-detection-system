import cv2

from src.workers.base_video_worker import BaseVideoWorker
from src.workers.strategies import MonitoringStrategy, strategy_for


class VideoWorker(BaseVideoWorker):
    """
    It is responsible for initializing the camera to display it on the interface,
    and processing the image to visualize the skeleton.

    The strategy comes from the patient's risk level; with it the camera is opened
    and (in the base class) the model is loaded, both inside the worker thread.
    """

    def __init__(self, camera_index=0, user=None, patient=None, parent=None):
        super().__init__(user=user, patient=patient, parent=parent)
        self.camera_index = camera_index
        self.source_label = f"camera {camera_index}"
        self._strategy = strategy_for(patient.risk_level if patient else "LOW")

    def _open_source(self) -> tuple[cv2.VideoCapture, MonitoringStrategy]:
        return self._strategy.configure_camera(self.camera_index), self._strategy
