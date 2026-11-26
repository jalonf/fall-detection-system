"""Every text of the interface (English).

Overline texts are already written in upper case here; the stylesheet never transforms text.
"""

from __future__ import annotations

from typing import ClassVar

EM_DASH = "—"


class Common:
    """Texts shared by several screens."""
    CANCEL = "Cancel"
    OPTIONAL = "Optional"
    SHOW_PASSWORD = "Show password"
    HIDE_PASSWORD = "Hide password"
    CLEAR_TEXT = "Clear text"
    UNEXPECTED_ERROR = "Something went wrong. Please try again."


class Brand:
    """Brand panel of the sign-in screens."""
    HEADLINE = "Continuous, private fall monitoring"
    PARAGRAPH = "For older adults, at home or in a care home."
    FEATURES = (
        ("activity", "Real-time fall detection",
         "Every second of movement is classified by a recurrent neural network."),
        ("eye-off", "Privacy by design", "The face is blurred before any frame is shown, stored or sent."),
        ("bell", "Immediate caregiver alert", "An e-mail with the capture is sent as soon as a fall is detected."),
    )
    FOOTER = "Trabajo de Fin de Grado · Universidad de León · 2026"


class Login:
    """Sign-in page."""
    TITLE = "Sign in"
    SUBTITLE = "Enter your account details to continue."
    EMAIL = "Email"
    EMAIL_PLACEHOLDER = "name@example.com"
    PASSWORD = "Password"
    SUBMIT = "Sign in"
    SUBMITTING = "Signing in…"
    NEW_HERE = "New to FallSense?"
    CREATE_ACCOUNT = "Create an account"
    EMAIL_REQUIRED = "Enter your email address."
    EMAIL_INVALID = "Enter a valid email address."
    PASSWORD_REQUIRED = "Enter your password."


class Form:
    """Questions of the health questionnaire."""
    CHOICE_REQUIRED = "Choose an answer."
    NUMBER_RANGE = "Enter a whole number between {minimum} and {maximum}."
    NUMBER_PLACEHOLDER = "{minimum}–{maximum}"


class Register:
    """Sign-up page: the caregiver's account only (patients are added afterwards)."""
    TITLE = "Create an account"
    SUBTITLE = "Your account as a caregiver. You add the people you look after next."
    CREATE = "Create account"
    CREATING = "Creating account…"
    HAVE_ACCOUNT = "Already have an account?"
    SIGN_IN = "Sign in"

    FULL_NAME = "Full name"
    PHONE = "Phone"
    PHONE_PLACEHOLDER = "+34 600 000 000"
    ROLE = "Role"
    EMAIL = "Email"
    EMAIL_PLACEHOLDER = "name@example.com"
    EMAIL_HELP = "Used to sign in and to receive fall alerts."
    PASSWORD = "Password"
    CONFIRM_PASSWORD = "Confirm password"
    CHECKLIST = (
        ("length", "8+ characters"),
        ("upper", "An uppercase letter"),
        ("number", "A number"),
        ("symbol", "A symbol"),
    )

    NAME_REQUIRED = "Enter your full name."
    PHONE_INVALID = "Enter a phone number with country code, e.g. +34 600 000 000."
    ROLE_REQUIRED = "Choose a role."
    EMAIL_INVALID = "Enter a valid email address."
    EMAIL_IN_USE = "This email is already in use."
    PASSWORD_WEAK = "Password doesn't meet all the requirements."
    PASSWORD_TOO_LONG = "Password is too long: use at most 72 characters (fewer with accents or emoji)."
    PASSWORD_MISMATCH = "Passwords don't match."


class PatientForm:
    """New patient form: who they are and the health questionnaire that sets their risk level."""
    BACK_TO_PATIENTS = "Patients"
    TITLE = "New patient"
    SUBTITLE = ("Answer every question about the person you look after. The answers set their risk level, "
                "which decides how closely the camera watches them.")
    CANCEL = "Cancel"
    ADD = "Add patient"
    ADDING = "Adding patient…"
    PATIENT_NAME = "Full name"
    PATIENT_REQUIRED = "Enter the patient's full name."
    MEDICAL_NOTES = "Medical notes"
    MEDICAL_NOTES_PLACEHOLDER = "e.g. vertigo, reduced mobility"
    PROGRESS = "{answered} of {total} answered"
    MISSING_ONE = "1 answer is missing"
    MISSING_MANY = "{n} answers are missing"
    SECTION_PROGRESS = "{answered} of {total}"
    SECTION_MISSING = "{n} missing"
    SECTION_DONE = "Complete"
    SECTION_OPTIONAL = "Tick all that apply"
    DISCARD_TITLE = "Discard this patient?"
    DISCARD_BODY = "The answers entered so far will be lost."
    DISCARD_ACTION = "Discard"


