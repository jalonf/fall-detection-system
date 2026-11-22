# FallSense · Fall risk assessment and detection

**FallSense** is a desktop application that watches a person through a camera and raises an
alert when it detects a fall. MediaPipe extracts the 3D pose of the person in every frame and a GRU
recurrent network classifies the last second of movement as a normal activity or a fall.
When a fall starts, the application records the event and e-mails the caregiver with a
capture of the fall.

Developed as a **Bachelor's Thesis (Trabajo de Fin de Grado, TFG)**.

---

## Features

* **Live monitoring** from a webcam, with the person's skeleton and bounding box drawn on the video.
* **Three detection modes** chosen from the patient's risk level, which is calculated at sign-up from a
  short health questionnaire (see [Risk levels](#risk-levels)).
* **Privacy:** the face is blurred before anything is displayed, stored or sent.
* **Fall alerts:** the event is stored in the database and an e-mail with a capture of the fall
  is sent through Gmail (SMTP). The capture only lives in memory: it is never written to disk.
* **User accounts** (login and sign-up) with a patient linked to each caregiver.
* **Administrator (tester) view**: no patient and a **test mode** in which falls are shown and logged
  but never stored or e-mailed. The tester picks the camera's test profile (the settings and model of a
  risk level), analyses uploaded video files and sees an extra skeleton panel and live telemetry
  (inference time, pose confidence, hip height). Administrators cannot sign up from the application;
  they are created from the command line (see [Running the application](#running-the-application)).

---

## How it works

For every frame, `BaseVideoWorker` runs this pipeline in its own thread:

1. **Pose:** `MediaPipeExtractor` returns the 33 body landmarks in 3D (meters), centred on the
   midpoint of the hips so the position of the person in the room does not matter, plus the
   2D landmarks used for drawing.
2. **Privacy:** the face area is blurred.
3. **Model:** the pose (33 × 3 = 99 values) is added to a sliding window. When the window is
   full, `InferenceWorker` runs the GRU model in a separate thread. A probability of 0.5 or
   more is a fall.
4. **Drawing and telemetry:** skeleton, bounding box and the administrator's telemetry.
5. **Fall:** when the prediction changes to "fall", a `FallEvent` is stored and the alert
   e-mail (with the capture attached from memory) is sent in the background so the video does
   not stall.

### Risk levels

Each patient has a risk level, calculated at sign-up. The caregiver answers a health questionnaire
about the patient (`src/domain/questionnaire.py`: age, mobility, pain, conditions, medication...) and a
Random Forest (`src/ai/risk_assessor.py`) turns the answers into LOW, MEDIUM or HIGH. If the model cannot
be used, the patient is registered as HIGH, the strictest level. The level decides how the camera is
configured and which model is used (`src/workers/strategies.py`):

| Risk   | Camera | Model window | Model file |
|--------|--------|--------------|------------|
| LOW    | 640 × 480, 15 FPS  | 15 frames (1 s) | `models/fall_detection/fall_gru_low_risk_15fps.keras` |
| MEDIUM | 1280 × 720, 15 FPS | 15 frames (1 s) | `models/fall_detection/fall_gru_low_risk_15fps.keras` |
| HIGH   | 1280 × 720, 30 FPS | 30 frames (1 s) | `models/fall_detection/fall_gru_high_risk_30fps.keras` |

For an uploaded video the model is chosen from the file's own frame rate instead
(20 FPS or less → 15-frame model, otherwise the 30-frame model), because the model has to
match the speed of the frames it receives.

### Model

Both models share the same architecture, trained with Keras (`training/fall_detection/train_fall_model.py`):

```text
Input (window, 99) → GRU(64) → Dropout(0.3) → Dense(32, ReLU) → Dense(1, sigmoid)
```

The confusion matrices and training curves are in `docs/high_risk_30fps/` and
`docs/low_risk_15fps/`.

---

## Architecture

The application follows **Model-View-Controller** on top of PySide6 (Qt):

* **Views** (`src/views/`): the login / sign-up screen (`AuthView`), the caregiver's monitoring
  screen (`MonitorView`) and the administrator's one (`AdminView`).
* **Navigation** (`src/navigation/`, Application Controller / Coordinator pattern): `AppCoordinator`
  owns the flow (sign-in → the dashboard of the user's role → sign-out) and builds each screen (a view
  and its controller); controllers only report events and never open screens themselves. `Navigator`
  shows one screen at a time with a cross-fade and owns their life cycle: it stops the controller of
  the screen being left (releasing the camera) and destroys its view.
* **Controllers** (`src/controllers/`): `AuthController` handles login and sign-up.
  `BaseMonitorController` starts and stops the video workers and shows what they report;
  `MonitorController` and `AdminController` extend it. `AdminController` only accepts administrators
  and runs everything in test mode (workers without user or patient, so nothing is stored or sent).
* **Workers** (`src/workers/`): Qt threads that do the heavy work. `VideoWorker` reads the
  camera and `VideoFileWorker` an uploaded file; both share the pipeline in `BaseVideoWorker`.
  The monitoring strategies (Strategy pattern) hold the camera settings and the model of each
  risk level.
* **Persistence** (`src/database/`, `src/repositories/`): SQLite through the Peewee ORM, with
  the `User`, `Patient` and `FallEvent` models. Repositories are the only classes that query
  the database. Every account, administrators included, is a `User` row with a role (role-based
  access): the role decides the screen and the permissions, and the table only accepts the roles
  defined in `src/domain/roles.py`. Administrators simply have no `Patient`.
* **Notifications** (`src/notifications/`): builds and sends the alert e-mail.

---

## Repository structure

```text
fall-detection-system/
├── data/                   # Datasets, one folder per model (ignored by Git, see data/README.md)
│   ├── fall_detection/     # Videos (raw/) and pose sequences (processed/) of the GRU detector
│   └── risk_assessment/    # ESdE 2025 microdata (raw/) and the risk-level dataset (processed/)
├── models/                 # Trained and downloaded models, one folder per model
│   ├── fall_detection/     # GRU fall detectors (.keras)
│   ├── pose/               # MediaPipe pose landmarker models (.task)
│   └── risk_model/         # Patient risk-level model (Random Forest, .joblib)
├── docs/                   # Evaluation plots of both models and the UML diagram
├── src/
│   ├── main.py             # Entry point: main window, login and role-based navigation
│   ├── create_admin.py     # Command that creates administrator (tester) accounts
│   ├── paths.py            # Locations of the models, datasets and database (built from the project root)
│   ├── ai/                 # MediaPipe pose extractor and risk-level assessor
│   ├── controllers/        # Auth and monitoring controllers
│   ├── database/           # SQLite connection and Peewee models
│   ├── domain/             # Domain rules: user roles, password policy and the health questionnaire
│   ├── dtos/               # Data transfer objects between layers (immutable dataclasses)
│   ├── notifications/      # Alert e-mail (sender and template)
│   ├── repositories/       # Database access for users, patients and fall events
│   ├── navigation/         # Screen flow (AppCoordinator) and screen changes (Navigator)
│   ├── views/              # Screens, components, theme and stylesheet
│   └── workers/            # Video, inference and monitoring-strategy classes
├── training/
│   ├── fall_detection/
│   │   ├── build_fall_dataset.py       # Videos → pose sequences (.npy)
│   │   └── train_fall_model.py         # Trains and evaluates both GRU models
│   └── risk_assessment/
│       ├── build_risk_dataset_esde.py  # ESdE 2025 microdata → risk-assessment dataset (.csv)
│       └── train_risk_model.py         # Trains and evaluates the Random Forest risk model
└── requirements.txt        # Dependencies of the application and the training scripts
```

Created at runtime and ignored by Git: `app.db` (database) and `app.log` (log).

---

## Getting started

### Prerequisites

* **Python 3.11** (TensorFlow 2.18 supports 3.9 to 3.12)
* A webcam
* A Gmail account with 2-step verification and an
  [app password](https://myaccount.google.com/apppasswords) to send the alert e-mails
  (optional: without it the application works, but the e-mails fail). A dedicated account
  is recommended, because sent alerts stay in its "Sent" folder.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jalonf/fall-detection-system.git
   cd fall-detection-system
   ```

2. **Create and activate a virtual environment:**
   * Windows (PowerShell / Git Bash):
     ```bash
     python -m venv venv
     source venv/Scripts/activate
     ```
   * Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install the dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root:
   ```dotenv
   GMAIL_USER=your-account@gmail.com
   GMAIL_APP_PASSWORD=your-16-character-app-password
   # Optional: use the more accurate (and slower) pose model
   POSE_LANDMARKER_MODEL_PATH=models/pose/pose_landmarker_heavy.task
   ```

### Running the application

From the project root:

```bash
python -m src.main
```

The database is created on the first run. Sign up, fill in the patient's data and answer the health
questionnaire (it sets the patient's risk level), and press **Start monitoring**. The role decides the screen:

| Role | How the account is created | Screen |
|------|----------------------------|--------|
| Family / Caregiver | Sign-up form | Monitoring screen of their patient |
| Medical Staff | Sign-up form | Monitoring screen of their patient |
| Administrator | `python -m src.create_admin` | Test mode: test profiles, video upload, skeleton panel and telemetry |

#### Creating an administrator

Administrators are the application's testers. The sign-up form does not offer that role, so nobody
can give themselves the administration screen; create the account from the project root instead:

```bash
python -m src.create_admin
```

It asks for the name, the e-mail and the password (typed twice, hidden, with the same rules as the
sign-up form) and creates the account without a patient. Then sign in with it in the application.

---

## Training the models

The trained models are already in `models/fall_detection/`. To train them again:

1. Place the videos (`.mp4`) in `data/fall_detection/raw/VideoDataset/ADL/` (normal activities) and
   `data/fall_detection/raw/VideoDataset/Fall/` (falls). Subfolders are allowed.
2. Extract the pose sequences for both modes (written to `data/fall_detection/processed/`):
   ```bash
   python -m training.fall_detection.build_fall_dataset
   ```
3. Train and evaluate both models (written to `models/fall_detection/`, plots to `docs/`):
   ```bash
   python -m training.fall_detection.train_fall_model
   ```

`data/` is ignored by Git, except `data/README.md`, which describes its layout.

### Risk-assessment dataset

The patient's risk level comes from a Random Forest trained on the ESdE 2025 health survey (INE).
The microdata zip goes in `data/risk_assessment/raw/ESdEadulto_2025.zip`; then, from the project root:

```bash
python -m training.risk_assessment.build_risk_dataset_esde
```

This writes `data/risk_assessment/processed/risk_dataset_esde2025.csv` (people aged 65+, the 28
predictors that the application asks the patient, the targets and the survey weight) and a
`..._dictionary.csv` that explains every column. The survey has no question about falls, so the
targets are a proxy: accidents at home or during leisure time in the last 12 months.

Then train the Random Forest. It reports its cross-validated AUC and the observed event rate per risk
level, saves the confusion matrices in `docs/risk_assessment/` and stores the model, the questions it
expects and the limits of each level in `models/risk_model/risk_random_forest.joblib`:

```bash
python -m training.risk_assessment.train_risk_model
```

The application only needs that `.joblib` file. Questions are defined once in
`src/domain/questionnaire.py`; each one is a feature of the model.

---

## Code quality

```bash
pip install ruff
ruff check src/ training/
```

GitHub Actions installs the dependencies and runs the linter on every push and pull request
to `main` (`.github/workflows/ci.yml`).

### Docstrings

Every module, class and public function is documented in
[Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings): a one-line
summary, a blank line, the description and, where they help, `Args`, `Returns`, `Raises`, `Attributes`
and `Signals` (for Qt signals) sections. Types are not repeated: they are in the annotations. Comments
(`#`) explain *why* something is done, not what. Ruff checks the docstrings (`pyproject.toml`: rules
`D` with the Google convention), so the linter fails when one is missing or malformed.
