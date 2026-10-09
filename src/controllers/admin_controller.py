import logging
from datetime import datetime

from src.notifications.email_notifier import EmailNotifier
from src.workers.strategies import HighRiskStrategy, LowRiskStrategy, MonitoringStrategy
from src.workers.video_file_worker import VideoFileWorker
from src.workers.video_worker import VideoWorker

logger = logging.getLogger(__name__)

class AdminController:
    """
    Controller responsible for managing the administrative monitoring workflow, 
    camera threads, skeleton telemetry updates, and root-level video file processing.
    """
    
    def __init__(self, view, current_user, patient, on_logout_callback):
        self.view = view
        self.user = current_user
        self.patient = patient
        self.worker = None
        self.falls_count = 0

        self.view.notify_requested.connect(self.notify_user)
        self.view.start_requested.connect(self.start_camera)
        self.view.upload_requested.connect(self.start_video_file)
        self.view.stop_requested.connect(self.stop_camera)
        self.view.logout_requested.connect(on_logout_callback)
        
        logger.info("AdminController initialized for root administrator: %s", getattr(self.user, 'name', 'Unknown'))

    def _get_user_strategy(self) -> MonitoringStrategy:
        risk_level = getattr(self.patient, 'risk_level', 'LOW') if self.patient else 'LOW'
        
        if str(risk_level).upper() == "HIGH":
            logger.info("High baseline risk detected. Applying HighRiskStrategy.")
            return HighRiskStrategy()
        
        logger.info("Low/Default baseline risk detected. Applying LowRiskStrategy.")
        return LowRiskStrategy()

    def start_camera(self, camera_index):
        if self.worker is not None:
            logger.warning("Attempted to start camera stream, but a worker is already active.")
            return

        strategy = self._get_user_strategy()
        logger.info("Initializing admin camera worker with source index: %s", camera_index)
        self.worker = VideoWorker(camera_index=camera_index, strategy=strategy)
        
        # Wire up signals to both the video stream and the skeleton telemetry panel
        self.worker.frame_ready.connect(self.view.update_video_frame)
        self.worker.skeleton_frame_ready.connect(self.view.skeleton_panel.update_frame)
        self.worker.telemetry_data_ready.connect(self.view.skeleton_panel.update_telemetry)
        self.worker.fall_detected.connect(self.handle_fall_alert)
        
        self.worker.start()
        
        self.view.set_monitoring_state(True)
        logger.info("Admin stream connected (Source %s)", camera_index)
        self.view.log_event("INFO", f"Stream connected (Source {camera_index})")

    def start_video_file(self, file_path):
        if self.worker is not None:
            logger.warning("Attempted to process video file, but a worker is already active.")
            return

        logger.info("Initializing administrative video file worker for path: %s", file_path)
        self.worker = VideoFileWorker(video_path=file_path)
        
        # Wire up video and skeleton panel signals for file processing
        self.worker.frame_ready.connect(self.view.update_video_frame)
        self.worker.skeleton_frame_ready.connect(self.view.skeleton_panel.update_frame)
        self.worker.telemetry_data_ready.connect(self.view.skeleton_panel.update_telemetry)
        self.worker.fall_detected.connect(self.handle_fall_alert)
        
        if hasattr(self.worker, "playback_finished"):
            self.worker.playback_finished.connect(self.stop_camera)
            
        self.worker.start()
        
        filename = file_path.split("/")[-1].split("\\")[-1]
        self.view.set_monitoring_state(True)
        logger.info("Processing administrative video file: %s", filename)
        self.view.log_event("INFO", f"Processing video file: {filename}")

    def stop_camera(self):
        if not self.worker:
            logger.debug("Stop requested, but no active worker was found.")
            return

        logger.info("Stopping admin camera worker...")
        self.worker.stop()
        self.worker.wait()
        self.worker = None
        
        self.view.set_monitoring_state(False)
        logger.info("Stream disconnected")
        self.view.log_event("INFO", "Stream disconnected")
        self.view.clear_video()

    def handle_fall_alert(self, message):
        self.falls_count += 1
        logger.warning("Admin Fall detected: %s (Total falls: %d)", message, self.falls_count)
        
        self.view.update_fall_count(str(self.falls_count))
        self.view.trigger_fall_alert(message)
        self.view.log_event("ALERT", f"Fall detected: {message}")

    def notify_user(self):
        snapshot_file = None
        event_data = {
            "event_name": "fall_detected",
            "patient_name": getattr(self.patient, 'name', self.user.name),
            "medical_history": "N/A",
            "prediction_probability": 0.94,
            "timestamp": datetime.now().astimezone().strftime("%d/%m/%Y %H:%M:%S"),
            "snapshot_path": str(snapshot_file) if snapshot_file else None,
        }
        logger.info("Admin broadcast notification sent")
        email_notifier = EmailNotifier(self.user.email)
        email_notifier.update(event_data)