class Patients:
    """Patients page: the caregiver's patients, add and delete."""
    TITLE = "Patients"
    SUBTITLE = "The people you look after. Each one's risk level sets how the camera monitors them."
    COUNT_ONE = "1 patient"
    COUNT_MANY = "{n} patients"
    ADD = "Add patient"
    COLUMNS = ("NAME", "RISK", "FALLS", "LAST FALL", "ADDED")
    NO_FALLS = "No falls"
    DATE_FORMAT = "d MMM yyyy"
    DATE_TIME_FORMAT = "d MMM yyyy · HH:mm"
    DELETE_TIP = "Delete {name}"
    EMPTY_TITLE = "Add the person you look after"
    EMPTY_TEXT = "Monitoring starts once a patient is added. Their health answers set how the camera is used."
    CONFIRM_DELETE_TITLE = "Delete {name}?"
    CONFIRM_DELETE_BODY = "Their fall history ({falls}) is deleted with them. This cannot be undone."
    FALLS_NONE = "no stored falls"
    FALLS_ONE = "1 stored fall"
    FALLS_MANY = "{n} stored falls"
    CONFIRM_DELETE_ACTION = "Delete patient"
    ADDED_TITLE = "Patient added"
    ADDED = "{name} · risk level {level}."
    DELETED_TITLE = "Patient deleted"
    DELETED = "{name} and their fall history were deleted."


class Monitor:
    """Dashboards: top bar, session card, video panel and alerts."""
    TAB_MONITORING = "Live view"
    TAB_PATIENTS = "Patients"
    TAB_MONITORING_LOCKED = "Add a patient first"
    TAB_PATIENTS_LOCKED = "Stop monitoring to manage patients"
    ADMIN_TITLE = "Detection testing"      # the administrators' single page
    SIGN_OUT = "Sign out"
    SIGN_OUT_SHORTCUT = "Ctrl+Shift+Q"
    ACCOUNT_TIP = "Account"
    ACCOUNT_NAME = "{name}, {role}. Account menu"
    ACCOUNT_MENU = "Account menu"
    CLOCK_FORMAT = "ddd d MMM · HH:mm"

    CAMERA = "Camera"
    STRIP_PATIENT = "PATIENT"
    STRIP_CAMERA = "CAMERA"
    STRIP_FILE = "VIDEO FILE"
    STRIP_STATUS = "STATUS"
    STRIP_DURATION = "DURATION"
    RISK_BADGE = "{level} RISK"
    CAMERA_SPEC = "{width} × {height} · {fps} fps"
    CAMERA_SPEC_TIP = "Resolution and frame rate set by the patient's {level} risk level"
    CAMERA_SPEC_DEFAULT_TIP = "No patient selected: the camera uses the {level} risk profile"
    PATIENT_COMBO = "Patient"
    PATIENT_COMBO_TIP = "Patient being monitored. Their risk level sets the camera settings and the fall model."
    CAMERA_SPEC_TEST_TIP = "Resolution and frame rate of the {level} risk test profile"
    FILE_SPEC = "Analysed at its own frame rate"

    # Administrators (testers): no patient, a test profile instead, and nothing is stored or e-mailed.
    STRIP_TEST_PROFILE = "TEST PROFILE"
    TEST_PROFILES: ClassVar[dict[str, str]] = {"LOW": "Low risk", "MEDIUM": "Medium risk", "HIGH": "High risk"}
    TEST_PROFILE_COMBO = "Test profile"
    TEST_PROFILE_TIP = "Camera settings and fall model of a risk level. It applies the next time you start the camera."
    TEST_MODE_BADGE = "TEST MODE"
    TEST_MODE_TIP = "Falls are shown and logged here, but they are not stored and no e-mail is sent."

    STATUS_TEXT: ClassVar[dict[str, str]] = {
        "idle": "Stopped",
        "starting": "Starting…",
        "live": "Live",
        "stopping": "Stopping…",
        "error": "Source error",
        "finished": "Analysis finished",
        "alert": "Fall alert",
    }

    LIVE_VIDEO = "Live video"
    SUBTITLE_IDLE = "Select a source to begin"
    SUBTITLE_RUNNING = "Analysing {label}"
    SUBTITLE_ERROR = "Source unavailable"
    SUBTITLE_FINISHED = "Finished · {label}"

    CAMERAS = ("Camera 0", "Camera 1", "Camera 2")
    CAMERA_LABEL = "Camera {index}"
    SOURCE_COMBO = "Video source"
    ANALYSE_VIDEO = "Analyse video…"
    ANALYSE_VIDEO_TIP = "Analyse a video file (Ctrl+O)"
    FILE_DIALOG_TITLE = "Analyse a video file"
    FILE_DIALOG_FILTER = "Video files (*.mp4 *.avi *.mov *.mkv)"
    START = "Start monitoring"
    START_TIP = "Start monitoring (Ctrl+Enter)"
    STOP = "Stop monitoring"
    STOP_TIP = "Stop monitoring (Ctrl+Enter)"
    STOPPING = "Stopping…"


    PLACEHOLDER: ClassVar[dict[str, tuple[str, str]]] = {
        "idle": ("Monitoring stopped", "Choose a source and press Start monitoring."),
        "starting": ("Starting…", "Opening the source and loading the models."),
        "error": ("Source unavailable", ""),
        "finished": ("Analysis finished", "{label} · {duration}"),
    }
    TRY_AGAIN = "Try again"
    CAMERA_LOST = "The camera stopped sending images. Check that it is connected and not used by another app."

    STATUS_ALERT_COUNT = "Fall alert ×{n}"
    ACKNOWLEDGE = "Acknowledge"
    ACKNOWLEDGE_TIP = "Acknowledge the fall alert (Esc)"
    ALERT_ACKNOWLEDGED = "Alert acknowledged by the operator"

    CONFIRM_SIGN_OUT_TITLE = "Stop monitoring and sign out?"
    CONFIRM_SIGN_OUT_BODY = "Monitoring is running. Signing out stops the camera and the analysis."
    CONFIRM_SIGN_OUT_ACTION = "Stop and sign out"


