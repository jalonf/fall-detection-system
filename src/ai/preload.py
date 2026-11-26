"""Loads the heavy AI libraries (TensorFlow and MediaPipe) once, in the background, one after the other.

Importing them takes several seconds, so the application does not import them when it starts: the
sign-in screen would take that long to appear. `start()` loads them in a background thread as soon
as the window is up (while the user signs in), and the monitoring threads call `wait()` before
using them.

They are loaded one after the other in a single thread, so the interface competes with only one
import at a time. With the libraries already loaded, a monitoring goes live in about a second;
started before they are (a very quick sign-in), it simply waits for them.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)

THREAD_NAME = "ai-preload-thread"

_loaded = threading.Event()
_lock = threading.Lock()
_started = False


def start() -> None:
    """Starts loading the libraries in a background thread. Calling it again does nothing."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
    # Not a daemon: closing the window while it imports lets the import finish instead of killing
    # the thread half-way through loading native libraries.
    threading.Thread(target=_load, name=THREAD_NAME).start()


def wait() -> None:
    """Blocks until the libraries are loaded, starting the load if nobody has. Never from the GUI thread."""
    start()
    _loaded.wait()


def _load() -> None:
    began = time.perf_counter()
    try:
        import mediapipe  # noqa: F401
        import tensorflow  # noqa: F401
        from mediapipe.python.solutions import drawing_utils  # noqa: F401
        from mediapipe.tasks.python.vision.pose_landmarker import (
            PoseLandmarker,  # noqa: F401
        )
    except Exception:
        logger.exception("The AI libraries could not be preloaded")
    else:
        logger.info("AI libraries loaded in %.1f s", time.perf_counter() - began)
    finally:
        _loaded.set()
