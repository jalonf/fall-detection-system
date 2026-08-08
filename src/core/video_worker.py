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
            if not ret or frame is None:
                break

            # Explicit keyword argument call (frame_bgr=frame)
            skeleton, landmarks_2d = self.extractor.extract_skeleton(frame_bgr=frame)


            # Censor the face
            if landmarks_2d:
                frame = self._censor_face(frame,landmarks_2d)

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

    def _censor_face(self, frame, landmarks_2d):
        """
        Calculates the face area using MediaPipe landmarks and applies 
        a Gaussian blur to censor it.
        """
        # If there are no detections or the array is empty, return the untouched frame
        if not landmarks_2d:
            return frame

        h, w, _ = frame.shape
        
        # Points 0 to 10 in MediaPipe Pose correspond to the head/face
        face_landmarks = landmarks_2d[:11] 
        
        # Extract normalized coordinates and convert them to pixels
        x_coords = [int(lm.x * w) for lm in face_landmarks]
        y_coords = [int(lm.y * h) for lm in face_landmarks]
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Add padding since the landmarks do not cover the forehead or hair
        face_width = x_max - x_min
        face_height = y_max - y_min
        
        margin_x = int(face_width * 0.4)
        margin_y = int(face_height * 0.5)
        
        # Calculate final coordinates ensuring they don't go out of image bounds
        x1 = max(0, x_min - margin_x)
        y1 = max(0, y_min - int(margin_y * 1.5)) # Extra margin on top for the forehead
        x2 = min(w, x_max + margin_x)
        y2 = min(h, y_max + margin_y)
        
        # Validate that the crop area is logical (greater than zero)
        if x2 > x1 and y2 > y1:
            # Extract the Region of Interest (ROI)
            face_roi = frame[y1:y2, x1:x2]
            
            # Calculate a dynamic kernel size based on the face size
            kernel_size = min(x2 - x1, y2 - y1) // 2
            kernel_size = kernel_size if kernel_size % 2 != 0 else kernel_size + 1
            
            if kernel_size > 3:
                # Apply heavy blur
                blurred_face = cv2.GaussianBlur(face_roi, (kernel_size, kernel_size), 50)
                
                # Overlay the blurred patch onto the original frame
                frame[y1:y2, x1:x2] = blurred_face
                
        return frame

    def stop(self):
        """
            Close the camera.
        """
        self._is_running = False
        self.wait()