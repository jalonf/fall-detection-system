import time
import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
import mediapipe as mp

from mediapipe.framework.formats import landmark_pb2 # type: ignore
mp_drawing = mp.solutions.drawing_utils # type: ignore
mp_pose = mp.solutions.pose # type: ignore

from src.models_ai.extractor import MediaPipeExtractor 
from src.models_ai.dtos import InferenceResult

class VideoWorker(QThread):
    """
    It is responsible for initializing the camera to display it on the interface, 
    and processing the image to visualize the skeleton.
    """
    frame_ready = Signal(QImage)
    fall_detected = Signal(str)

    def __init__(self, camera_index=0, parent=None):
        """
        Args:
            camera_index (int): Index of the camera to use for video capture (default: 0).
            parent (QObject): Parent object for the QThread/QObject.
        """
        super().__init__(parent)
        self.camera_index = camera_index
        self._is_running = True
        self.extractor = MediaPipeExtractor()
        self.last_known_landmarks = None

    def run(self):
        """
        Initializes the camera, processes the image to extract the skeleton and perform inference, 
        and sends the information to the interface via signals.
        """
        cap = cv2.VideoCapture(self.camera_index)
        
        while self._is_running and cap.isOpened():
            start_time = time.perf_counter()
            
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            skeleton, landmarks_2d = self.extractor.extract_skeleton(frame_bgr=frame)

            if landmarks_2d:
                self.last_known_landmarks = landmarks_2d
            else:
                landmarks_2d = self.last_known_landmarks

            if landmarks_2d:
                frame = self._censor_face(frame, landmarks_2d)

            is_fall = False
            probability = 0.0
            inference_time = (time.perf_counter() - start_time) * 1000
            
            result = InferenceResult(
                skeleton=skeleton,
                pose_landmarks=landmarks_2d,
                is_fall=is_fall,
                fall_probability=probability,
                inference_time_ms=inference_time
            )

            if result.pose_landmarks:
                frame = self._draw_human_bounding_box(frame, result.pose_landmarks)

                proto_landmarks = landmark_pb2.NormalizedLandmarkList() # type: ignore
                proto_landmarks.landmark.extend([
                    landmark_pb2.NormalizedLandmark( # type: ignore
                        x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility
                    ) for lm in result.pose_landmarks
                ])
                
                mp_drawing.draw_landmarks(
                    frame,
                    proto_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(0, 255, 127), thickness=2)
                )

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            
            qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            self.frame_ready.emit(qimg)

        cap.release()
        self.extractor.release()

    def _draw_human_bounding_box(self, frame, landmarks_2d):
        """Calculates skeleton bounds and draws a modern, attractive bounding box with label."""
        if not landmarks_2d:
            return frame

        h, w, _ = frame.shape
        
        x_coords = [int(lm.x * w) for lm in landmarks_2d if lm.visibility > 0.3]
        y_coords = [int(lm.y * h) for lm in landmarks_2d if lm.visibility > 0.3]
        
        if not x_coords or not y_coords:
            return frame

        padding = 25
        x1 = max(0, min(x_coords) - padding)
        y1 = max(0, min(y_coords) - padding)
        x2 = min(w, max(x_coords) + padding)
        y2 = min(h, max(y_coords) + padding)

        box_color = (0, 255, 127) 
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 1, cv2.LINE_AA)

        length = 20
        thickness = 2
        
        cv2.line(frame, (x1, y1), (x1 + length, y1), box_color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x1, y1), (x1, y1 + length), box_color, thickness, cv2.LINE_AA)
        
        cv2.line(frame, (x2, y1), (x2 - length, y1), box_color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x2, y1), (x2, y1 + length), box_color, thickness, cv2.LINE_AA)
        
        cv2.line(frame, (x1, y2), (x1 + length, y2), box_color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x1, y2), (x1, y2 - length), box_color, thickness, cv2.LINE_AA)
        
        cv2.line(frame, (x2, y2), (x2 - length, y2), box_color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x2, y2), (x2, y2 - length), box_color, thickness, cv2.LINE_AA)

        label = "HUMAN"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
        
        label_y = max(y1 - 6, text_height + 6)
        cv2.putText(frame, label, (x1, label_y), font, font_scale, box_color, font_thickness, cv2.LINE_AA)

        return frame

    def _censor_face(self, frame, landmarks_2d):
        """
        Calculates the face area using MediaPipe landmarks and applies 
        a Gaussian blur to censor it.
        """
        if not landmarks_2d:
            return frame

        h, w, _ = frame.shape
        face_landmarks = landmarks_2d[:11] 
        
        x_coords = [int(lm.x * w) for lm in face_landmarks]
        y_coords = [int(lm.y * h) for lm in face_landmarks]
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        face_width = x_max - x_min
        face_height = y_max - y_min
        
        margin_x = int(face_width * 0.4)
        margin_y = int(face_height * 0.5)
        
        x1 = max(0, x_min - margin_x)
        y1 = max(0, y_min - int(margin_y * 1.5))
        x2 = min(w, x_max + margin_x)
        y2 = min(h, y_max + margin_y)
        
        if x2 > x1 and y2 > y1:
            face_roi = frame[y1:y2, x1:x2]
            kernel_size = min(x2 - x1, y2 - y1) // 2
            kernel_size = kernel_size if kernel_size % 2 != 0 else kernel_size + 1
            
            if kernel_size > 3:
                blurred_face = cv2.GaussianBlur(face_roi, (kernel_size, kernel_size), 50)
                frame[y1:y2, x1:x2] = blurred_face
                
        return frame

    def stop(self):
        """Close the camera."""
        self._is_running = False
        self.wait()