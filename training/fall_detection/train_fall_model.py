"""Evaluates and trains the two GRU fall-detection models (15 and 30 FPS).

The evaluation is by subject: the people recorded are split into 5 groups (StratifiedGroupKFold)
and each group is predicted by a model trained without any of its videos, so no window of a test
person (nor the window of the same video that overlaps it by half) is ever seen in training. Two
kinds of results are reported, as the mean and standard deviation over the 5 groups:

- Windows: accuracy, precision, recall, F1 (threshold 0.5) and ROC AUC of every one-second window.
- Videos, as the application decides: every test video is replayed one pose at a time through the
  model with the application's hysteresis (`FALL_ON` / `FALL_OFF`). A fall video is detected if it
  raises an alarm; a normal-activity video that raises one is a false alarm.

The report (`evaluation.json`) and the pooled confusion matrices go to `docs/<mode>/`. Then the
final model is trained with every subject but a fifth of them, kept apart for early stopping,
and saved in `models/fall_detection/` with its training curves.

    python -m training.fall_detection.train_fall_model                  # evaluate and train
    python -m training.fall_detection.train_fall_model --evaluate-only  # evaluate, keep the models
"""

import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import argparse
import json
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")   # files only, no window

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from keras import layers, models
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold

from src.ai.fall_model import FALL_OFF, FALL_ON, POSE_VALUES, is_fall
from src.paths import DOCS_DIR, FALL_MODELS_DIR, FALL_PROCESSED_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SEED = 42
FOLDS = 5                     # groups of subjects of the evaluation
VALIDATION_SUBJECTS = 0.2     # share of the training subjects kept apart for early stopping
EPOCHS, BATCH_SIZE, PATIENCE = 20, 32, 4

MODES = (
    # (folder in data/ and docs/, model file, window length, name)
    ("high_risk_30fps", "fall_gru_high_risk_30fps.keras", 30, "High_Risk_30FPS"),
    ("low_risk_15fps", "fall_gru_low_risk_15fps.keras", 15, "Low_Risk_15FPS"),
)
WINDOW_METRICS = ("accuracy", "precision", "recall", "f1", "roc_auc")
VIDEO_METRICS = ("falls_detected", "adl_false_alarms")


