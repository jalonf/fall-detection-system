import logging
import os
from pathlib import Path

from dotenv import load_dotenv
import resend

from src.notifications.template import render_fall_alert_email
from src.patterns.observer import Observer

load_dotenv()

logger = logging.getLogger(__name__)


class EmailNotifier(Observer):

    def __init__(self, email: str):
        self.email = email
        self.api_key = os.getenv("RESEND_API_KEY", "")
        self.from_email = os.getenv(
            "RESEND_FROM_EMAIL", "Safeguard Alerts <onboarding@resend.dev>"
        )
        resend.api_key = self.api_key

    def update(self, event_data: dict) -> None:
        patient_name = event_data.get("patient_name", "Unknown Patient")
        timestamp = event_data.get("timestamp", "Recent")
        probability = float(event_data.get("prediction_probability", 0.0))
        medical_info = event_data.get("medical_history", "No medical records available.")

        # Resolve and validate image path cleanly
        snapshot_raw = event_data.get("snapshot_path")
        snapshot_file = Path(snapshot_raw) if snapshot_raw else None
        has_attachment = snapshot_file is not None and snapshot_file.is_file()

        # Build message bodies from the template
        plain_text, html_content = render_fall_alert_email(
            patient_name=patient_name,
            timestamp=timestamp,
            probability=probability,
            medical_info=medical_info,
            has_attachment=has_attachment,
        )

        # Build payload parameters
        params: resend.Emails.SendParams = {
            "from": self.from_email,
            "to": [self.email],
            "subject": f"Safeguard: Fall Alert - {patient_name}",
            "html": html_content,
            "text": plain_text,
        }

        # Attach image if valid
        if has_attachment and snapshot_file:
            try:
                with open(snapshot_file, "rb") as img:
                    params["attachments"] = [
                        {
                            "filename": snapshot_file.name,
                            "content": list(img.read()),
                        }
                    ]
            except OSError as err:
                logger.warning("Failed to read snapshot file for attachment: %s", err)

        # Dispatch via Resend API
        try:
            response = resend.Emails.send(params)
            logger.info("Alert email sent to %s (ID: %s)", self.email, response.get("id"))
        except Exception as err:  # noqa: BLE001
            logger.error("Failed to send email to %s via Resend: %s", self.email, err)