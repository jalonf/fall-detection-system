import logging

import cv2
from PySide6.QtCore import Signal

from src.workers.base_video_worker import BaseVideoWorker
from src.workers.strategies import HighRiskStrategy, LowRiskStrategy

logger = logging.getLogger(__name__)


class VideoFileWorker(BaseVideoWorker):
    """
    Responsible for loading an uploaded video file, processing frames to extract
    the skeleton, and rendering the fall detection pipeline at natural speed.
    """

    playback_finished = Signal()
    video_quality_detected = Signal(str, int, int)

    def __init__(self, video_path: str, user=None, patient=None, parent=None):
        super().__init__(user=user, patient=patient, parent=parent)
        self.video_path = video_path

    def run(self):
        logger.info(f"Opening video file: {self.video_path}")
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            logger.error(f"Could not open video file: {self.video_path}")
            self._release(cap)
            self.playback_finished.emit()   # lets the controller leave the "monitoring" state
            return

        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        labels = {2160: "4K (UHD)", 1080: "1080p (FHD)", 720: "720p (HD)", 480: "480p (SD)"}
        quality_label = next((lbl for res, lbl in labels.items() if h >= res), f"Low Res ({w}x{h})")
        self.video_quality_detected.emit(quality_label, w, h)

        # Unlike the camera (configured from the patient's risk level), a file comes with
        # its own frame rate, so the model must be the one trained for those FPS.
        self._load_model(LowRiskStrategy() if fps <= 20 else HighRiskStrategy())

        while self._is_running and cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            self._process_frame(frame)

        self._release(cap)
        self.playback_finished.emit()
