import logging
from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd

from src.paths import RISK_MODEL

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RiskResult:
    level: str           # "LOW", "MEDIUM" or "HIGH": it selects the monitoring strategy
    probability: float   # probability (0-1) that the patient has an accident at home or in leisure time


class RiskAssessor:
    """
    Estimates the fall risk level of a patient from the sign-up questionnaire.

    It uses the Random Forest trained in `training/risk_assessment/train_risk_model.py`. The model file
    also stores the questions the model expects and the probability limits of each level, so
    nothing about the model is repeated here. The file is read the first time it is needed.
    """

    def __init__(self, model_path=RISK_MODEL):
        self._model_path = model_path
        self._saved: dict = {}

    def _load(self) -> dict:
        if not self._saved:
            self._saved = joblib.load(self._model_path)
            logger.info("Risk model loaded from: %s", self._model_path)
        return self._saved

    def assess(self, answers: dict[str, float]) -> RiskResult:
        """Returns the risk level for the answers (keyed by the model's questions)."""
        saved = self._load()
        missing = [name for name in saved["features"] if name not in answers]
        if missing:
            raise ValueError(f"Missing answers for the risk model: {', '.join(missing)}")

        row = pd.DataFrame([answers])[saved["features"]]   # same columns and order as in training
        probability = float(saved["model"].predict_proba(row)[0, 1])
        level = saved["levels"][int(np.digitize(probability, saved["thresholds"]))]
        logger.info("Risk assessed: %s (probability %.3f)", level, probability)
        return RiskResult(level, probability)
