import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.notifications.email_notifier import EmailNotifier

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_send_test_email(tmp_path: Path | None = None) -> None:
    test_email = os.getenv("TEST_EMAIL", "").strip()
    api_key = os.getenv("RESEND_API_KEY", "").strip()

    if not api_key:
        logger.error("Missing RESEND_API_KEY in environment or .env file")
        sys.exit(1)

    if not test_email:
        logger.error("Missing TEST_EMAIL in environment or .env file")

    snapshot_file = None
    if tmp_path is not None:
        snapshot_file = tmp_path / "test_snapshot.jpg"
        snapshot_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 32)

    notifier = EmailNotifier(email=test_email)

    event_data = {
        "event_name": "fall_detected",
        "patient_name": "Juan Pérez",
        "medical_history": "Hipertensión y antecedentes médicos.",
        "prediction_probability": 0.94,
        "timestamp": "08/09/2026 13:30:00",
        "snapshot_path": str(snapshot_file) if snapshot_file else None,
    }

    logger.info("Sending test email to %s...", test_email)
    notifier.update(event_data)


if __name__ == "__main__":
    test_send_test_email()