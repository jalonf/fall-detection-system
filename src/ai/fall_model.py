"""The GRU fall model: loading it and checking that it fits the pipeline."""

import logging
from collections.abc import Callable

import numpy as np

from src.ai import preload

logger = logging.getLogger(__name__)

POSE_VALUES = 99   # model input per frame: 33 landmarks x (x, y, z)
FALL_ON = 0.6      # a fall starts when the probability reaches this...
FALL_OFF = 0.4     # ...and ends when it drops below this (hysteresis)


def is_fall(probability: float, was_fall: bool) -> bool:
    """Hysteresis: a fall starts at FALL_ON and lasts until the probability drops below FALL_OFF.

    The application and the evaluation of the models both decide with this, so a probability
    hovering around 0.5 is one fall, not many.

    Args:
        probability: The model's output for the newest window (0-1).
        was_fall: Whether the previous window was a fall.
    """
    return probability >= (FALL_OFF if was_fall else FALL_ON)


class FallModelError(RuntimeError):
    """The fall model cannot be used: it did not load, or it keeps failing.

    Monitoring without a working model would look normal but never detect a fall, so the
    video pipeline stops and reports it instead of going on silently.
    """


def load_fall_model(model_path: str, seq_len: int) -> Callable[[np.ndarray], float]:
    """Loads the Keras model and checks that it fits the window.

    The model is called directly (`model(window, training=False)`), which is faster than
    `model.predict()` for a single window. A dummy window is run through it, so a file that
    loads but does not fit the pipeline is rejected here instead of failing on every window later.

    Args:
        model_path: The `.keras` file.
        seq_len: Poses per window (the model's frame rate: one second).

    Returns:
        A function that takes a (1, seq_len, POSE_VALUES) float32 window and returns the
        probability (0-1) that it shows a fall.

    Raises:
        FallModelError: If the file cannot be loaded or the model does not take those windows
            and return one probability.
    """
    # TensorFlow takes seconds to import: `preload` loads it in the background after the window
    # appears, never when the application starts. This waits for it (in the fall detection thread).
    preload.wait()
    import tensorflow as tf

    try:
        model = tf.keras.models.load_model(model_path, compile=False)
    except Exception as err:   # Keras raises many types (OSError, ValueError, ImportError...)
        raise FallModelError(f"Could not load the fall model {model_path}: {err}") from err

    # A GRU runs on windows of any length, so a wrong one would not fail: it would just predict badly.
    declared = tuple(model.input_shape[1:])
    if declared not in ((seq_len, POSE_VALUES), (None, POSE_VALUES)):
        raise FallModelError(
            f"The fall model {model_path} expects windows of shape {declared}, "
            f"but the pipeline sends ({seq_len}, {POSE_VALUES})"
        )

    try:
        output = model(np.zeros((1, seq_len, POSE_VALUES), dtype=np.float32), training=False)
    except Exception as err:
        raise FallModelError(f"The fall model {model_path} cannot run on the window: {err}") from err
    if tuple(output.shape) != (1, 1):
        raise FallModelError(f"The fall model {model_path} returns shape {tuple(output.shape)} instead of (1, 1)")

    logger.info("Fall model loaded: %s", model_path)
    return lambda window: float(model(window, training=False)[0][0])