class Log:
    """Event log panel."""
    TITLE = "Event log"
    COUNT_ONE = "1 event"
    COUNT_MANY = "{n} events"
    COUNT_FILTERED = "{shown} of {total} events"
    FILTERS = (("all", "All events"), ("alerts", "Alerts"), ("errors", "Errors"), ("info", "Info"))
    FILTER_NAME = "Filter events"
    MORE = "More log actions"
    EXPORT = "Export CSV…"
    CLEAR = "Clear log…"
    COLUMNS = ("Time", "Type", "Description")
    CSV_HEADER = ("time", "type", "description")
    EMPTY = "No events in this session"
    EMPTY_FILTERED = "No events match this filter."
    EXPORT_DIALOG_TITLE = "Export the event log"
    EXPORT_FILTER = "CSV files (*.csv)"
    EXPORT_FILE_NAME = "fallsense-events-{stamp}.csv"
    EXPORT_FAILED = "The event log could not be exported to {name}"
    CONFIRM_CLEAR_TITLE = "Clear the event log?"
    CONFIRM_CLEAR_BODY = (
        "This removes {n} events from this view. Fall events already stored are not affected."
    )
    CONFIRM_CLEAR_BODY_ONE = (
        "This removes 1 event from this view. Fall events already stored are not affected."
    )
    CONFIRM_CLEAR_ACTION = "Clear log"
    TABLE_NAME = "Events"


class Pose:
    """Pose analysis panel (administrators)."""
    TITLE = "Pose analysis"
    SUBTITLE = "33 landmarks"
    SKELETON = "SKELETON"
    NO_SIGNAL = "No signal"
    INFERENCE = "Inference"
    CONFIDENCE = "Confidence"
    HIP_HEIGHT = "Hip height"
    HIP_HEIGHT_TIP = "Normalised vertical position of the hip centre (0 = top of frame, 1 = bottom)"
    TREND_WINDOW = "Last 30 s"
    METRICS_EMPTY = "Inference time, confidence and hip height appear here while monitoring."


class Toasts:
    """Toasts of the sign-in screen: signed in, account created and signed out."""

    SIGNED_IN_TITLE = "Signed in"
    SIGNED_IN = "Opening your dashboard…"
    ACCOUNT_CREATED_TITLE = "Account created"
    ACCOUNT_CREATED = "Next, add the person you look after."
    SIGNED_OUT_TITLE = "Signed out"
    SIGNED_OUT = "Your session has ended."
    KIND_TITLES: ClassVar[dict[str, str]] = {"success": "Done", "error": "Something went wrong", "warning": "Warning", "info": "Information"}


def event_count(shown: int, total: int) -> str:
    """Returns the event log's counter text.

    Args:
        shown: Events that pass the filter.
        total: Events in the log.

    Returns:
        "3 events", or "2 of 3 events" while a filter hides some.
    """
    if shown != total:
        return Log.COUNT_FILTERED.format(shown=shown, total=total)
    return Log.COUNT_ONE if total == 1 else Log.COUNT_MANY.format(n=total)
