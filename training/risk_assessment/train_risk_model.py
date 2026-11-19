import logging
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import ConfusionMatrixDisplay, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from src.paths import DOCS_DIR, RISK_MODEL, RISK_PROCESSED_DIR
from training.build_risk_dataset_esde import PREDICTOR_COLUMNS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TARGET = "y_any_event"                 # accident at home / leisure time, with care or with sequelae
LEVELS = ["LOW", "MEDIUM", "HIGH"]
LEVEL_PERCENTILES = (50, 80)           # LOW: lowest 50 % of the probabilities, HIGH: highest 20 %
RANDOM_STATE = 42


def load_dataset(csv_path: str) -> tuple[pd.DataFrame, pd.Series]:
    """Returns the questionnaire answers (X) and what happened to each person (y)."""
    data = pd.read_csv(csv_path)
    return data[PREDICTOR_COLUMNS], data[TARGET]


def build_model() -> RandomForestClassifier:
    """The Random Forest and its hyperparameters (chosen by comparing configurations with cross-validation)."""
    return RandomForestClassifier(
        n_estimators=500,        # number of trees
        min_samples_leaf=30,     # every leaf groups at least 30 people: avoids memorizing individuals
        max_features=3,          # each split only looks at 3 random questions: makes the trees different
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )


def risk_level(probability: float, thresholds: list[float]) -> str:
    """Turns a probability into LOW, MEDIUM or HIGH using the limits chosen in training."""
    return LEVELS[int(np.digitize(probability, thresholds))]


def save_confusion_matrices(y: pd.Series, levels: pd.Series, docs_dir: Path) -> None:
    """Draws one confusion matrix for each way of using the level: flag from MEDIUM, or flag only at HIGH."""
    rules = {"MEDIUM or HIGH": levels != "LOW", "HIGH only": levels == "HIGH"}

    _, axes = plt.subplots(1, len(rules), figsize=(11, 4))
    for ax, (rule, flagged) in zip(axes, rules.items()):
        display = ConfusionMatrixDisplay.from_predictions(
            y, flagged.astype(int), display_labels=["No", "Yes"], cmap=plt.cm.Blues, ax=ax, colorbar=False
        )
        ax.set_title(f"Flagged when the level is {rule}")
        ax.set_xlabel("Flagged by the model")
        ax.set_ylabel("Had the event")

        true_negative, false_positive, false_negative, true_positive = display.confusion_matrix.ravel()
        logger.info(
            "%s -> sensitivity (events found) %.2f, specificity %.2f, precision %.2f",
            rule,
            true_positive / (true_positive + false_negative),
            true_negative / (true_negative + false_positive),
            true_positive / (true_positive + false_positive),
        )

    docs_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(docs_dir / "confusion_matrix.png", dpi=300, bbox_inches="tight")
    plt.close()


def train_risk_model(dataset_path: str, model_path: str, docs_dir: Path) -> None:
    """Evaluates the model with cross-validation and saves the final one."""
    # 1. Load dataset
    X, y = load_dataset(dataset_path)
    logger.info("Loaded %d people, %d questions. People with the event: %.1f%%", len(X), X.shape[1], 100 * y.mean())

    # 2. Cross-validation: every person is predicted by a model that has NOT seen them,
    #    so the probabilities are honest (the final model would be too optimistic on its own data).
    model = build_model()
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    probabilities = cross_val_predict(model, X, y, cv=folds, method="predict_proba")[:, 1]
    logger.info("Cross-validated AUC: %.3f (0.5 is chance, 1 is perfect)", roc_auc_score(y, probabilities))

    # 3. Risk levels: the limits are percentiles of the probabilities.
    thresholds = np.percentile(probabilities, LEVEL_PERCENTILES).tolist()
    levels = pd.Series([risk_level(p, thresholds) for p in probabilities], name="level")
    report = y.groupby(levels).agg(people="count", events="sum", event_rate="mean").loc[LEVELS]
    logger.info("Probability limits: LOW < %.3f <= MEDIUM < %.3f <= HIGH", *thresholds)
    logger.info("People and observed event rate per level:\n%s", report.round(3).to_string())
    save_confusion_matrices(y, levels, docs_dir)
    logger.info("Confusion matrices saved in '%s'.", docs_dir)

    # 4. Final model, trained with all the data
    model.fit(X, y)
    importance = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
    logger.info("Most important questions:\n%s", importance.head(10).round(3).to_string())

    # 5. Save the model together with what the application needs to use it
    model_file = {"model": model, "features": list(X.columns), "thresholds": thresholds, "levels": LEVELS}
    joblib.dump(model_file, model_path)
    logger.info("Model saved at '%s'.", model_path)


if __name__ == "__main__":
    logger.info("Starting Risk Model Training")

    RISK_MODEL.parent.mkdir(parents=True, exist_ok=True)
    train_risk_model(
        dataset_path=str(RISK_PROCESSED_DIR / "risk_dataset_esde2025.csv"),
        model_path=str(RISK_MODEL),
        docs_dir=DOCS_DIR / "risk_assessment",
    )

    logger.info("Training Completed")