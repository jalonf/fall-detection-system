import os
from dotenv import load_dotenv
from src.notifications.email_notifier import EmailNotifier

load_dotenv()


def test_send_test_email():
    test_email = os.getenv("TEST_EMAIL","")

    notifier = EmailNotifier(email=test_email)

    event_data = {
        "event_name": "fall_detected",
        "patient_name": "Juan Pérez",
        "medical_history": "Hipertensión y antecedentes médicos.",
        "prediction_probability": 0.94,
        "timestamp": "08/09/2026 13:30:00",
        "snapshot_path": None,
    }

    notifier.update(event_data)


if __name__ == "__main__":
    test_send_test_email()