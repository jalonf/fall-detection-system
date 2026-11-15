import logging

import cv2
from PySide6.QtCore import Signal

from src.workers.base_video_worker import BaseVideoWorker
from src.workers.strategies import HighRiskStrategy, LowRiskStrategy

logger = logging.getLogger(__name__)

QUALITY_LABELS = {2160: "4K (UHD)", 1080: "1080p (FHD)", 720: "720p (HD)", 480: "480p (SD)"}


class VideoFileWorker(BaseVideoWorker):
    """
    Responsible for loading an uploaded video file, processing frames to extract
    the skeleton, and rendering the fall detection pipeline at natural speed.

    Everything is set up in the constructor: the file is opened and, since it comes
    with its own frame rate (unlike the camera, which follows the patient's risk
    level), the model trained for those FPS is loaded.
    """

    playback_finished = Signal()
    video_quality_detected = Signal(str, int, int)

    def __init__(self, video_path: str, user=None, patient=None, parent=None):
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        super().__init__(
            cap=cap,
            strategy=LowRiskStrategy() if fps <= 20 else HighRiskStrategy(),
            user=user,
            patient=patient,
            parent=parent,
        )
        self.video_path = video_path
        self.width, self.height = width, height
        self.quality_label = next(
            (label for res, label in QUALITY_LABELS.items() if height >= res),
            f"Low Res ({width}x{height})",
        )

    def run(self):
        logger.info(f"Opening video file: {self.video_path}")

        if not self.cap.isOpened():
            logger.error(f"Could not open video file: {self.video_path}")
            self._release(self.cap)
            self.playback_finished.emit()   # lets the controller leave the "monitoring" state
            return

        # Emitted here and not in the constructor: the signal is connected after creating the worker.
        self.video_quality_detected.emit(self.quality_label, self.width, self.height)

        while self._is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                break

            self._process_frame(frame)

        self._release(self.cap)
        self.playback_finished.emit()
