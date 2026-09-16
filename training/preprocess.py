import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GLOG_minloglevel"] = "3"

import logging
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm

from src.ai.extractor import MediaPipeExtractor

# Configure clean logging format
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def process_dataset(dataset_root: str, output_dir: str, target_fps: int = 30) -> None:
    dataset_path = Path(dataset_root)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Traditional if statement for sequence length configuration
    if target_fps == 30:
        seq_len = 30
    else:
        seq_len = 15

    if not dataset_path.exists():
        logger.error("Dataset path '%s' not found.", dataset_root)
        return

    extractor = MediaPipeExtractor()
    categories = {"ADL": 0, "Fall": 1}
    
    all_videos = []
    for category, label in categories.items():
        cat_path = dataset_path / category
        if cat_path.exists():
            for video_file in cat_path.glob("**/*.mp4"):
                all_videos.append((video_file, label, category))

    if not all_videos:
        logger.warning("No .mp4 videos found for %d FPS mode.", target_fps)
        extractor.release()
        return

    X_list, y_list = [], []
    
    # tqdm progress bar loop
    with tqdm(total=len(all_videos), desc=f"Processing {target_fps} FPS", unit="vid", ncols=90) as pbar:
        for video_file, label, category in all_videos:
            pbar.set_postfix(cat=category, file=video_file.name[:15])

            cap = cv2.VideoCapture(str(video_file))
            if not cap.isOpened():
                pbar.update(1)
                continue
                
            original_fps = cap.get(cv2.CAP_PROP_FPS)
            if original_fps <= 1:
                original_fps = 30.0
                
            raw_frames = []
            try:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        break
                        
                    skeleton, _ = extractor.extract_skeleton(frame_bgr=frame)
                    if skeleton is not None:
                        raw_frames.append(skeleton.coordinates_3d.flatten())
                    else:
                        if raw_frames:
                            raw_frames.append(raw_frames[-1])
                        else:
                            raw_frames.append(np.zeros(99, dtype=np.float32))
            finally:
                cap.release()
            
            # Sub-sampling with traditional if statements
            if target_fps == 15:
                stride = max(1, round(original_fps / target_fps))
                frames = raw_frames[::stride]
            else:
                if original_fps > 30:
                    stride = max(1, round(original_fps / target_fps))
                else:
                    stride = 1
                
                if stride > 1:
                    frames = raw_frames[::stride]
                else:
                    frames = raw_frames

            if len(frames) < seq_len:
                pbar.update(1)
                continue
                
            sequence_array = np.array(frames, dtype=np.float32)
            step_size = max(1, seq_len // 2)
            
            for i in range(0, len(sequence_array) - seq_len + 1, step_size):
                X_list.append(sequence_array[i : i + seq_len])
                y_list.append(label)

            pbar.update(1)

    extractor.release()

    if X_list:
        np.save(out_path / "X_data.npy", np.array(X_list, dtype=np.float32))
        np.save(out_path / "y_data.npy", np.array(y_list, dtype=np.float32))
        logger.info("Saved %d samples to '%s'.", len(X_list), output_dir)
    else:
        logger.warning("No valid windows generated for %d FPS.", target_fps)


if __name__ == "__main__":
    DATASET_ROOT = "./fall_dataset" 
    
    logger.info("Starting Dual-Mode Preprocessing")
    
    # 1. High-Risk / Precision Mode (30 FPS, window = 30 frames)
    process_dataset(
        dataset_root=DATASET_ROOT, 
        output_dir="./processed_features/high_risk_30fps", 
        target_fps=30
    )
    
    # 2. Low-Risk / Eco Mode (15 FPS with adaptive sub-sampling, window = 15 frames)
    process_dataset(
        dataset_root=DATASET_ROOT, 
        output_dir="./processed_features/low_risk_15fps", 
        target_fps=15
    )
    
    logger.info("Preprocessing Completed")