import time
from src.core.video_worker import VideoWorker

FALL_ALERT_COOLDOWN_S = 3.0

class MonitorController:
    """
    Controller responsible for managing the video monitoring workflow, 
    camera threads, and handling fall detection events in real time.
    """
    def __init__(self, view, on_logout_callback):
        """
        Args:
            view: The monitoring view instance showing the camera feed and statistics.
            on_logout_callback (callable): Callback function executed when the user signs out.
        """
        self.view = view
        self.worker = None
        self.falls_count = 0
        self._last_fall_ts = 0.0
        
        self.view.on_start = self.start_camera
        self.view.on_stop = self.stop_camera
        self.view.on_logout = on_logout_callback

    def start_camera(self, camera_index):
        """
        Initializes and starts the video processing worker thread 
        for the specified camera index if not already active.
        
        Args:
            camera_index (int): Index or identifier of the video source.
        """
        if self.worker is not None:
            return

        self.worker = VideoWorker(camera_index=camera_index)
        self.worker.frame_ready.connect(self.view.update_video_frame)
        self.worker.fall_detected.connect(self.handle_fall_alert)
        self.worker.start()

    def stop_camera(self):
        """
        Safely stops the active video worker thread, disconnects its signals,
        releases resources, and clears the video display on the view.
        """
        if self.worker:
            try:
                self.worker.frame_ready.disconnect()
                self.worker.fall_detected.disconnect()
            except Exception:
                pass
                
            self.worker.stop()
            self.worker.wait()
            self.worker = None
            
            self.view.clear_video()

    def handle_fall_alert(self, message):
        """
        Handles incoming fall alerts from the video worker, applying a cooldown 
        period to prevent redundant triggers, updating statistics, and notifying the view.
        
        Args:
            message (str): Description or details of the detected fall event.
        """
        now = time.time()
        if now - self._last_fall_ts < FALL_ALERT_COOLDOWN_S:
            return
        self._last_fall_ts = now
        self.falls_count += 1
        self.view.update_stat("stat_falls", str(self.falls_count))
        self.view.trigger_fall_alert(message)