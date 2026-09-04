import logging
import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
    VisionTaskRunningMode as RunningMode,
)
from mediapipe.tasks.python.vision.pose_landmarker import (
    PoseLandmarker,
    PoseLandmarkerOptions,
)

from src.config import POSE_LANDMARKER_MODEL_PATH
from src.models_ai.dtos import Skeleton

logger = logging.getLogger(__name__)


class MediaPipeExtractor:
    """
    Extracts 3D anatomical landmarks from raw BGR images using the
    MediaPipe Pose Landmarker Tasks API (mediapipe >= 0.10).
    """

    def __init__(
        self, min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5, model_path: str = POSE_LANDMARKER_MODEL_PATH,
    ):
        """
        Args:
            min_detection_confidence: Minimum confidence ([0.0, 1.0]) for person detection
                                      and pose presence scoring.
            min_tracking_confidence:  Minimum confidence ([0.0, 1.0]) for inter-frame tracking.
            model_path:               Absolute path to the .task bundle
                                      (e.g. models/pose_landmarker_full.task).
        """
        logger.info("Initializing MediaPipeExtractor with model path: %s", model_path)
        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=False,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)
        logger.info("MediaPipe PoseLandmarker successfully created.")

    def extract_skeleton(self, frame_bgr: np.ndarray) -> tuple[Skeleton | None, list | None]:
        """
        Processes a BGR image frame and returns a (Skeleton, landmarks_2d) tuple.

        Args:
            frame_bgr (np.ndarray): Raw frame from OpenCV with shape (H, W, 3) in BGR format.

        Returns:
            Tuple:
              - Optional[Skeleton]: 3D world-space skeleton centered at origin, for the AI model.
              - Optional[list]:     Normalized 2D screen-space NormalizedLandmark list, for drawing.
            Both elements are None when no person is detected.
        """
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # RunningMode.VIDEO requires a strictly-increasing timestamp in milliseconds.
        timestamp_ms = int(time.perf_counter() * 1000)
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.pose_world_landmarks:
            logger.debug("No pose detected in the current frame.")
            return None, None

        # 3D world-space landmarks (metres) — used by the AI model.
        landmarks_3d = result.pose_world_landmarks[0]
        coords_3d = np.array(
            [[lm.x, lm.y, lm.z] for lm in landmarks_3d], dtype=np.float32
        )
        visibility = np.array(
            [lm.visibility if lm.visibility is not None else 0.0 for lm in landmarks_3d],
            dtype=np.float32,
        )
        skeleton = Skeleton(
            coordinates_3d=coords_3d, visibility=visibility
        ).normalize_center_of_mass()

        # 2D normalized screen-space landmarks — used for overlay drawing.
        landmarks_2d = result.pose_landmarks[0] if result.pose_landmarks else None

        return skeleton, landmarks_2d

    def release(self) -> None:
        """Safely releases underlying MediaPipe C++ resources to prevent memory leaks."""
        logger.info("Releasing MediaPipe landmarker C++ resources...")
        self._landmarker.close()
        logger.info("MediaPipe resources successfully released.")