"""Fall detection thread: builds the one-second pose window and runs the GRU on it."""

import collections
import logging
import queue
import threading
from collections.abc import Callable

import numpy as np
import tensorflow as tf
from PySide6.QtCore import QThread, Signal

from src.ai.fall_model import POSE_VALUES, FallModelError, load_fall_model
from src.dtos.fall_prediction import FallPrediction

logger = logging.getLogger(__name__)

THREAD_NAME = "fall-detection-thread"
FALL_ON = 0.6                 # a fall starts when the probability reaches this...
FALL_OFF = 0.4                # ...and ends when it drops below this (hysteresis)
MAX_CONSECUTIVE_ERRORS = 10   # inference failures in a row before the model is given up as broken
_STOP = object()              # put in the queue to end the thread


class FallDetectionThread(QThread):
    """Fall detection thread: detects falls from the poses the `VideoThread` sends.

    It is the second of the three threads of a monitoring session. The controller creates, starts
    and stops it, and connects to its `fall_detected` signal; the `VideoThread` hands it a pose per
    frame. When a fall starts, this thread emits `fall_detected` and the controller hands the fall
    to the `AlertThread`.

    The model is loaded at the start of `run`, in this thread, so the window never freezes and it
    loads at the same time as MediaPipe (in the video thread). `wait_until_ready` lets the video
    thread wait for it before its first frame. If it cannot be loaded, `failed` is set.

    The video thread calls `push(timestamp_ms, pose)` once per frame; it never waits. The poses
    travel through a `queue.Queue` (which has its own lock and wake-up), so no pose is lost.
    Every time this thread wakes up it takes all the poses waiting, adds them to the window and
    runs the model once, on the newest window: if it ever falls behind, it catches up instead of
    lagging.

    The window always covers one second of real time: poses are sampled by their timestamp at
    the model's frame rate, so a camera that delivers more frames than asked does not squeeze
    the window (as in training, where the videos were subsampled to 15 or 30 FPS). While nobody
    is seen, the last pose is repeated, also as in training.

    Hysteresis decides what a fall is: it starts when the probability reaches `FALL_ON` and ends
    when it drops below `FALL_OFF`, so a probability hovering around 0.5 is one fall, not many.
    `fall_detected` is emitted (from this thread) only when a fall starts.

    `latest` (a FallPrediction: the current state and the last probability) and `failed` (the
    model did not load or keeps failing) are written only by this thread and read by the video
    thread; replacing a reference is atomic.

    Signals:
        fall_detected(float): A fall has just started, with the model's probability (0-1).

    Args:
        model_path: The `.keras` model trained for this frame rate.
        fps: Frame rate the model was trained for; it is also the window length (one second).
        parent: Parent object.
    """

    fall_detected = Signal(float)        # a fall has just started: probability (0-1)

    def __init__(self, model_path: str, fps: int, parent=None):
        super().__init__(parent)
        self.setObjectName(THREAD_NAME)
        self.latest: FallPrediction | None = None
        self.failed = False

        self._model_path = model_path
        self._predict: Callable[[np.ndarray], float] | None = None   # loaded at the start of `run`
        self._ready = threading.Event()                 # set once the model is loaded (or failed to)
        self._poses: queue.Queue = queue.Queue()       # (timestamp_ms, pose) from the video thread

        # Only this thread touches these once it runs.
        self._seq_len = fps                                               # poses per window (one second)
        self._window: collections.deque = collections.deque(maxlen=fps)   # the last second of poses
        self._period_ms = 1000 / fps
        self._tolerance_ms = self._period_ms / 4       # camera jitter accepted around each sample
        self._next_sample_ms: float | None = None
        self._last_pose: np.ndarray | None = None

    # ------------------------------------------------------------------ video thread
    def push(self, timestamp_ms: float, pose: np.ndarray | None) -> None:
        """Hands over the pose of one frame (None when nobody was found). Never blocks.

        Args:
            timestamp_ms: When the frame was taken, in milliseconds (any origin, increasing).
            pose: The model input of the frame (33 x 3 values), or None.
        """
        self._poses.put((timestamp_ms, pose))

    def wait_until_ready(self) -> None:
        """Blocks until the model is loaded, or failed to load (then `failed` is True)."""
        self._ready.wait()

    # ------------------------------------------------------------------ controller
    def stop(self) -> None:
        """Ends the thread and waits for it."""
        self._poses.put(_STOP)
        self.wait()

    # ------------------------------------------------------------------ fall detection thread
    def run(self):
        """Loads the model, then waits for poses, runs the model and decides whether a fall started."""
        threading.current_thread().name = THREAD_NAME   # shown in the log as the thread name

        # 0. Load the model (the slow part of starting).
        try:
            self._predict = load_fall_model(self._model_path, seq_len=self._seq_len)
        except FallModelError:
            logger.exception("The fall model could not be loaded")
            self.failed = True                           # the video thread stops the monitoring
            return
        finally:
            self._ready.set()                            # the video thread can go on either way
        predict = self._predict

        errors = 0
        while True:
            # 1. Sleep until the video thread sends something, then take everything waiting.
            items = [self._poses.get()]
            while not self._poses.empty():
                items.append(self._poses.get_nowait())

            window_changed = False
            for item in items:
                if item is _STOP:
                    return
                window_changed |= self._add_pose(*item)
            if not window_changed or len(self._window) < self._seq_len:
                continue                                 # nothing new, or not one second yet

            # 2. Run the model once, on the newest window.
            try:
                probability = predict(np.asarray(self._window, dtype=np.float32)[np.newaxis])
                errors = 0
            except (ValueError, TypeError, tf.errors.OpError):
                errors += 1
                logger.exception("Inference error (%d in a row)", errors)
                if errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.error("The fall model failed %d times in a row; giving up", errors)
                    self.failed = True                   # the video thread stops the monitoring
                    return
                continue

            # 3. Hysteresis: a fall starts at FALL_ON and lasts until the probability drops below FALL_OFF.
            was_fall = self.latest is not None and self.latest.is_fall
            is_fall = probability >= (FALL_OFF if was_fall else FALL_ON)
            self.latest = FallPrediction(is_fall=is_fall, probability=probability)
            if is_fall and not was_fall:
                self.fall_detected.emit(probability)     # Qt queues it to the controller

    def _add_pose(self, timestamp_ms: float, pose: np.ndarray | None) -> bool:
        """Adds the pose to the window if it falls on a sampling instant. Returns True if added."""
        # Sampling: one pose every 1000 / fps ms, so the window always covers one real second.
        if self._next_sample_ms is None or timestamp_ms > self._next_sample_ms + self._period_ms:
            self._next_sample_ms = timestamp_ms          # first pose, or after a gap: start again here
        elif timestamp_ms < self._next_sample_ms - self._tolerance_ms:
            return False                                 # too early: skip this frame
        self._next_sample_ms += self._period_ms

        # While nobody is seen, the last pose is repeated (as in training).
        if pose is not None and pose.size == POSE_VALUES:
            self._last_pose = pose.reshape(POSE_VALUES)
        if self._last_pose is None:
            return False                                 # nobody seen yet: nothing to repeat
        self._window.append(self._last_pose)
        return True
