import logging

from src.core.video_file_worker import VideoFileWorker
from src.core.video_worker import VideoWorker

FALL_ALERT_COOLDOWN_S = 3.0

logger = logging.getLogger(__name__)

class MonitorController:
    """
    Controller responsible for managing the video monitoring workflow, 
    camera threads, and handling fall detection events in real time.
    """
    
    def __init__(self, view, current_user, on_logout_callback):
        self.view = view
        self.user = current_user
        self.worker = None
        self.falls_count = 0
        self._last_fall_ts = 0.0
        
        self.view.start_requested.connect(self.start_camera)
        self.view.upload_requested.connect(self.start_video_file)
        self.view.stop_requested.connect(self.stop_camera)
        self.view.logout_requested.connect(on_logout_callback)
        
        logger.info("MonitorController initialized for user: %s", getattr(self.user, 'name', 'Unknown'))

    def start_camera(self, camera_index):
        if self.worker is not None:
            logger.warning("Attempted to start camera stream, but a worker is already active.")
            return

        logger.info("Initializing camera worker with source index: %s", camera_index)
        self.worker = VideoWorker(camera_index=camera_index)
        self.worker.frame_ready.connect(self.view.update_video_frame)
        self.worker.skeleton_frame_ready.connect(self.view.skeleton_panel.update_frame)
        self.worker.telemetry_data_ready.connect(self.view.skeleton_panel.update_telemetry)
        self.worker.fall_detected.connect(self.handle_fall_alert)
        self.worker.start()
        
        self.view.set_monitoring_state(True)
        logger.info("Stream connected (Source %s)", camera_index)
        self.view.log_event("INFO", f"Stream connected (Source {camera_index})")

    def start_video_file(self, file_path):
        """Starts the worker responsible for processing an uploaded video file."""
        if self.worker is not None:
            logger.warning("Attempted to process video file, but a worker is already active.")
            return

        logger.info("Initializing video file worker for path: %s", file_path)
        self.worker = VideoFileWorker(video_path=file_path)
        self.worker.frame_ready.connect(self.view.update_video_frame)
        self.worker.skeleton_frame_ready.connect(self.view.skeleton_panel.update_frame)
        self.worker.telemetry_data_ready.connect(self.view.skeleton_panel.update_telemetry)
        self.worker.fall_detected.connect(self.handle_fall_alert)
        
        if hasattr(self.worker, "playback_finished"):
            self.worker.playback_finished.connect(self.stop_camera)
            
        self.worker.start()
        
        filename = file_path.split("/")[-1].split("\\")[-1]
        self.view.set_monitoring_state(True)
        logger.info("Processing video file: %s", filename)
        self.view.log_event("INFO", f"Processing video file: {filename}")

    def stop_camera(self):
        if not self.worker:
            logger.debug("Stop requested, but no active worker was found.")
            return

        logger.info("Stopping camera worker and disconnecting signals...")
        try:
            self.worker.frame_ready.disconnect()
            self.worker.skeleton_frame_ready.disconnect()
            self.worker.telemetry_data_ready.disconnect()
            self.worker.fall_detected.disconnect()
        except TypeError as e:
           logger.warning("Failed to disconnect signal: %s", e)
            
        self.worker.stop()
        self.worker.wait()
        self.worker = None
        
        self.view.set_monitoring_state(False)
        logger.info("Stream disconnected")
        self.view.log_event("INFO", "Stream disconnected")
        self.view.clear_video()

    def handle_fall_alert(self, message):
        """Placeholder for fall alert handling. Will be expanded later."""
        self.falls_count += 1
        logger.warning("Fall detected: %s (Total falls: %d)", message, self.falls_count)
        
        self.view.update_fall_count(str(self.falls_count))
        self.view.trigger_fall_alert(message)
        self.view.log_event("ALERT", f"Fall detected: {message}")
        
        # TODO: Implementar lógica avanzada más adelante (guardar en BD, notificaciones, etc.)