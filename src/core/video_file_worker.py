import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.framework.formats import landmark_pb2  # type: ignore
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

mp_drawing = mp.solutions.drawing_utils # type: ignore
mp_pose = mp.solutions.pose # type: ignore

from src.models_ai.dtos import InferenceResult
from src.models_ai.extractor import MediaPipeExtractor


class VideoFileWorker(QThread):
    """
    Responsible for loading an uploaded video file, processing frames to extract 
    the skeleton, and rendering the fall detection pipeline at natural speed.
    """
    frame_ready = Signal(QImage)
    fall_detected = Signal(str)
    skeleton_frame_ready = Signal(QImage)
    telemetry_data_ready = Signal(dict)
    playback_finished = Signal()

    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self._is_running = True
        self.extractor = MediaPipeExtractor()
        self.last_known_landmarks = None

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print(f"[Worker Error] Could not open video file: {self.video_path}")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / fps if fps > 0 else 1.0 / 30.0

        while self._is_running and cap.isOpened():
            loop_start = time.perf_counter()
            
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            start_time = time.perf_counter()

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

            h, w, ch = frame.shape
            colour_frame = np.full((h, w, ch), (42, 23, 15), dtype=np.uint8)
            
            telemetry_data = {
                'inference_ms': inference_time,
                'centroid_y': None,
                'confidence': 0.0
            }

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

                mp_drawing.draw_landmarks(
                    colour_frame,
                    proto_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=4, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(0, 255, 127), thickness=4)
                )

                visibilities = [lm.visibility for lm in result.pose_landmarks]
                if visibilities:
                    telemetry_data['confidence'] = sum(visibilities) / len(visibilities)
                
                if len(result.pose_landmarks) > 24:
                    l_hip = result.pose_landmarks[23]
                    r_hip = result.pose_landmarks[24]
                    if l_hip.visibility > 0.5 and r_hip.visibility > 0.5:
                        telemetry_data['centroid_y'] = (l_hip.y + r_hip.y) / 2.0

                x_coords = [int(lm.x * w) for lm in result.pose_landmarks if lm.visibility > 0.3]
                y_coords = [int(lm.y * h) for lm in result.pose_landmarks if lm.visibility > 0.3]
                
                if x_coords and y_coords:
                    pad = 60
                    x1 = max(0, min(x_coords) - pad)
                    y1 = max(0, min(y_coords) - pad)
                    x2 = min(w, max(x_coords) + pad)
                    y2 = min(h, max(y_coords) + pad)
                    
                    colour_frame = colour_frame[y1:y2, x1:x2]

            self.telemetry_data_ready.emit(telemetry_data)

            bytes_per_line = ch * w
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            black_rgb = cv2.cvtColor(colour_frame, cv2.COLOR_BGR2RGB)
            bh, bw = black_rgb.shape[:2]
            b_bytes_per_line = 3 * bw
            skeleton_qimg = QImage(black_rgb.data, bw, bh, b_bytes_per_line, QImage.Format.Format_RGB888)

            self.skeleton_frame_ready.emit(skeleton_qimg)
            self.frame_ready.emit(qimg)

            elapsed = time.perf_counter() - loop_start
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        cap.release()
        self.extractor.release()
        self.playback_finished.emit()

    def _draw_human_bounding_box(self, frame, landmarks_2d):
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
        (_text_width, text_height), _baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
        
        label_y = max(y1 - 6, text_height + 6)
        cv2.putText(frame, label, (x1, label_y), font, font_scale, box_color, font_thickness, cv2.LINE_AA)

        return frame

    def _censor_face(self, frame, landmarks_2d):
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
        self._is_running = False
        self.wait()