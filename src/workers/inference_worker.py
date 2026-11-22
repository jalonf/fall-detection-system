"""Thread that runs the GRU fall model on the latest pose window."""

import logging

import numpy as np
import tensorflow as tf
from PySide6.QtCore import QMutex, QMutexLocker, QThread, QWaitCondition

logger = logging.getLogger(__name__)

class InferenceWorker(QThread):
    """Runs the fall model in its own thread.

    The video thread hands over the newest sequence with `predict` and reads the most
    recent result from `latest` (an `(is_fall, probability)` tuple; assigning it is atomic).

    The thread sleeps on a `QWaitCondition` until `predict` wakes it, so it uses no CPU
    while there is nothing to do. Only the newest sequence is kept: if a new one arrives
    before the previous one was processed, the old one is dropped, because a stale window
    is of no use for a real-time alert.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None
        self.latest: tuple[bool, float] | None = None

        self._mutex = QMutex()
        self._has_work = QWaitCondition()
        self._pending: np.ndarray | None = None
        self._stopping = False

    def load_model(self, model_path: str):
        """Loads the Keras model directly into memory."""
        try:
            self.model = tf.keras.models.load_model(model_path, compile=False)
            logger.info(f"AI model loaded in inference thread: {model_path}")
        except (OSError, ValueError) as e:
            logger.error(f"Failed to load AI model: {e}")

    def predict(self, seq_array: np.ndarray):
        """Receives the sequence from the video thread and wakes the inference thread."""
        with QMutexLocker(self._mutex):
            self._pending = seq_array   # replaces a sequence that was not processed yet
            self._has_work.wakeOne()

    def run(self):
        """Waits for a sequence, runs the model on it, and goes back to sleep."""
        while True:
            with QMutexLocker(self._mutex):
                while self._pending is None and not self._stopping:
                    self._has_work.wait(self._mutex)   # releases the mutex while asleep
                if self._stopping:
                    return
                seq, self._pending = self._pending, None

            if self.model is None:
                continue

            try:
                # Direct tensor call (faster than .predict() for real-time)
                probability = float(self.model(seq, training=False)[0][0])
                self.latest = (probability >= 0.5, probability)
            except (ValueError, TypeError, tf.errors.OpError) as e:
                logger.error(f"Inference error: {e}")

    def stop(self):
        """Wakes the thread so it exits, and waits for it."""
        with QMutexLocker(self._mutex):
            self._stopping = True
            self._has_work.wakeAll()
        self.wait()
