import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import logging
import numpy as np
import tensorflow as tf
from keras import layers, models
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_dataset(processed_dir: str) -> tuple[np.ndarray, np.ndarray]:
    """Load consolidated dataset arrays from disk for a specific mode."""
    x_path = os.path.join(processed_dir, "X_data.npy")
    y_path = os.path.join(processed_dir, "y_data.npy")
    
    if not os.path.exists(x_path) or not os.path.exists(y_path):
        raise FileNotFoundError(f"Consolidated dataset files not found in '{processed_dir}'.")
        
    logger.info("Loading dataset from %s...", processed_dir)
    return np.load(x_path), np.load(y_path)


def train_fall_detector(processed_dir: str, model_save_path: str, seq_len: int, mode_name: str) -> None:
    """Trains, evaluates, and saves a GRU model for a specific operational mode."""
    logger.info("Starting training pipeline for: %s", mode_name)
    
    # 1. Load dataset
    try:
        X, y = load_dataset(processed_dir)
    except Exception as e:
        logger.error("%s", e)
        return

    # 2. Split dataset into train and validation sets (stratified)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Build GRU model architecture matching theoretical schema
    model = models.Sequential([
        layers.Input(shape=(seq_len, 99)),
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

    # 4. Train model with checkpointing and early stopping
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        filepath=model_save_path, monitor='val_loss', save_best_only=True, verbose=0
    )
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=4, restore_best_weights=True, verbose=1
    )

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=20,
        batch_size=32,
        callbacks=[checkpoint, early_stopping],
        verbose="auto"
    )

    # 5. Evaluate best model on validation set
    logger.info("Evaluating best model for %s...", mode_name)
    best_model = tf.keras.models.load_model(MODEL_SAVE_PATH_STR := model_save_path, compile=False)
    y_pred = (best_model.predict(X_val) >= 0.5).astype(int).flatten()

    cm = confusion_matrix(y_val, y_pred)
    print(f"\n[{mode_name}] Confusion Matrix:\n", cm)
    print(f"\n[{mode_name}] Classification Report:\n", classification_report(y_val, y_pred, target_names=["ADL (Normal)", "Fall (Alarm)"]))

    # 6. Generate evaluation plots inside mode-specific directories under ./docs/
    mode_folder_name = mode_name.lower()
    docs_sub_dir = os.path.join("./docs", mode_folder_name)
    os.makedirs(docs_sub_dir, exist_ok=True)
    
    # Confusion Matrix Plot
    fig, ax = plt.subplots(figsize=(6, 4))
    ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["ADL", "Fall"]).plot(cmap=plt.cm.Blues, ax=ax, colorbar=False)
    plt.title(f"Confusion Matrix - {mode_name}")
    plt.savefig(os.path.join(docs_sub_dir, "confusion_matrix.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # Training Curves Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.plot(history.history['loss'], label='Train')
    ax1.plot(history.history['val_loss'], label='Val', linestyle='--')
    ax1.set_title(f'Loss Evolution ({mode_name})')
    ax1.legend()
    
    ax2.plot(history.history['accuracy'], label='Train')
    ax2.plot(history.history['val_accuracy'], label='Val', linestyle='--')
    ax2.set_title(f'Accuracy Evolution ({mode_name})')
    ax2.legend()
    
    plt.savefig(os.path.join(docs_sub_dir, "training_performance.png"), dpi=300, bbox_inches='tight')
    plt.close()

    logger.info("Finished pipeline for %s. Model saved at '%s' and docs saved in '%s'.\n", mode_name, model_save_path, docs_sub_dir)


if __name__ == "__main__":
    logger.info("Starting Safeguard Dual-Mode Training Pipeline")
    
    # 1. Train High-Risk Model (30 FPS, window size 30)
    train_fall_detector(
        processed_dir="./processed_features/high_risk_30fps",
        model_save_path="assets/fall_gru_high_risk_30fps.keras",
        seq_len=30,
        mode_name="High_Risk_30FPS"
    )
    
    # 2. Train Low-Risk Model (15 FPS, window size 15)
    train_fall_detector(
        processed_dir="./processed_features/low_risk_15fps",
        model_save_path="assets/fall_gru_low_risk_15fps.keras",
        seq_len=15,
        mode_name="Low_Risk_15FPS"
    )
    
    logger.info("All Training Pipelines Completed Successfully")