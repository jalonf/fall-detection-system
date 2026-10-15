import logging
import numpy as np
import tensorflow as tf
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)

class InferenceWorker(QThread):
    prediction_ready = Signal(bool, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True
        self.model = None
        self.current_sequence = None

    def load_model(self, model_path: str):
        """Loads the Keras model directly into memory."""
        try:
            self.model = tf.keras.models.load_model(model_path, compile=False)
            logger.info(f"AI model loaded in inference thread: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")

    def predict(self, seq_array: np.ndarray):
        """Receives the sequence from the video thread and queues it for prediction."""
        self.current_sequence = seq_array

    def run(self):
        """Background loop continuously checking for new sequences to process."""
        while self._is_running:
            if self.model is not None and self.current_sequence is not None:
                seq = self.current_sequence
                self.current_sequence = None  # Clear to avoid repeated inference
                
                try:
                    # Direct tensor call (faster than .predict() for real-time)
                    probability = float(self.model(seq, training=False)[0][0])
                    is_fall = probability >= 0.5
                    self.prediction_ready.emit(is_fall, probability)
                except Exception as e:
                    logger.error(f"Inference error: {e}")
            
            # Short sleep to prevent 100% CPU usage
            self.msleep(5)

    def stop(self):
        self._is_running = False
        self.wait()