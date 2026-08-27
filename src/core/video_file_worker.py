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

class VideoFileWorker(QThread):
    """
    Responsible for loading an uploaded video file, processing frames to extract 
    the skeleton, and rendering the fall detection pipeline at natural speed.
    """
    # Signals to communicate with PySide6
    frame_ready = Signal(QImage)
    fall_detected = Signal(str)
    playback_finished = Signal()

    def __init__(self, video_path: str, parent=None):
        """
        Args:
            video_path (str): File path of the uploaded video to process.
            parent (QObject): Parent object for the QThread.
        """
        super().__init__(parent)
        self.video_path = video_path
        self._is_running = True
        
        self.extractor = MediaPipeExtractor()

    def run(self):
        """
        Initializes the video capture from file, processes frames synchronously, 
        and streams the annotated frames via signals.
        """
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print(f"[Worker Error] Could not open video file: {self.video_path}")
            return

        # Extract original video FPS to maintain natural playback speed
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / fps if fps > 0 else 1.0 / 30.0

        while self._is_running and cap.isOpened():
            loop_start = time.perf_counter()
            
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            start_time = time.perf_counter()

            # Explicit keyword argument call (frame_bgr=frame)
            skeleton, landmarks_2d = self.extractor.extract_skeleton(frame_bgr=frame)

            # Censor the face
            if landmarks_2d:
                frame = self._censor_face(frame, landmarks_2d)

            is_fall = False
            probability = 0.0
            inference_time = (time.perf_counter() - start_time) * 1000
            
            # Package everything into the immutable DTO
            result = InferenceResult(
                skeleton=skeleton,
                pose_landmarks=landmarks_2d,
                is_fall=is_fall,
                fall_probability=probability,
                inference_time_ms=inference_time
            )

            # Draw landmarks on the frame
            if result.pose_landmarks:
                proto_landmarks = landmark_pb2.NormalizedLandmarkList() # type: ignore
                proto_landmarks.landmark.extend([
                    landmark_pb2.NormalizedLandmark( # type: ignore
                        x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility
                    ) for lm in result.pose_landmarks
                ])
                
                mp_drawing.draw_landmarks(
                    frame,
                    proto_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

            # Convert to QImage for the graphical interface
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            
            qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Send the ready frame to the view
            self.frame_ready.emit(qimg)

            # Synchronize video playback timing to match natural FPS
            elapsed = time.perf_counter() - loop_start
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        # Safely release C++ resources when the video ends or stops
        cap.release()
        self.extractor.release()
        self.playback_finished.emit()

    def _censor_face(self, frame, landmarks_2d):
        """Calculates face region using MediaPipe landmarks and applies Gaussian blur."""
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
        """Stops video thread processing gracefully."""
        self._is_running = False
        self.wait()