def load_dataset(processed_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Loads the windows, their labels, and the subject and video each one comes from."""
    files = {name: processed_dir / f"{name}_data.npy" for name in ("X", "y", "subject", "video")}
    missing = [path.name for path in files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing {', '.join(missing)} in '{processed_dir}'. "
            "Build them with: python -m training.fall_detection.build_fall_dataset"
        )
    logger.info("Loading dataset from %s...", processed_dir)
    X, y, subjects, videos = (np.load(files[name]) for name in ("X", "y", "subject", "video"))
    return X, y, subjects, videos


def build_model(seq_len: int, mode_name: str) -> tf.keras.Model:
    """The GRU: one second of poses in, the probability of a fall out."""
    model = models.Sequential([
        layers.Input(shape=(seq_len, POSE_VALUES)),
        layers.GRU(64, return_sequences=False, activation='tanh'),
        layers.Dropout(0.3),
        layers.Dense(32, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ], name=f"GRU_FallDetector_{mode_name}")
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.Precision(name='precision'), tf.keras.metrics.Recall(name='recall')]
    )
    return model


def split_validation(subjects: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Splits the training windows by subject: (windows to fit, windows for early stopping)."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=VALIDATION_SUBJECTS, random_state=seed)
    return next(splitter.split(np.zeros(len(subjects)), groups=subjects))


def fit(model: tf.keras.Model, train: tuple[np.ndarray, np.ndarray], validation: tuple[np.ndarray, np.ndarray],
        checkpoint_path: Path | None = None) -> tf.keras.callbacks.History:
    """Trains until the validation loss stops improving and keeps the best weights."""
    callbacks: list[tf.keras.callbacks.Callback] = [
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=PATIENCE, restore_best_weights=True)]
    if checkpoint_path is not None:
        callbacks.append(tf.keras.callbacks.ModelCheckpoint(
            filepath=str(checkpoint_path), monitor='val_loss', save_best_only=True, verbose=0))
    return model.fit(*train, validation_data=validation, epochs=EPOCHS, batch_size=BATCH_SIZE,
                     callbacks=callbacks, verbose=0)


def video_sequences(X: np.ndarray, videos: np.ndarray, seq_len: int) -> dict[int, np.ndarray]:
    """Rebuilds the pose sequence of every video from its windows, which overlap by half."""
    step = max(1, seq_len // 2)
    parts: dict[int, list[np.ndarray]] = {}
    for window, video in zip(X, videos):
        video = int(video)
        if video in parts:
            parts[video].append(window[seq_len - step:])   # only the poses the previous window did not have
        else:
            parts[video] = [window]
    return {video: np.concatenate(pieces) for video, pieces in parts.items()}


def count_alarms(probabilities: np.ndarray) -> int:
    """The alarms the application would raise for these consecutive probabilities (with its hysteresis)."""
    alarms, falling = 0, False
    for probability in probabilities:
        now = is_fall(float(probability), falling)
        alarms += now and not falling
        falling = now
    return alarms


def replay_videos(model: tf.keras.Model, sequences: dict[int, np.ndarray], seq_len: int) -> dict[int, int]:
    """Runs the model on every one-second window of each video, one pose at a time as the application does.

    Returns:
        The number of alarms of each video.
    """
    windows, owners = [], []
    for video, sequence in sequences.items():
        for start in range(len(sequence) - seq_len + 1):
            windows.append(sequence[start:start + seq_len])
            owners.append(video)
    probabilities = model.predict(np.stack(windows), batch_size=1024, verbose=0).ravel()
    owners = np.array(owners)
    return {video: count_alarms(probabilities[owners == video]) for video in sequences}


def evaluate_by_subject(X: np.ndarray, y: np.ndarray, subjects: np.ndarray, videos: np.ndarray, seq_len: int,
                        mode_name: str, docs_dir: Path) -> dict:
    """Cross-validation by subject: every window and video is predicted by a model that never saw that person.

    Returns:
        The report saved as `evaluation.json`: metrics per fold, their mean and standard deviation,
        and the pooled confusion matrices.
    """
    folds = StratifiedGroupKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    per_fold, window_true, window_pred, video_true, video_alarm = [], [], [], [], []

    for fold, (train_idx, test_idx) in enumerate(folds.split(X, y, groups=subjects), start=1):
        tf.keras.utils.set_random_seed(SEED + fold)
        fit_idx, val_idx = split_validation(subjects[train_idx], SEED + fold)
        fit_idx, val_idx = train_idx[fit_idx], train_idx[val_idx]
        model = build_model(seq_len, mode_name)
        fit(model, (X[fit_idx], y[fit_idx]), (X[val_idx], y[val_idx]))

        # Windows, at 0.5 (as the original evaluation)
        probability = model.predict(X[test_idx], verbose=0).ravel()
        truth, prediction = y[test_idx].astype(int), (probability >= 0.5).astype(int)

        # Videos, as the application decides
        alarms = replay_videos(model, video_sequences(X[test_idx], videos[test_idx], seq_len), seq_len)
        label = {int(v): int(t) for v, t in zip(videos[test_idx], truth)}
        fall_videos = [v for v in alarms if label[v] == 1]
        adl_videos = [v for v in alarms if label[v] == 0]

        result = {
            "fold": fold,
            "test_subjects": sorted(int(s) for s in np.unique(subjects[test_idx])),
            "test_windows": len(test_idx),
            "test_fall_videos": len(fall_videos),
            "test_adl_videos": len(adl_videos),
            "accuracy": accuracy_score(truth, prediction),
            "precision": precision_score(truth, prediction, zero_division=0),
            "recall": recall_score(truth, prediction, zero_division=0),
            "f1": f1_score(truth, prediction, zero_division=0),
            "roc_auc": roc_auc_score(truth, probability),
            "falls_detected": float(np.mean([alarms[v] > 0 for v in fall_videos])),
            "adl_false_alarms": float(np.mean([alarms[v] > 0 for v in adl_videos])),
        }
        per_fold.append(result)
        logger.info("[%s] fold %d (subjects %s): accuracy %.3f, recall %.3f, AUC %.3f | "
                    "fall videos detected %.3f, ADL videos with a false alarm %.3f",
                    mode_name, fold, result["test_subjects"], result["accuracy"], result["recall"],
                    result["roc_auc"], result["falls_detected"], result["adl_false_alarms"])

        window_true += truth.tolist()
        window_pred += prediction.tolist()
        video_true += [label[v] for v in alarms]
        video_alarm += [int(alarms[v] > 0) for v in alarms]

    summary = {
        name: {"mean": float(np.mean([f[name] for f in per_fold])), "std": float(np.std([f[name] for f in per_fold]))}
        for name in WINDOW_METRICS + VIDEO_METRICS
    }
    window_matrix = confusion_matrix(window_true, window_pred, labels=[0, 1])
    video_matrix = confusion_matrix(video_true, video_alarm, labels=[0, 1])
    report = {
        "model": mode_name,
        "evaluation": f"StratifiedGroupKFold by subject, {FOLDS} folds",
        "subjects": len(np.unique(subjects)),
        "windows": len(y),
        "videos": len(np.unique(videos)),
        "hysteresis": {"fall_on": FALL_ON, "fall_off": FALL_OFF},
        "summary": summary,
        "window_confusion_matrix": window_matrix.tolist(),
        "video_confusion_matrix": video_matrix.tolist(),
        "folds": per_fold,
    }

    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    save_confusion_matrices(window_matrix, video_matrix, mode_name, docs_dir)
    for name in WINDOW_METRICS + VIDEO_METRICS:
        logger.info("[%s] %-17s %.3f ± %.3f", mode_name, name, summary[name]["mean"], summary[name]["std"])
    return report


def save_confusion_matrices(window_matrix: np.ndarray, video_matrix: np.ndarray, mode_name: str,
                            docs_dir: Path) -> None:
    """Draws the pooled confusion matrices of the evaluation: windows (at 0.5) and videos (as the application)."""
    _, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ConfusionMatrixDisplay(window_matrix, display_labels=["ADL", "Fall"]).plot(cmap="Blues", ax=ax1, colorbar=False)
    ax1.set_title(f"Windows, unseen subjects - {mode_name}")
    ConfusionMatrixDisplay(video_matrix, display_labels=["ADL", "Fall"]).plot(cmap="Blues", ax=ax2, colorbar=False)
    ax2.set_title(f"Videos, with the app's alarm - {mode_name}")
    ax2.set_xlabel("Alarm raised (ADL = no, Fall = yes)")
    plt.savefig(docs_dir / "confusion_matrix.png", dpi=300, bbox_inches='tight')
    plt.close()


def train_final_model(X: np.ndarray, y: np.ndarray, subjects: np.ndarray, seq_len: int, mode_name: str,
                      model_path: Path, docs_dir: Path) -> None:
    """Trains the model the application uses, keeping a fifth of the subjects apart for early stopping."""
    tf.keras.utils.set_random_seed(SEED)
    fit_idx, val_idx = split_validation(subjects, SEED)
    model = build_model(seq_len, mode_name)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    history = fit(model, (X[fit_idx], y[fit_idx]), (X[val_idx], y[val_idx]), checkpoint_path=model_path)

    _, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.plot(history.history['loss'], label='Train')
    ax1.plot(history.history['val_loss'], label='Val (unseen subjects)', linestyle='--')
    ax1.set_title(f'Loss Evolution ({mode_name})')
    ax1.legend()
    ax2.plot(history.history['accuracy'], label='Train')
    ax2.plot(history.history['val_accuracy'], label='Val (unseen subjects)', linestyle='--')
    ax2.set_title(f'Accuracy Evolution ({mode_name})')
    ax2.legend()
    docs_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(docs_dir / "training_performance.png", dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("Model saved at '%s'.", model_path)


def main(argv: list[str] | None = None) -> None:
    """Evaluates both models by subject and, unless --evaluate-only, trains and saves them."""
    parser = argparse.ArgumentParser(prog="python -m training.fall_detection.train_fall_model")
    parser.add_argument("--evaluate-only", action="store_true", help="evaluate by subject and keep the saved models")
    args = parser.parse_args(argv)

    for folder, model_file, seq_len, mode_name in MODES:
        try:
            X, y, subjects, videos = load_dataset(FALL_PROCESSED_DIR / folder)
        except FileNotFoundError as err:
            logger.error("%s", err)
            continue
        logger.info("[%s] %d windows (%d falls) from %d videos of %d subjects", mode_name, len(y), int(y.sum()),
                    len(np.unique(videos)), len(np.unique(subjects)))
        docs_dir = DOCS_DIR / folder
        evaluate_by_subject(X, y, subjects, videos, seq_len, mode_name, docs_dir)
        if not args.evaluate_only:
            train_final_model(X, y, subjects, seq_len, mode_name, FALL_MODELS_DIR / model_file, docs_dir)


if __name__ == "__main__":
    main()
