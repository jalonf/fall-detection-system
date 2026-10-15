import collections
import logging
import time
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.framework.formats import landmark_pb2
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtGui import QImage

from src.ai.extractor import MediaPipeExtractor
from src.patterns.observer import EventSubject
from src.workers.inference_worker import InferenceWorker

logger = logging.getLogger(__name__)

pb2: Any = landmark_pb2
mp_drawing: Any = mp.solutions.drawing_utils #type: ignore
mp_pose: Any = mp.solutions.pose #type: ignore

class VideoFileWorker(QThread, EventSubject):
    """
    Responsible for loading an uploaded video file, processing frames to extract 
    the skeleton, and rendering the fall detection pipeline at natural speed.
    """
    frame_ready = Signal(QImage)
    fall_detected = Signal(str)
    skeleton_frame_ready = Signal(QImage)
    telemetry_data_ready = Signal(dict)
    playback_finished = Signal()
    video_quality_detected = Signal(str, int, int)

    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)
        EventSubject.__init__(self)

        self.video_path = video_path
        self._is_running = True
        self.extractor = MediaPipeExtractor()
        self.last_known_landmarks = None

        self.seq_len = 30 
        self.sequence_buffer = collections.deque()
        
        # Current prediction state
        self.current_is_fall = False

        # Initialize and connect the inference thread
        self.inference_worker = InferenceWorker()
        self.inference_worker.prediction_ready.connect(self._on_prediction_ready)

    @Slot(bool, float)
    def _on_prediction_ready(self, is_fall, probability):
        """Asynchronously updates the current fall status from the inference thread."""
        self.current_is_fall = is_fall

    def run(self):
        logger.info(f"Opening video file: {self.video_path}")
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            logger.error(f"Could not open video file: {self.video_path}")
            return

        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        labels = {2160: "4K (UHD)", 1080: "1080p (FHD)", 720: "720p (HD)", 480: "480p (SD)"}
        quality_label = next((lbl for res, lbl in labels.items() if h >= res), f"Low Res ({w}x{h})")
        self.video_quality_detected.emit(quality_label, w, h)

        self.seq_len = 15 if fps <= 20 else 30
        model_path = f"assets/fall_gru_{'low_risk_15fps' if self.seq_len == 15 else 'high_risk_30fps'}.keras"
        
        self.sequence_buffer = collections.deque(maxlen=self.seq_len)
        
        # Start inference background thread
        self.inference_worker.load_model(model_path)
        self.inference_worker.start()

        frame_delay = 1.0 / fps if fps > 0 else 1.0 / 30.0

        while self._is_running and cap.isOpened():
            loop_start = time.perf_counter()
            ret, frame = cap.read()
            if not ret or frame is None: break

            start_time = time.perf_counter()
            skeleton, landmarks_2d = self.extractor.extract_skeleton(frame_bgr=frame)

            landmarks_2d = landmarks_2d or self.last_known_landmarks
            self.last_known_landmarks = landmarks_2d

            if landmarks_2d:
                frame = self._censor_face(frame, landmarks_2d)

            if skeleton is not None:
                skel_array = skeleton.to_array().flatten()
                if skel_array.size == 99:
                    self.sequence_buffer.append(skel_array)

            # Send sequence to InferenceWorker asynchronously
            if len(self.sequence_buffer) == self.seq_len:
                seq_array = np.expand_dims(np.array(self.sequence_buffer), axis=0) 
                self.inference_worker.predict(seq_array)

            inference_ms = (time.perf_counter() - start_time) * 1000
            fh, fw, ch = frame.shape
            colour_frame = np.full((fh, fw, ch), (59, 41, 30), dtype=np.uint8)
            telemetry = {'inference_ms': inference_ms, 'centroid_y': None, 'confidence': 0.0}

            if landmarks_2d:
                # Use current state updated by the asynchronous slot
                frame = self._draw_human_bounding_box(frame, landmarks_2d, self.current_is_fall)
                
                proto_lms = pb2.NormalizedLandmarkList(landmark=[
                    pb2.NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility) 
                    for lm in landmarks_2d
                ])

                lm_color = (0, 0, 255) if self.current_is_fall else (0, 255, 127)

                for target_frame, thick, r in [(frame, 2, 2), (colour_frame, 4, 4)]:
                    mp_drawing.draw_landmarks(
                        target_frame, proto_lms, mp_pose.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=thick, circle_radius=r),
                        mp_drawing.DrawingSpec(color=lm_color, thickness=thick)
                    )

                vis = [lm.visibility for lm in landmarks_2d]
                if vis: telemetry['confidence'] = sum(vis) / len(vis)
                
                if len(landmarks_2d) > 24 and landmarks_2d[23].visibility > 0.5 and landmarks_2d[24].visibility > 0.5:
                    telemetry['centroid_y'] = (landmarks_2d[23].y + landmarks_2d[24].y) / 2.0

                xs = [int(lm.x * fw) for lm in landmarks_2d if lm.visibility > 0.3]
                ys = [int(lm.y * fh) for lm in landmarks_2d if lm.visibility > 0.3]
                
                if xs and ys:
                    colour_frame = colour_frame[
                        max(0, min(ys)-60):min(fh, max(ys)+60), 
                        max(0, min(xs)-60):min(fw, max(xs)+60)
                    ]

            self.telemetry_data_ready.emit(telemetry)
            self.frame_ready.emit(QImage(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).data, fw, fh, ch * fw, QImage.Format.Format_RGB888))
            self.skeleton_frame_ready.emit(QImage(cv2.cvtColor(colour_frame, cv2.COLOR_BGR2RGB).data, colour_frame.shape[1], colour_frame.shape[0], 3 * colour_frame.shape[1], QImage.Format.Format_RGB888))

            sleep_time = frame_delay - (time.perf_counter() - loop_start)
            if sleep_time > 0: time.sleep(sleep_time)

        logger.info("Releasing resources...")
        cap.release()
        self.extractor.release()
        self.inference_worker.stop()
        self.playback_finished.emit()

    def _draw_human_bounding_box(self, frame, landmarks_2d, is_fall):
        """Draws the bounding box. Removed the probability percentage per requirements."""
        h, w, _ = frame.shape
        xs = [int(lm.x * w) for lm in landmarks_2d if lm.visibility > 0.3]
        ys = [int(lm.y * h) for lm in landmarks_2d if lm.visibility > 0.3]
        if not xs or not ys: return frame

        x1, y1 = max(0, min(xs) - 25), max(0, min(ys) - 25)
        x2, y2 = min(w, max(xs) + 25), min(h, max(ys) + 25)

        color, label, t = ((0, 0, 255), "FALL ALERT", 3) if is_fall else ((0, 255, 127), "HUMAN", 2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)

        for px, py in [(x1,y1), (x2,y1), (x1,y2), (x2,y2)]:
            cv2.line(frame, (px, py), (px + (20 if px==x1 else -20), py), color, t, cv2.LINE_AA)
            cv2.line(frame, (px, py), (px, py + (20 if py==y1 else -20)), color, t, cv2.LINE_AA)

        tw, th = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, t - 1)[0]
        ty = max(y1 - 6, th + 6)
        cv2.rectangle(frame, (x1, ty - th - 4), (x1 + tw, ty + 2), color, -1)
        cv2.putText(frame, label, (x1, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255) if is_fall else color, t - 1, cv2.LINE_AA)

        return frame

    def _censor_face(self, frame, landmarks_2d):
        h, w, _ = frame.shape
        xs, ys = [int(lm.x * w) for lm in landmarks_2d[:11]], [int(lm.y * h) for lm in landmarks_2d[:11]]
        
        mx, my = int((max(xs) - min(xs)) * 0.4), int((max(ys) - min(ys)) * 0.5)
        x1, y1 = max(0, min(xs) - mx), max(0, min(ys) - int(my * 1.5))
        x2, y2 = min(w, max(xs) + mx), min(h, max(ys) + my)
        
        if x2 > x1 and y2 > y1:
            k = min(x2 - x1, y2 - y1) // 2
            k = k + 1 if k % 2 == 0 else k
            if k > 3: frame[y1:y2, x1:x2] = cv2.GaussianBlur(frame[y1:y2, x1:x2], (k, k), 50)
        return frame

    def stop(self):
        self._is_running = False
        self.wait()