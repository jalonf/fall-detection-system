"""Sends the fall-alert e-mail through Gmail (SMTP over TLS)."""

import logging
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

from src.notifications.template import BRAND_NAME, render_fall_alert_email

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465   # implicit TLS
SMTP_TIMEOUT = 15


def fall_event_data(patient, user, probability: float, timestamp: str, snapshot: bytes | None) -> dict:
    """Builds the dictionary `EmailNotifier.update` expects from a fall.

    `snapshot` is the JPEG of the incident frame, kept only in memory (never written to disk).
    """
    return {
        "event_name": "fall_detected",
        "patient_name": getattr(patient, "name", None) or user.name,
        "medical_history": getattr(patient, "medical_notes", None) or "N/A",
        "prediction_probability": probability,
        "timestamp": timestamp,
        "snapshot": snapshot,
    }


class EmailNotifier:
    """Sends the fall alert through Gmail SMTP using an app password (see README)."""

    def __init__(self, email: str):
        self.email = email
        self.gmail_user = os.getenv("GMAIL_USER", "")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")

    def update(self, event_data: dict) -> bool:
        """Sends the fall alert. Returns True when Gmail accepted the e-mail."""
        if not self.gmail_user or not self.gmail_app_password:
            logger.error("GMAIL_USER / GMAIL_APP_PASSWORD are not set: the alert e-mail was not sent")
            return False

        patient_name = event_data.get("patient_name", "Unknown Patient")
        snapshot = event_data.get("snapshot")   # bytes | None

        plain_text, html_content = render_fall_alert_email(
            patient_name=patient_name,
            timestamp=event_data.get("timestamp", "Recent"),
            probability=float(event_data.get("prediction_probability", 0.0)),
            medical_info=event_data.get("medical_history", "No medical records available."),
            has_attachment=bool(snapshot),
        )

        msg = EmailMessage()
        msg["From"] = f"{BRAND_NAME} Alerts <{self.gmail_user}>"   # Gmail only allows the account itself
        msg["To"] = self.email
        msg["Subject"] = f"{BRAND_NAME}: Fall Alert - {patient_name}"
        msg.set_content(plain_text)
        msg.add_alternative(html_content, subtype="html")
        if snapshot:
            msg.add_attachment(snapshot, maintype="image", subtype="jpeg", filename="fall.jpg")

        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as smtp:
                smtp.login(self.gmail_user, self.gmail_app_password)
                smtp.send_message(msg)
            logger.info("Alert email sent to %s", self.email)
            return True
        except (smtplib.SMTPException, OSError) as err:
            logger.error("Failed to send email to %s via Gmail: %s", self.email, err)
            return False
