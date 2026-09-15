import os
import logging
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm

from src.ai.extractor import MediaPipeExtractor

# Configure logging for professional monitoring
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def process_dataset(dataset_root: str, output_dir: str, seq_len: int = 30) -> None:
    """
    Processes the raw fall detection dataset, extracts 3D normalized skeletons 
    using MediaPipe, and exports consolidated temporal sliding windows as X_data.npy and y_data.npy.

    Args:
        dataset_root (str): Root directory containing 'ADL' and 'Fall' folders.
        output_dir (str): Destination directory for processed feature arrays.
        seq_len (int): Number of consecutive frames per temporal window (default: 30).
    """
    dataset_path = Path(dataset_root)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    if not dataset_path.exists():
        logger.error("Critical error: Dataset root path '%s' does not exist.", dataset_root)
        return

    logger.info("Initializing MediaPipeExtractor for dataset preprocessing...")
    extractor = MediaPipeExtractor()
    
    # Category mapping: ADL (Activities of Daily Living) -> 0, Fall -> 1
    categories = {"ADL": 0, "Fall": 1}
    
    # Collect all video files recursively to compute a precise global progress bar
    all_videos = []
    for category, label in categories.items():
        cat_path = dataset_path / category
        if cat_path.exists():
            video_files = list(cat_path.glob("**/*.mp4"))
            for video_file in video_files:
                all_videos.append((video_file, label, category))

    total_videos = len(all_videos)
    if total_videos == 0:
        logger.warning("No .mp4 video files found under the specified directory structure.")
        extractor.release()
        return

    logger.info("Starting preprocessing pipeline across %d total video files.", total_videos)
    
    X_list = []
    y_list = []
    
    # Global progress bar loop
    with tqdm(total=total_videos, desc="Dataset Preprocessing", unit="video", ncols=100) as pbar:
        for video_file, label, category in all_videos:
            rel_name = video_file.relative_to(dataset_path)
            pbar.set_postfix(cat=category, file=str(rel_name.name)[:20])

            cap = cv2.VideoCapture(str(video_file))
            if not cap.isOpened():
                logger.warning("Could not open video stream: %s", rel_name)
                pbar.update(1)
                continue
                
            frames_skeleton = []
            
            try:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        break
                        
                    # Extract 3D world-space skeleton normalized at center of mass
                    skeleton, _ = extractor.extract_skeleton(frame_bgr=frame)
                    
                    if skeleton is not None:
                        # Flatten 3D coordinates array: shape (33, 3) -> (99,)
                        frames_skeleton.append(skeleton.coordinates_3d.flatten())
                    else:
                        # Fallback mechanism for missing frames to ensure temporal continuity
                        if frames_skeleton:
                            frames_skeleton.append(frames_skeleton[-1])
                        else:
                            frames_skeleton.append(np.zeros(99, dtype=np.float32))
                            
            except Exception as e:
                logger.error("Unexpected error while parsing video %s: %s", rel_name, e)
            finally:
                cap.release()
            
            # Discard videos shorter than the required temporal sequence window length
            if len(frames_skeleton) < seq_len:
                pbar.update(1)
                continue
                
            # Generate sliding windows with 50% overlap (seq_len // 2)
            sequence_array = np.array(frames_skeleton, dtype=np.float32)
            step_size = max(1, seq_len // 2)
            
            for i in range(0, len(sequence_array) - seq_len + 1, step_size):
                window = sequence_array[i : i + seq_len]
                X_list.append(window)
                y_list.append(label)

            pbar.update(1)

    extractor.release()

    if len(X_list) > 0:
        X_data = np.array(X_list, dtype=np.float32)
        y_data = np.array(y_list, dtype=np.float32)
        
        np.save(out_path / "X_data.npy", X_data)
        np.save(out_path / "y_data.npy", y_data)
        logger.info("Preprocessing completed successfully. Saved %d consolidated samples into '%s'.", len(X_data), output_dir)
    else:
        logger.warning("No valid sliding windows were generated from the dataset.")


if __name__ == "__main__":
    DATASET_ROOT = "./fall_dataset" 
    OUTPUT_PROCESSED = "./processed_features"
    
    process_dataset(DATASET_ROOT, OUTPUT_PROCESSED, seq_len=30)