import logging
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

from src.notifications.template import render_fall_alert_email
from src.patterns.observer import Observer

load_dotenv()

logger = logging.getLogger(__name__)

class EmailNotifier(Observer):

    def __init__(self, email: str):
        self.email = email
        self.server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASSWORD", "")

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

        # Build email structure
        msg = EmailMessage()
        msg["Subject"] = f"Safeguard: Fall Alert - {patient_name}"
        msg["From"] = f"Safeguard Alerts <{self.user}>"
        msg["To"] = self.email
        msg.set_content(plain_text)
        msg.add_alternative(html_content, subtype="html")

        # Attach image if valid
        if has_attachment and snapshot_file:
            try:
                with open(snapshot_file, "rb") as img:
                    msg.add_attachment(
                        img.read(),
                        maintype="image",
                        subtype="jpeg",
                        filename=snapshot_file.name,
                    )
            except OSError as err:
                print(f"Warning: Failed to attach snapshot ({err})")

        # Dispatch
        try:
            with smtplib.SMTP(self.server, self.port) as client:
                client.starttls()
                client.login(self.user, self.password)
                client.send_message(msg)
            logger.info("Alert email sent to: %s" , self.email)
        except Exception as err:  # noqa: BLE001
            logger.error("Failed to send email to %s : %s",self.email, err)