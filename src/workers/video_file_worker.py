import logging
import os

import cv2
from PySide6.QtCore import Signal

from src.workers.base_video_worker import BaseVideoWorker
from src.workers.strategies import HighRiskStrategy, LowRiskStrategy, MonitoringStrategy

logger = logging.getLogger(__name__)

QUALITY_LABELS = {2160: "4K (UHD)", 1080: "1080p (FHD)", 720: "720p (HD)", 480: "480p (SD)"}


class VideoFileWorker(BaseVideoWorker):
    """
    Responsible for loading an uploaded video file, processing frames to extract
    the skeleton, and running the fall detection pipeline on it.

    The file is opened in the worker thread. Since it comes with its own frame rate
    (unlike the camera, which follows the patient's risk level), the model trained
    for those FPS is loaded. The thread ends on its own when the file runs out.
    """

    video_quality_detected = Signal(str, int, int)

    def __init__(self, video_path: str, user=None, patient=None, parent=None):
        super().__init__(user=user, patient=patient, parent=parent)
        self.video_path = video_path
        self.source_label = f"video file {os.path.basename(video_path)}"

    def _open_source(self) -> tuple[cv2.VideoCapture, MonitoringStrategy]:
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        return cap, LowRiskStrategy() if fps <= 20 else HighRiskStrategy()

    def _on_source_opened(self, cap: cv2.VideoCapture) -> None:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        quality_label = next(
            (label for res, label in QUALITY_LABELS.items() if height >= res),
            f"Low Res ({width}x{height})",
        )
        logger.info("Video file quality: %s", quality_label)
        self.video_quality_detected.emit(quality_label, width, height)
