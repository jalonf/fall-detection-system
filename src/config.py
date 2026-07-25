from pathlib import Path

# Absolute path to the repository root (one level above src/)
PROJECT_ROOT = Path(__file__).parent.parent

# ── MediaPipe Tasks model paths ──────────────────────────────────────────────
# Download script: see README.md or run the download command in the project root.
# Model files are intentionally excluded from version control (.gitignore).
POSE_LANDMARKER_MODEL_PATH = str(PROJECT_ROOT / "models" / "pose_landmarker_full.task")