"""Image helpers for the video thread: drawing, face blur and Qt conversion.

All the functions work on BGR NumPy frames (OpenCV format). The drawing ones modify the
frame they receive instead of returning a copy.
"""

import logging
from typing import Any

import cv2
import numpy as np
from mediapipe.framework.formats import landmark_pb2
from mediapipe.python.solutions import drawing_utils, pose
from PySide6.QtGui import QImage

logger = logging.getLogger(__name__)

pb2: Any = landmark_pb2
mp_drawing: Any = drawing_utils
mp_pose: Any = pose

# BGR colours
FALL_COLOR = (0, 0, 255)
OK_COLOR = (0, 255, 127)
WHITE = (255, 255, 255)

MIN_VISIBILITY = 0.3   # landmarks less visible than this are ignored when measuring the person
FACE_LANDMARKS = 11    # MediaPipe landmarks 0-10: nose, eyes, ears and mouth


def person_bounds(landmarks, width: int, height: int, margin: int = 0):
    """Box (x1, y1, x2, y2) around the visible landmarks plus `margin` pixels, or None."""
    visible = [lm for lm in landmarks if lm.visibility > MIN_VISIBILITY]
    if not visible:
        return None

    xs = [int(lm.x * width) for lm in visible]
    ys = [int(lm.y * height) for lm in visible]
    return (
        max(0, min(xs) - margin),
        max(0, min(ys) - margin),
        min(width, max(xs) + margin),
        min(height, max(ys) + margin),
    )


def censor_face(frame, landmarks) -> None:
    """Blurs the face area so neither the screen nor the stored capture shows it."""
    height, width, _ = frame.shape
    xs = [int(lm.x * width) for lm in landmarks[:FACE_LANDMARKS]]
    ys = [int(lm.y * height) for lm in landmarks[:FACE_LANDMARKS]]

    # Face box plus some margin; more room above, to cover the forehead and hair.
    margin_x = int((max(xs) - min(xs)) * 0.4)
    margin_y = int((max(ys) - min(ys)) * 0.5)
    x1, x2 = max(0, min(xs) - margin_x), min(width, max(xs) + margin_x)
    y1, y2 = max(0, min(ys) - int(margin_y * 1.5)), min(height, max(ys) + margin_y)
    if x2 <= x1 or y2 <= y1:
        return

    kernel = (min(x2 - x1, y2 - y1) // 2) | 1   # GaussianBlur needs an odd kernel size
    if kernel > 3:
        frame[y1:y2, x1:x2] = cv2.GaussianBlur(frame[y1:y2, x1:x2], (kernel, kernel), 50)


def draw_person_box(frame, box, is_fall: bool) -> None:
    """Thin rectangle with thick corners and a label: green 'HUMAN', red 'FALL ALERT'."""
    x1, y1, x2, y2 = box
    color, label, thickness = (FALL_COLOR, "FALL ALERT", 3) if is_fall else (OK_COLOR, "HUMAN", 2)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)

    for x, dx in ((x1, 20), (x2, -20)):
        for y, dy in ((y1, 20), (y2, -20)):
            cv2.line(frame, (x, y), (x + dx, y), color, thickness, cv2.LINE_AA)
            cv2.line(frame, (x, y), (x, y + dy), color, thickness, cv2.LINE_AA)

    # Label on a filled tag above the box (kept inside the frame).
    text_w, text_h = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, thickness - 1)[0]
    text_y = max(y1 - 6, text_h + 6)
    cv2.rectangle(frame, (x1, text_y - text_h - 4), (x1 + text_w, text_y + 2), color, -1)
    cv2.putText(
        frame, label, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
        WHITE if is_fall else color, thickness - 1, cv2.LINE_AA,
    )


def draw_skeleton(image, landmarks, color, size: int) -> None:
    """Draws the pose connections in white and the joints in `color` (`size` = line/dot size)."""
    landmark_list = pb2.NormalizedLandmarkList(landmark=[
        pb2.NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility)
        for lm in landmarks
    ])
    mp_drawing.draw_landmarks(
        image, landmark_list, mp_pose.POSE_CONNECTIONS,
        mp_drawing.DrawingSpec(color=WHITE, thickness=size, circle_radius=size),
        mp_drawing.DrawingSpec(color=color, thickness=size),
    )


def to_qimage(bgr) -> QImage:
    """Converts a BGR array to a QImage.

    Qt reads BGR directly (`Format_BGR888`), so there is no colour conversion. `.copy()`
    detaches the image from the NumPy buffer, which is freed as soon as the video thread moves on
    to the next frame.

    Args:
        bgr: Image (H, W, 3), possibly a non-contiguous crop.

    Returns:
        An independent QImage.
    """
    bgr = np.ascontiguousarray(bgr)   # a crop is a view with gaps between rows
    height, width, _ = bgr.shape
    return QImage(bgr.data, width, height, bgr.strides[0], QImage.Format.Format_BGR888).copy()


