"""Every text of the interface (English), plus the rules that turn controller messages into toasts.

Overline texts are already written in upper case here; the stylesheet never transforms text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

EM_DASH = "—"


class Common:
    CANCEL = "Cancel"
    OPTIONAL = "Optional"
    SHOW_PASSWORD = "Show password"
    HIDE_PASSWORD = "Hide password"
    CLEAR_TEXT = "Clear text"
    UNEXPECTED_ERROR = "Something went wrong. Please try again."


class Brand:
    OVERLINE = "FALL RISK ASSESSMENT AND DETECTION"
    HEADLINE = "Continuous, private fall monitoring"
    PARAGRAPH = "For older adults, at home or in a care home."
    FEATURES = (
        ("activity", "Real-time fall detection",
         "Every second of movement is classified by a recurrent neural network."),
        ("eye-off", "Privacy by design", "The face is blurred before any frame is shown, stored or sent."),
        ("bell", "Immediate caregiver alert", "An e-mail with the capture is sent as soon as a fall is detected."),
    )
    FOOTER = "Trabajo de Fin de Grado · Universidad de León · 2026 · v1.0"


class Login:
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


class Register:
    BACK_TO_SIGN_IN = "Back to sign in"
    TITLE = "Create an account"
    SUBTITLE = "Five short steps. The health questions set the patient's risk level."
    STEPS = ("Caregiver", "Account", "Patient", "Daily life", "Health")
    BACK = "Back"
    CONTINUE = "Continue"
    CREATE = "Create account"
    CREATING = "Creating account…"
    STEP_OF = "Step {current} of {total}"

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
    PATIENT_NAME = "Patient full name"
    MEDICAL_NOTES = "Medical notes"
    MEDICAL_NOTES_PLACEHOLDER = "e.g. vertigo, reduced mobility"
    RISK_CALLOUT = "The patient's risk level is calculated from these answers when the account is created."

    NAME_REQUIRED = "Enter the caregiver's full name."
    PHONE_INVALID = "Enter a phone number with country code, e.g. +34 600 000 000."
    ROLE_REQUIRED = "Choose a role."
    EMAIL_INVALID = "Enter a valid email address."
    EMAIL_IN_USE = "This email is already in use."
    PASSWORD_WEAK = "Password doesn't meet all the requirements."
    PASSWORD_TOO_LONG = "Password is too long: use at most 72 characters (fewer with accents or emoji)."
    PASSWORD_MISMATCH = "Passwords don't match."
    PATIENT_REQUIRED = "Enter the patient's full name."
    CHOICE_REQUIRED = "Choose an answer."
    NUMBER_RANGE = "Enter a whole number between {minimum} and {maximum}."
    NUMBER_PLACEHOLDER = "{minimum}–{maximum}"


class Monitor:
    SECTION_MONITORING = "Patient Monitoring"
    SECTION_ADMIN = "Administration Monitoring"
    SIGN_OUT = "Sign out"
    SIGN_OUT_TIP = "Sign out (Ctrl+Shift+Q)"
    CLOCK_FORMAT = "ddd d MMM · HH:mm"

    PATIENT = "Patient"
    CAMERA = "Camera"
    STRIP_PATIENT = "PATIENT"
    STRIP_CAMERA = "CAMERA"
    STRIP_FILE = "VIDEO FILE"
    STRIP_STATUS = "STATUS"
    STRIP_DURATION = "DURATION"
    RISK_BADGE = "{level} RISK"
    CAMERA_SPEC = "{width} × {height} · {fps} fps"
    CAMERA_SPEC_TIP = "Resolution and frame rate set by the patient's {level} risk level"
    CAMERA_SPEC_DEFAULT_TIP = "No patient linked: the camera uses the {level} risk profile"
    FILE_SPEC = "Analysed at its own frame rate"

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

    OVERLAY_LIVE = "LIVE"
    OVERLAY_STANDBY = "STANDBY"

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
    TITLE = "Pose analysis"
    SUBTITLE = "33 landmarks"
    SKELETON = "SKELETON"
    NO_SIGNAL = "No signal"
    INFERENCE = "Inference"
    CONFIDENCE = "Confidence"
    HIP_HEIGHT = "Hip height"
    HIP_HEIGHT_TIP = "Normalised vertical position of the hip centre (0 = top of frame, 1 = bottom)"
    TREND_WINDOW = "Last 30 s"


class Toasts:
    """The only toasts the app shows: signed in, account created (TOAST_RULES) and signed out."""

    SIGNED_OUT_TITLE = "Signed out"
    SIGNED_OUT = "Your session has ended."
    KIND_TITLES: ClassVar[dict[str, str]] = {"success": "Done", "error": "Something went wrong", "warning": "Warning", "info": "Information"}


def event_count(shown: int, total: int) -> str:
    if shown != total:
        return Log.COUNT_FILTERED.format(shown=shown, total=total)
    return Log.COUNT_ONE if total == 1 else Log.COUNT_MANY.format(n=total)


# ---------------------------------------------------------------------- toast rules
@dataclass(frozen=True)
class ToastRule:
    """How a controller message becomes a toast.

    `source` is where the message arrives: "success" (`AuthView.show_success`) or the event type
    of `log_event` ("INFO" / "ERROR"). `key` is the controller's text, matched by `match`
    ("equals", "prefix" or "any"). `message` may use {text}, {source} and {level}.
    """

    source: str
    key: str
    match: str
    kind: str
    title: str
    message: str


TOAST_RULES: tuple[ToastRule, ...] = (
    ToastRule("success", "Welcome back", "prefix", "success", "Signed in", "Opening your dashboard…"),
    ToastRule("success", "Account created", "prefix", "success", "Account created",
              "Patient risk level: {level}. Opening your dashboard…"),
)

_RISK_LEVEL = re.compile(r"\b(LOW|MEDIUM|HIGH)\b")


def toast_rule_for(source: str, text: str) -> ToastRule | None:
    """First rule that matches a message, or None when the message only goes to the log."""
    for rule in TOAST_RULES:
        if rule.source != source:
            continue
        if rule.match == "any":
            return rule
        if rule.match == "equals" and text == rule.key:
            return rule
        if rule.match == "prefix" and text.startswith(rule.key):
            return rule
    return None


def risk_level_in(text: str) -> str:
    match = _RISK_LEVEL.search(text)
    return match.group(1) if match else EM_DASH


def check_toast_rules() -> list[str]:
    """Keys of TOAST_RULES that no longer appear in `src/controllers/*.py`. Empty when in sync."""
    controllers = Path(__file__).resolve().parents[1] / "controllers"
    source = "\n".join(path.read_text(encoding="utf-8") for path in sorted(controllers.glob("*.py")))
    return [rule.key for rule in TOAST_RULES if rule.key and rule.key not in source]
