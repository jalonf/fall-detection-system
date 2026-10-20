# Real-Time Fall Detection System

A desktop application that watches a person through a camera and raises an alert when it
detects a fall. MediaPipe extracts the 3D pose of the person in every frame and a GRU
recurrent network classifies the last second of movement as a normal activity or a fall.
When a fall starts, the application stores a capture, records the event and e-mails the
caregiver.

Developed as a **Bachelor's Thesis (Trabajo de Fin de Grado, TFG)**.

---

## Features

* **Live monitoring** from a webcam, with the person's skeleton and bounding box drawn on the video.
* **Two detection modes** chosen from the patient's risk level (see [Risk levels](#risk-levels)).
* **Privacy:** the face is blurred before anything is displayed, stored or sent.
* **Fall alerts:** a capture of the fall is saved in `snapshots/`, the event is stored in the
  database and an e-mail with the capture is sent through [Resend](https://resend.com).
* **User accounts** (login and sign-up) with a patient linked to each caregiver.
* **Administrator view** with an extra skeleton panel, live telemetry (inference time, pose
  confidence, hip height) and the option to analyse an uploaded video file.

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
5. **Fall:** when the prediction changes to "fall", the capture is saved, a `FallEvent` is
   stored and the alert e-mail is sent in the background so the video does not stall.

### Risk levels

Each patient has a risk level, chosen at sign-up. It decides how the camera is configured and
which model is used (`src/workers/strategies.py`):

| Risk | Camera | Model window | Model file |
|------|--------|--------------|------------|
| LOW  | 640 × 480, 15 FPS  | 15 frames (1 s) | `assets/fall_gru_low_risk_15fps.keras` |
| HIGH | 1280 × 720, 30 FPS | 30 frames (1 s) | `assets/fall_gru_high_risk_30fps.keras` |

For an uploaded video the model is chosen from the file's own frame rate instead
(20 FPS or less → 15-frame model, otherwise the 30-frame model), because the model has to
match the speed of the frames it receives.

### Model

Both models share the same architecture, trained with Keras (`training/train.py`):

```text
Input (window, 99) → GRU(64) → Dropout(0.3) → Dense(32, ReLU) → Dense(1, sigmoid)
```

The confusion matrices and training curves are in `docs/high_risk_30fps/` and
`docs/low_risk_15fps/`.

---

## Architecture

The application follows **Model-View-Controller** on top of PySide6 (Qt):

* **Views** (`src/views/`): the login / sign-up screen (`AuthView`), the caregiver's monitoring
  screen (`MonitorView`) and the administrator's one (`AdminView`). `ViewRouter` switches
  between them with a cross-fade.
* **Controllers** (`src/controllers/`): `AuthController` handles login and sign-up.
  `BaseMonitorController` starts and stops the video workers and shows what they report;
  `MonitorController` and `AdminController` extend it.
* **Workers** (`src/workers/`): Qt threads that do the heavy work. `VideoWorker` reads the
  camera and `VideoFileWorker` an uploaded file; both share the pipeline in `BaseVideoWorker`.
  The monitoring strategies (Strategy pattern) hold the camera settings and the model of each
  risk level.
* **Persistence** (`src/database/`, `src/repositories/`): SQLite through the Peewee ORM, with
  the `User`, `Patient` and `FallEvent` models. Repositories are the only classes that query
  the database.
* **Notifications** (`src/notifications/`): builds and sends the alert e-mail.

---

## Repository structure

```text
fall-detection-system/
├── assets/                 # Trained GRU models (.keras) and MediaPipe pose models (.task)
├── docs/                   # Evaluation plots of both models and the UML diagram
├── src/
│   ├── main.py             # Entry point: main window, login and role-based navigation
│   ├── ai/                 # MediaPipe pose extractor
│   ├── controllers/        # Auth and monitoring controllers
│   ├── database/           # SQLite connection and Peewee models
│   ├── dtos/               # Data passed from the views to the controllers
│   ├── notifications/      # Alert e-mail (sender and template)
│   ├── repositories/       # Database access for users, patients and fall events
│   ├── router/             # Animated navigation between screens
│   ├── views/              # Screens, components, theme and stylesheet
│   └── workers/            # Video, inference and monitoring-strategy classes
├── training/
│   ├── preprocess.py       # Videos → pose sequences (.npy)
│   └── train.py            # Trains and evaluates both GRU models
├── tests/                  # pytest suite
├── requirements.txt        # Application dependencies
└── requirements-dev.txt    # Tests, linter and training dependencies
```

Created at runtime and ignored by Git: `app.db` (database), `app.log` (log) and `snapshots/`
(fall captures).

---

## Getting started

### Prerequisites

* **Python 3.11** (TensorFlow 2.18 supports 3.9 to 3.12)
* A webcam
* A [Resend](https://resend.com) API key to send the alert e-mails (optional: without it the
  application works, but the e-mails fail)

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
   To run the tests, the linter or the training scripts, install `requirements-dev.txt` instead.

4. **Create a `.env` file** in the project root:
   ```dotenv
   RESEND_API_KEY=your-resend-api-key
   RESEND_FROM_EMAIL=Safeguard Alerts <alerts@your-domain.com>
   # Optional: use the more accurate (and slower) pose model
   POSE_LANDMARKER_MODEL_PATH=assets/pose_landmarker_heavy.task
   ```

### Running the application

From the project root:

```bash
python -m src.main
```

The database is created on the first run. Sign up as **Family / Caregiver** or
**Medical Staff**, fill in the patient's data and risk level, and press **Start detection**.

Administrator accounts cannot be created from the sign-up form. To turn an existing account
into an administrator:

```bash
python -c "from src.database.models.user import User; User.update(role='Administrator').where(User.email == 'you@example.com').execute()"
```

---

## Training the models

The trained models are already in `assets/`. To train them again:

1. Place the videos (`.mp4`) in `fall_dataset/ADL/` (normal activities) and
   `fall_dataset/Fall/` (falls). Subfolders are allowed.
2. Extract the pose sequences for both modes (written to `processed_features/`):
   ```bash
   python -m training.preprocess
   ```
3. Train and evaluate both models (written to `assets/`, plots to `docs/`):
   ```bash
   python -m training.train
   ```

`fall_dataset/` and `processed_features/` are ignored by Git.

---

## Tests and code quality

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
ruff check src/ training/ tests/
```

The tests do not need a camera: the database tests use an in-memory SQLite database and the
camera is replaced by a fake object. GitHub Actions runs the linter and the tests on every
push and pull request to `main` (`.github/workflows/ci.yml`).
