# Data

Datasets are not versioned (see `.gitignore`); only this file is. Download them from their sources
(see [Datasets](../README.md#datasets) in the main README) and place them as shown. One folder per model:

```text
data/
├── fall_detection/                       # GRU fall detector
│   ├── raw/
│   │   ├── VideoDataset.zip              # As downloaded
│   │   └── VideoDataset/                 # Extracted: ADL/ (normal activities) and Fall/ (falls)
│   └── processed/                        # Written by build_fall_dataset, one folder per mode
│       ├── high_risk_30fps/              # X_data, y_data, subject_data, video_data (.npy)
│       └── low_risk_15fps/
└── risk_assessment/                      # Fall-risk model (Random Forest)
    ├── raw/
    │   ├── ESdEadulto_2025.zip           # ESdE 2025 microdata, as downloaded (the script reads it)
    │   └── ESdEadulto_2025/              # Extracted (optional): microdata and record layout (dr_*.xlsx / .json)
    └── processed/                        # Written by build_risk_dataset_esde
        ├── risk_dataset_esde2025.csv             # One row per person aged 65+: predictors, targets, weight
        └── risk_dataset_esde2025_dictionary.csv  # Meaning of every column and why it relates to falls
```

## Fall detection

`raw/VideoDataset/` is `VideoDataset.zip` from the *Video-Based Fall Detection Dataset with 2017
Activities from 29 Subjects* (Ivan Ursul, figshare, 2025, https://doi.org/10.6084/m9.figshare.28596332,
licence CC BY 4.0): 2,014 videos (1,017 normal activities, 997 falls) of 29 subjects, about 1.9 s
each at 30 FPS. Each recording is in `ADL|Fall/SBJ_<subject>_LOC<location>/ACT<action>_<side>_<attempt>/`,
with the `.mp4`, the readings of a wearable sensor (`.txt`, not used) and a `metadata.json`.

`python -m training.fall_detection.build_fall_dataset` runs MediaPipe on every video and writes, for
each mode, four arrays with one entry per window:

| File | Content |
|---|---|
| `X_data.npy` | One-second windows of 3D poses: (windows, 30 or 15 frames, 99), the 33 landmarks in metres, centred on the hips |
| `y_data.npy` | 0 = normal activity, 1 = fall (every window takes the label of its video) |
| `subject_data.npy` | The person recorded, from the `SBJ_xx` folder |
| `video_data.npy` | The video the window comes from |

| Mode | Frame rate | Windows | Falls |
|---|---|---|---|
| `high_risk_30fps` | 30 FPS, 30-frame windows | 4,025 | 1,994 |
| `low_risk_15fps` | 15 FPS (every second frame), 15-frame windows | 5,046 | 2,484 |

Consecutive windows of a video overlap by half. A frame where nobody is found repeats the last pose
(zeros before the first one). The subject and video let the evaluation keep every video of a person
out of training (`train_fall_model.py`).

## Risk assessment

`ESdEadulto_2025.zip` is the adult questionnaire microdata of the *Encuesta de Salud de España
(ESdE) 2025*, run by the Ministry of Health (Ministerio de Sanidad) and the Spanish National
Statistics Institute (INE), who must be cited as the source of the primary data. It contains 21,641
respondents, 6,456 of them aged 65 or more. The record layout (`dr_ESdEadulto_2025.xlsx`) describes
every variable and its codes.

`python -m training.risk_assessment.build_risk_dataset_esde` turns it into
`processed/risk_dataset_esde2025.csv`: 6,396 people aged 65+ (those whose targets are known), the 28
predictors that the application asks about the patient, 7 targets and the survey weight
(`sample_weight`). Unanswered predictors take the median of their column.

The ESdE has **no question about falls**, so the targets are proxies based on accidents in the last
12 months. The model learns `y_accident_home`, an accident at home (442 people, 6.9 %), the closest
to a fall at home; the other targets are kept to compare with it (see the main README).
`risk_dataset_esde2025_dictionary.csv` explains every column.
