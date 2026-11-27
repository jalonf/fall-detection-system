# Vigía · Fall risk assessment and detection

**Vigía** is a desktop application that watches a person through a camera and raises an
alert when it detects a fall. MediaPipe extracts the 3D pose of the person in every frame and a GRU
recurrent network classifies the last second of movement as a normal activity or a fall.
When a fall starts, the application records the event and e-mails the caregiver with a
capture of the fall.

Developed as a **Bachelor's Thesis (Trabajo de Fin de Grado, TFG)**.

---

## Features

* **Live monitoring** from a webcam, with the person's skeleton and bounding box drawn on the video.
* **Three detection modes** chosen from the patient's risk level, which is calculated when the patient
  is added, from a short health questionnaire (see [Risk levels](#risk-levels)).
* **Privacy:** the face is blurred before anything is displayed, stored or sent.
* **Fall alerts:** the event is stored in the database and an e-mail with a capture of the fall
  is sent through Gmail (SMTP). The capture only lives in memory: it is never written to disk.
* **User accounts** (login and sign-up) and **patient management**: each caregiver adds, lists and
  deletes the people they look after (Patients tab) and picks which one to monitor (Live view tab).
* **Administrator (tester) view**: no patient and a **test mode** in which falls are shown and logged
  but never stored or e-mailed. The tester picks the camera's test profile (the settings and model of a
  risk level), analyses uploaded video files and sees an extra skeleton panel and live telemetry
  (inference time, pose confidence, hip height). Administrators cannot sign up from the application;
  they are created from the command line (see [Running the application](#running-the-application)).

---

## How it works

The work is split in three threads besides the interface (all in `src/threads/`), so none of them
ever waits for another. The monitoring controller creates, connects and stops the three of them at
every "Start" / "Stop". Each thread is named after its job, and the log shows which one wrote each line:

1. **Video thread** (`VideoThread`, `video-thread`; it reads a camera or a video file), for every frame:
   * **Pose:** `MediaPipeExtractor` returns the 33 body landmarks in 3D (meters), centred on the
     midpoint of the hips so the position of the person in the room does not matter, plus the
     2D landmarks used for drawing.
   * **Privacy:** the face area is blurred.
   * **Hand-over:** the pose (33 × 3 = 99 values) goes to the fall detection thread through a queue.
   * **Drawing and telemetry:** skeleton, bounding box (red during a fall) and the
     administrator's telemetry; the frame goes to the interface through a one-slot mailbox.
2. **Fall detection thread** (`FallDetectionThread`, `fall-detection-thread`): loads the GRU while
   MediaPipe loads in the video thread. It samples the poses at the model's frame rate, so the
   sliding window always covers one second of real time, and runs the GRU on the newest window.
   If the model is slower than the frames arrive, the waiting poses are added at once and only the
   newest window is analysed, so detection never lags behind. A fall starts when the
   probability reaches 0.6 and ends when it drops below 0.4 (hysteresis), so a probability
   hovering around the threshold is one fall, not many.
3. **Alert thread** (`AlertThread`, `alert-thread`): when a fall starts, the controller hands it over; this thread
   stores the `FallEvent` and e-mails the caregiver with the capture (encoded in memory) attached.
   Every fall is stored, but at most one e-mail goes out per minute.

### Risk levels

Each patient has a risk level, calculated when the caregiver adds them. The caregiver answers a health
questionnaire about the patient (`src/domain/questionnaire.py`: age, mobility, pain, conditions, medication...) and a
Random Forest (`src/ai/risk_assessor.py`) turns the answers into LOW, MEDIUM or HIGH. The patient must be
65 or older, the ages the model was trained on. If the model cannot be used, the patient is
registered as HIGH, the strictest level. The level decides how the camera is
configured and which model is used (`src/domain/monitoring_profiles.py`):

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

They are evaluated **by subject**: the people recorded are split into 5 groups and each group is
predicted by a model trained without any of their videos, so the results measure how the models
work with people they have never seen. Each test video is also replayed one pose at a time with the
application's hysteresis, which gives the share of falls that raise an alarm and of normal
activities that raise a false one. The report (`evaluation.json`), the confusion matrices and the
training curves are in `docs/high_risk_30fps/` and `docs/low_risk_15fps/`.

Results by subject (mean ± standard deviation over the 5 groups; 29 subjects, 2,013 videos):

| | 30 FPS model | 15 FPS model |
|---|---|---|
| Window accuracy | 0.906 ± 0.019 | 0.918 ± 0.006 |
| Window precision / recall | 0.927 / 0.881 | 0.942 / 0.889 |
| Window ROC AUC | 0.956 ± 0.011 | 0.968 ± 0.010 |
| Fall videos that raise an alarm | 98.1 % | 98.8 % |
| Normal-activity videos that raise a false alarm | 12.6 % | 11.5 % |

The clips are short (about 1.9 s) and the normal activities include movements that resemble a fall,
so the false-alarm share is per clip, not per hour of real monitoring.

---

## Architecture

The application follows **Model-View-Controller** on top of PySide6 (Qt):

* **Views** (`src/views/`): the login / sign-up screen (`AuthView`) and one dashboard per role
  (`dashboard_view.py`). A dashboard is a shell: the top bar (the application's mark, the tabs, the
  date and the account menu) over sibling pages that do not know about each other. The caregiver's
  (`CaregiverDashboardView`) has a Live view page (`MonitorView`) and a Patients page
  (`PatientsPage`), and applies the rules that link them (the patient list fills the monitoring
  selector, Patients is locked while monitoring runs); the administrator's (`AdminDashboardView`) has
  only its monitoring page (`AdminView`), titled "Detection testing". Sign-in and sign-up are single
  pages built the same way; the new patient form is one page of section cards generated from the
  questionnaire (`src/domain/questionnaire.py`), with a fixed bar that shows how much is answered.
  Every colour, size and animation timing comes from the design tokens in `src/views/theme.py`.
* **Navigation** (`src/navigation/`, Application Controller / Coordinator pattern): `AppCoordinator`
  owns the flow (sign-in → the dashboard of the user's role → sign-out) and builds each screen (a view
  and one controller per page); views and controllers only report events and never open screens
  themselves. `Navigator` shows one screen at a time with a cross-fade and owns their life cycle: it
  stops the controllers of the screen being left (releasing the camera) and destroys its view.
* **Controllers** (`src/controllers/`): `AuthController` handles login and sign-up (the account
  only). `PatientsController` lists, adds (calculating the risk level) and deletes the caregiver's
  patients.
  `BaseMonitorController` creates, connects and stops the three threads of each monitoring, shows
  what they report and hands each fall to the alert thread; `MonitorController` and
  `AdminController` extend it. `MonitorController` monitors the patient chosen in the view and owns
  the `PatientsController`.
  `AdminController` only accepts administrators and runs everything in test mode (no alert
  thread, so nothing is stored or sent).
* **Threads** (`src/threads/`): the three threads that do the heavy work. `VideoThread` reads the
  camera or an uploaded file, `FallDetectionThread` runs the model on its poses, and `AlertThread`
  stores each fall and sends the alert e-mail. The monitoring strategies (Strategy pattern, `src/domain/monitoring_profiles.py`) hold
  the camera settings and the model of each risk level.
* **Persistence** (`src/database/`, `src/repositories/`): SQLite through the Peewee ORM, with
  the `User`, `Patient` and `FallEvent` models. Repositories are the only classes that query
  the database. Every account, administrators included, is a `User` row with a role (role-based
  access): the role decides the screen and the permissions, and the table only accepts the roles
  defined in `src/domain/roles.py`. Administrators simply have no `Patient`.
* **Notifications** (`src/notifications/`): `EmailNotifier` and the template build and send the
  alert e-mail (the `AlertThread` uses them).

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
├── docs/                   # Evaluation plots of both models
├── src/
│   ├── main.py             # Entry point: main window, login and role-based navigation
│   ├── create_admin.py     # Command that creates administrator (tester) accounts
│   ├── paths.py            # Locations of the models, datasets and database (built from the project root)
│   ├── ai/                 # MediaPipe pose extractor, GRU fall model and risk-level assessor
│   ├── controllers/        # Auth and monitoring controllers
│   ├── database/           # SQLite connection and Peewee models
│   ├── domain/             # Domain rules: roles, password policy, questionnaire, monitoring strategies
│   ├── dtos/               # Data transfer objects between layers (immutable dataclasses)
│   ├── notifications/      # Alert e-mail (sender and template)
│   ├── repositories/       # Database access for users, patients and fall events
│   ├── navigation/         # Screen flow (AppCoordinator) and screen changes (Navigator)
│   ├── threads/            # VideoThread (camera / file), FallDetectionThread, AlertThread
│   └── views/              # Screens, components, theme and stylesheet
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

The database is created on the first run. Sign up (the caregiver's account), add a patient in the
**Patients** tab answering the health questionnaire (it sets the patient's risk level), choose them in
the **Live view** tab and press **Start monitoring**. Monitoring stays locked until there is at least
one patient. The role decides the screen:

| Role | How the account is created | Screen |
|------|----------------------------|--------|
| Family / Caregiver | Sign-up form | Live view and Patients tabs (any number of patients) |
| Medical Staff | Sign-up form | Live view and Patients tabs (any number of patients) |
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

1. Download `VideoDataset.zip` from the [Video-Based Fall Detection Dataset](https://doi.org/10.6084/m9.figshare.28596332)
   (see [Datasets](#datasets)) and place its videos (`.mp4`) in `data/fall_detection/raw/VideoDataset/ADL/`
   (normal activities) and `data/fall_detection/raw/VideoDataset/Fall/` (falls). Subfolders are allowed.
2. Extract the pose sequences for both modes (written to `data/fall_detection/processed/`, with
   the subject and video of every window):
   ```bash
   python -m training.fall_detection.build_fall_dataset
   ```
3. Evaluate both models by subject and train them (written to `models/fall_detection/`, report and
   plots to `docs/`); `--evaluate-only` runs the evaluation and keeps the saved models:
   ```bash
   python -m training.fall_detection.train_fall_model
   ```

`data/` is ignored by Git, except `data/README.md`, which describes its layout.

### Risk-assessment dataset

The patient's risk level comes from a Random Forest trained on the ESdE 2025 health survey (INE, see
[Datasets](#datasets)). The microdata zip goes in `data/risk_assessment/raw/ESdEadulto_2025.zip`; then, from the project root:

```bash
python -m training.risk_assessment.build_risk_dataset_esde
```

This writes `data/risk_assessment/processed/risk_dataset_esde2025.csv` (people aged 65+, the 28
predictors that the application asks the patient, the targets and the survey weight) and a
`..._dictionary.csv` that explains every column. The survey has no question about falls, so the
model learns a proxy: an accident at home in the last 12 months, the closest the survey gets to a
fall at home.

Then train the Random Forest. It reports its cross-validated AUC and the observed event rate per risk
level, saves the confusion matrices in `docs/risk_assessment/` and stores the model, the questions it
expects and the limits of each level in `models/risk_model/risk_random_forest.joblib`:

```bash
python -m training.risk_assessment.train_risk_model
```

The levels are percentiles of the cross-validated probabilities: the lowest 50 % of the people are
LOW, the next 30 % MEDIUM and the highest 20 % HIGH. Current results (5-fold cross-validation,
6,396 people, 442 with an accident at home):

| | |
|---|---|
| AUC | 0.779 |
| People with an accident at home: LOW / MEDIUM / HIGH | 2.1 % / 6.9 % / 19.0 % |
| Accidents caught by flagging MEDIUM or HIGH | 85 % (specificity 53 %) |
| Accidents caught by flagging HIGH only | 55 % (specificity 83 %) |

The questions that weigh most are the difficulty to shower, to do heavy housework, to get up from a
chair, to walk 500 m and to climb stairs, then age. Two decisions were checked against the data:

* **Target.** With the same model and folds, an accident at home (AUC 0.779) separates the levels
  better than an accident at home or during leisure time (0.726) or than any accident or permanent
  injury from one (0.712), which mix in active people's leisure injuries and old accidents.
* **Questions.** 32 more ESdE variables (dementia, body mass index, social support, alcohol, help
  received, the other daily activities...) were added one by one to the 28 questions and compared
  over 15 folds: none improved the AUC by more than 0.003, so the questionnaire stays at 28 questions.

The survey measures the answers and the accidents at the same time, so the model identifies the
profile of the older people who have had an accident at home; it is a screening of how closely to
monitor them, not a prediction of future falls.

The application only needs that `.joblib` file. Questions are defined once in
`src/domain/questionnaire.py`; each one is a feature of the model.

---

## Datasets

Neither dataset is redistributed in this repository (`data/` is ignored by Git): download them from
their sources. The trained models in `models/` were derived from them.

### Fall detection: Video-Based Fall Detection Dataset

> Ursul, Ivan (2025). *Video-Based Fall Detection Dataset with 2017 Activities from 29 Subjects*.
> figshare. Dataset. https://doi.org/10.6084/m9.figshare.28596332.v2

* **Content:** video recordings of 29 subjects: 999 falls (to the left, right, front and back, while
  trying to sit down, from a height...) and 1,017 activities of daily living (walking, running,
  getting up from the floor...).
* **Licence:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
* **Changes made:** the videos were not modified or redistributed. They were subsampled to 15 and
  30 FPS and converted into one-second windows of MediaPipe 3D poses to train the GRU fall models
  (`training/fall_detection/build_fall_dataset.py`).

### Fall-risk assessment: ESdE 2025 (INE)

> Ministerio de Sanidad and Instituto Nacional de Estadística (INE). *Encuesta de Salud de España
> (ESdE) 2025*, adult questionnaire microdata (`ESdEadulto_2025.zip`).
> https://www.sanidad.gob.es/estadEstudios/estadisticas/encuestaSaludEspana/home_2025.htm

* **Content:** 21,641 respondents, 6,456 of them aged 65 or more.
* **Use:** the respondents aged 65+ and 28 of their answers train the risk model. The survey has no
  question about falls, so the target is a proxy: an accident at home in the last 12 months (see
  `data/README.md`).
* **Terms:** any publication obtained from the microdata must cite the Ministerio de Sanidad and the
  INE as the source of the primary data.

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
