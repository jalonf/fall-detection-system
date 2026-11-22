"""Sends the fall-alert e-mail through Gmail (SMTP over TLS)."""

import logging
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

from src.dtos.fall_alert import FallAlert
from src.notifications.template import BRAND_NAME, render_fall_alert_email

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465   # implicit TLS
SMTP_TIMEOUT = 15


class EmailNotifier:
    """Sends the fall alert through Gmail SMTP using an app password (see README).

    Args:
        email: Recipient of the alerts (the caregiver's account e-mail).
    """

    def __init__(self, email: str):
        self.email = email
        self.gmail_user = os.getenv("GMAIL_USER", "")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")

    def send(self, alert: FallAlert) -> bool:
        """Sends the fall-alert e-mail, with the capture attached when there is one.

        Args:
            alert: What to tell the caregiver.

        Returns:
            True when Gmail accepted the e-mail; False when it could not be sent (or the Gmail
            credentials are not configured).
        """
        if not self.gmail_user or not self.gmail_app_password:
            logger.error("GMAIL_USER / GMAIL_APP_PASSWORD are not set: the alert e-mail was not sent")
            return False

        plain_text, html_content = render_fall_alert_email(
            patient_name=alert.patient_name,
            timestamp=alert.timestamp,
            probability=alert.probability,
            medical_info=alert.medical_notes,
            has_attachment=bool(alert.snapshot),
        )

        msg = EmailMessage()
        msg["From"] = f"{BRAND_NAME} Alerts <{self.gmail_user}>"   # Gmail only allows the account itself
        msg["To"] = self.email
        msg["Subject"] = f"{BRAND_NAME}: Fall Alert - {alert.patient_name}"
        msg.set_content(plain_text)
        msg.add_alternative(html_content, subtype="html")
        if alert.snapshot:
            msg.add_attachment(alert.snapshot, maintype="image", subtype="jpeg", filename="fall.jpg")

        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as smtp:
                smtp.login(self.gmail_user, self.gmail_app_password)
                smtp.send_message(msg)
            logger.info("Alert email sent to %s", self.email)
            return True
        except (smtplib.SMTPException, OSError) as err:
            logger.error("Failed to send email to %s via Gmail: %s", self.email, err)
            return False
