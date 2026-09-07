import mimetypes
import smtplib
from email.message import EmailMessage
from src.views.theme import Colors
from src.patterns.observer import Observer


class EmailNotifier(Observer):

    def __init__(self, email: str, smtp_config: dict):
        self.email = email
        self.config = smtp_config

    def update(self, event_data: dict) -> None:
        """event_data must contain:

        - event_name: str
        - patient_name: str
        - medical_history: str
        - snapshot_path: str (path to the fall snapshot image)
        - prediction_probability: float
        - timestamp: str or datetime
        """
        msg = EmailMessage()
        msg["Subject"] = (
            f"⚠️ Fall Alert: {event_data.get('patient_name', 'Patient')}"
        )
        msg["From"] = self.config["user"]
        msg["To"] = self.email

        # Extract event and patient details
        patient_name = event_data.get("patient_name", "Unknown Patient")
        medical_info = event_data.get(
            "medical_history", "No additional medical records available."
        )
        timestamp = event_data.get("timestamp", "Recent")
        probability = event_data.get("prediction_probability", 0.0)
        snapshot_path = event_data.get("snapshot_path")

        # Plain text fallback message
        plain_message = (
            f"WARNING: Fall detected for patient {patient_name}.\n"
            f"Timestamp: {timestamp}\n"
            f"Confidence: {probability * 100:.1f}%\n"
            f"Medical Notes: {medical_info}\n"
        )
        msg.set_content(plain_message)

        # HTML content synchronized with the app's Colors design tokens
        html_content = f"""
        <html>
          <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: {Colors.BACKGROUND}; color: {Colors.TEXT_BODY}; padding: 20px; margin: 0;">
            <div style="max-width: 600px; background: {Colors.SURFACE}; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); margin: 0 auto; border: 1px solid {Colors.BORDER};">
              
              <!-- Safeguard Header Style -->
              <div style="background-color: {Colors.SURFACE}; padding: 24px; border-bottom: 2px solid {Colors.BORDER}; text-align: left;">
                <h2 style="margin: 0; color: {Colors.TEXT_MAIN}; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">Safeguard</h2>
                <p style="margin: 4px 0 0 0; color: {Colors.PRIMARY}; font-size: 13px; font-weight: 600; text-transform: uppercase;">Pose Analytics & Fall Detection System</p>
              </div>

              <!-- Main Alert Content -->
              <div style="padding: 24px;">
                <div style="background-color: {Colors.DANGER_SOFT}; border-left: 4px solid {Colors.DANGER}; border: 1px solid {Colors.DANGER_BORDER}; padding: 12px 16px; margin-bottom: 20px; border-radius: 4px;">
                  <p style="margin: 0; color: {Colors.DANGER}; font-weight: 700; font-size: 15px;">Critical Alert: Fall Event Detected</p>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                  <tr>
                    <td style="padding: 8px 0; color: {Colors.TEXT_MUTED}; font-size: 14px; width: 40%;">Patient Name:</td>
                    <td style="padding: 8px 0; color: {Colors.TEXT_MAIN}; font-size: 14px; font-weight: 600;">{patient_name}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px 0; color: {Colors.TEXT_MUTED}; font-size: 14px;">Timestamp:</td>
                    <td style="padding: 8px 0; color: {Colors.TEXT_MAIN}; font-size: 14px;">{timestamp}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px 0; color: {Colors.TEXT_MUTED}; font-size: 14px;">Confidence Level:</td>
                    <td style="padding: 8px 0; color: {Colors.TEXT_MAIN}; font-size: 14px;">{probability * 100:.1f}%</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px 0; color: {Colors.TEXT_MUTED}; font-size: 14px; vertical-align: top;">Medical Data:</td>
                    <td style="padding: 8px 0; color: {Colors.TEXT_MAIN}; font-size: 14px;">{medical_info}</td>
                  </tr>
                </table>
              </div>

              <!-- Footer -->
              <div style="background-color: {Colors.SURFACE_ALT}; padding: 16px 24px; text-align: center; border-top: 1px solid {Colors.BORDER};">
                <p style="margin: 0; font-size: 12px; color: {Colors.TEXT_MUTED};">Powered by MediaPipe & PySide6</p>
              </div>

            </div>
          </body>
        </html>
        """

        # Attach HTML version alternative
        msg.add_alternative(html_content, subtype="html")

        # Attach the fall snapshot if path is provided
        if snapshot_path:
            try:
                with open(snapshot_path, "rb") as f:
                    file_data = f.read()
                    file_name = snapshot_path.split("/")[-1].split("\\")[-1]

                msg.add_attachment(
                    file_data,
                    maintype="image",
                    subtype="jpeg",
                    filename=file_name,
                )
            except Exception as img_err:
                print(f"Failed to attach fall snapshot image: {img_err}")

        # Send email via SMTP server
        try:
            with smtplib.SMTP(
                self.config["server"], self.config["port"]
            ) as server:
                server.starttls()
                server.login(self.config["user"], self.config["password"])
                server.send_message(msg)
            print(f"Alert email successfully sent to {self.email}")
        except Exception as e:
            print(f"Error sending email to {self.email}: {e}")