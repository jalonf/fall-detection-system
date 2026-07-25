from typing import Optional
import cv2
import numpy as np
import mediapipe as mp
from src.models_ai.dtos import Skeleton


class MediaPipeExtractor:
    """
    Extracts 3D anatomical landmarks from raw BGR images using MediaPipe Pose.
    """
    def __init__(self,min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5, model_complexity: int = 1):
        """
        Args:
            min_detection_confidence: Minimum confidence ([0.0, 1.0]) for person detection.
            min_tracking_confidence: Minimum confidence ([0.0, 1.0]) for landmark tracking.
            model_complexity: 0=Lite (fastest), 1=Full (balanced), 2=Heavy.
        """
        self.mp_pose = mp.solutions.pose  # type: ignore
        self.pose_engine = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def extract_skeleton(self,frame_bgr: np.ndarray) -> Optional[Skeleton]:
        """
        Processes a BGR image frame and returns a normalized Skeleton DTO if a person is detected.

        Args:
            frame_bgr (np.ndarray): Raw frame from OpenCV with shape (H, W, 3) in BGR format.

        Returns:
            Optional[Skeleton]: Standardized Skeleton object centered at origin (0,0,0),
                                or None if no human pose is detected.
        """

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False

        result = self.pose_engine.process(frame_rgb)

        if (result == None):
            return None
        else:
            landmarks = result.pose_world_landmarks.landmark

            coords_3d = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
            visibility = np.array([lm.visibility for lm in landmarks], dtype=np.float32)

            skeleton = Skeleton(coords_3d,visibility).normalize_center_of_mass()

            return skeleton

    def release(self) -> None:
        """Safely releases underlying MediaPipe C++ resources."""
        self.pose_engine.close()