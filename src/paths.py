"""Where everything lives in the project.

Every path is built from the project root, so the application and the training scripts work
no matter which directory they are launched from. Import the path from here instead of writing it
as text in the code.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Models
MODELS_DIR = ROOT / "models"
FALL_MODELS_DIR = MODELS_DIR / "fall_detection"
RISK_MODEL_DIR = MODELS_DIR / "risk_model"
RISK_MODEL = RISK_MODEL_DIR / "risk_random_forest.joblib"
POSE_MODEL = MODELS_DIR / "pose" / "pose_landmarker_full.task"

# Datasets (ignored by Git, see data/README.md)
DATA_DIR = ROOT / "data"
FALL_VIDEOS_DIR = DATA_DIR / "fall_detection" / "raw" / "VideoDataset"
FALL_PROCESSED_DIR = DATA_DIR / "fall_detection" / "processed"
RISK_RAW_DIR = DATA_DIR / "risk_assessment" / "raw"
RISK_PROCESSED_DIR = DATA_DIR / "risk_assessment" / "processed"
ESDE_ZIP = RISK_RAW_DIR / "ESdEadulto_2025.zip"

# Others
DOCS_DIR = ROOT / "docs"
DATABASE_FILE = ROOT / "app.db"
