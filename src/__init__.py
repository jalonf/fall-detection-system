"""Application package.

Runs before any submodule is imported, so the TensorFlow log level is set before
mediapipe/TensorFlow are loaded (their C++ logger reads it only once, at import time).
"""

import os

# 2 = hide INFO and WARNING messages from TensorFlow's C++ runtime (e.g. the oneDNN notice).
# setdefault keeps any value the user already exported in the environment.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
