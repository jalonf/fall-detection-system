# Data

Datasets are not versioned (see `.gitignore`); only this file is. One folder per model:

```text
data/
├── fall_detection/              # GRU fall detector
│   ├── raw/VideoDataset/        # Videos: ADL/ (normal activities) and Fall/ (falls)
│   └── processed/               # Pose sequences (.npy), one folder per mode
│       ├── high_risk_30fps/
│       └── low_risk_15fps/
└── risk_assessment/             # Fall-risk model (Random Forest)
    ├── raw/
    │   └── ESdEadulto_2025.zip  # ESdE 2025 microdata (INE), as downloaded
    └── processed/
        ├── risk_dataset_esde2025.csv             # One row per person aged 65+: predictors, targets, weight
        └── risk_dataset_esde2025_dictionary.csv  # Meaning of every column and why it relates to falls
```

## Fall detection

Videos in `raw/` are converted to pose sequences by `python -m training.fall_detection.build_fall_dataset`.

## Risk assessment

`ESdEadulto_2025.zip` is the microdata of the *Encuesta de Salud y Estilos de Vida de los adultos
2025* (ESdE), published by the Spanish National Statistics Institute (INE, www.ine.es) together
with the Ministry of Health. It contains 21,641 respondents, 6,456 of them aged 65 or more.

`python -m training.risk_assessment.build_risk_dataset_esde` turns it into `processed/risk_dataset_esde2025.csv`
(6,396 people, 28 predictors that the application asks the patient, 7 targets and the survey weight).

The ESdE has **no question about falls**: the targets are a proxy based on accidents at home or
during leisure time in the last 12 months. `risk_dataset_esde2025_dictionary.csv` explains every
column.
