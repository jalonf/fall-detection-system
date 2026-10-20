import logging
import os
import time

import cv2
import mediapipe as mp
import numpy as np
from dotenv import load_dotenv
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
    VisionTaskRunningMode as RunningMode,
)
from mediapipe.tasks.python.vision.pose_landmarker import (
    PoseLandmarker,
    PoseLandmarkerOptions,
)

load_dotenv()

logger = logging.getLogger(__name__)

LEFT_HIP, RIGHT_HIP = 23, 24


def center_on_hips(coords: np.ndarray) -> np.ndarray:
    """Moves the pose so the midpoint of the hips is the origin (where the person stands no longer matters)."""
    return coords - (coords[LEFT_HIP] + coords[RIGHT_HIP]) / 2


class MediaPipeExtractor:
    """
    Robust coordinate extractor resistant to FPS fluctuations.
    Uses real monotonic time to ensure video stream temporal continuity in MediaPipe.
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.6,
        model_path: str = os.getenv("POSE_LANDMARKER_MODEL_PATH", "assets/pose_landmarker_full.task"),
    ):
        logger.info("Initializing robust MediaPipeExtractor with model path: %s", model_path)
        
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
        
        # Strictly increasing timestamp control independent of FPS
        self._last_timestamp_ms = 0
        logger.info("MediaPipe PoseLandmarker successfully initialized.")

    def extract_pose(self, frame_bgr: np.ndarray) -> tuple[np.ndarray | None, list | None]:
        """
        Processes a BGR frame, calculating a safe monotonic timestamp resistant to frame drops or FPS drops.

        Args:
            frame_bgr (np.ndarray): Raw OpenCV frame (H, W, 3) in BGR format.

        Returns:
            The model input, 33x3 coordinates in meters centred on the hips, and the
            2D screen-space landmarks used for drawing. Both are None when no person is found.
        """
        # 1. Ensure memory continuity and color conversion
        frame_rgb = np.ascontiguousarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # 2. Generate a secure, strictly increasing timestamp resilient to variable FPS
        current_ms = int(time.monotonic() * 1000)
        if current_ms <= self._last_timestamp_ms:
            current_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = current_ms

        # 3. MediaPipe inference
        result = self._landmarker.detect_for_video(mp_image, current_ms)

        if not result.pose_world_landmarks or not result.pose_landmarks:
            logger.debug("No pose detected in the current frame.")
            return None, None

        # 4. 3D world landmarks (in meters), centred on the hips: the model input
        landmarks_3d = result.pose_world_landmarks[0]
        pose = center_on_hips(np.array([(lm.x, lm.y, lm.z) for lm in landmarks_3d], dtype=np.float32))

        # 5. Normalized 2D screen-space landmarks for drawing
        landmarks_2d = result.pose_landmarks[0]

        return pose, landmarks_2d

    def release(self) -> None:
        """Safely releases underlying C++ native resources."""
        logger.info("Releasing MediaPipe landmarker C++ resources...")
        self._landmarker.close()
        logger.info("MediaPipe resources successfully released.")