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
    # Signals to communicate with PySide6
    frame_ready = Signal(QImage)
    fall_detected = Signal(str)

    def __init__(self, camera_index=0, parent=None):
        """
        Args:
            camera_index (int):               Index of the camera to use for video capture (default: 0).
        
            parent (QObject):                 Parent object for the QThread/QObject.
        """
        super().__init__(parent)
        self.camera_index = camera_index
        self._is_running = True
        
        # Correct instantiation with parentheses
        self.extractor = MediaPipeExtractor()

    def run(self):

        """
            Initializes the camera, processes the image to extract the skeleton and perform inference, 
            and sends the information to the interface via signals."
        """
        cap = cv2.VideoCapture(self.camera_index)
        
        while self._is_running and cap.isOpened():
            start_time = time.perf_counter()
            
            ret, frame = cap.read()
            # Guard against null frames
            if not ret or frame is None:
                break

            # Explicit keyword argument call (frame_bgr=frame)
            skeleton, landmarks_2d = self.extractor.extract_skeleton(frame_bgr=frame)

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

            # Draw landmarks on the frame (Using explicit imports)
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

        # Safely release C++ resources when stopping the thread
        cap.release()
        self.extractor.release()

    def stop(self):
        """
            Close the camera.
        """
        self._is_running = False
        self.wait()