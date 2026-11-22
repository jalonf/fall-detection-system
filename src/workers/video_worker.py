"""Worker that monitors a camera."""

import cv2

from src.workers.base_video_worker import BaseVideoWorker
from src.workers.strategies import MonitoringStrategy, strategy_for


class VideoWorker(BaseVideoWorker):
    """Runs the fall-detection pipeline on a camera.

    The strategy comes from the patient's risk level, unless one is given (an administrator's
    test profile); with it the camera is opened and (in the base class) the model is loaded,
    both inside the worker thread.

    Args:
        camera_index: OpenCV index of the camera.
        user: Who receives the alert e-mails, or None (nothing is sent).
        patient: Whose falls are stored and whose risk level picks the strategy, or None.
        strategy: A strategy to use instead of the patient's (test profiles).
        parent: Parent object.
    """

    def __init__(self, camera_index=0, user=None, patient=None, strategy: MonitoringStrategy | None = None,
                 parent=None):
        super().__init__(user=user, patient=patient, parent=parent)
        self.camera_index = camera_index
        self.source_label = f"camera {camera_index}"
        self._strategy = strategy or strategy_for(patient.risk_level if patient else "LOW")

    def _open_source(self) -> tuple[cv2.VideoCapture, MonitoringStrategy]:
        return self._strategy.configure_camera(self.camera_index), self._strategy
