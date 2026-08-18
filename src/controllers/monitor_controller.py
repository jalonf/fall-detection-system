import time
from src.core.video_worker import VideoWorker

FALL_ALERT_COOLDOWN_S = 3.0

class MonitorController:
    """
    Controller responsible for managing the video monitoring workflow, 
    camera threads, and handling fall detection events in real time.
    """
    
    def __init__(self, view, on_logout_callback):
        self.view = view
        self.worker = None
        self.falls_count = 0
        self._last_fall_ts = 0.0
        
        # Conectamos las señales nativas de la vista a los métodos del controlador
        self.view.start_requested.connect(self.start_camera)
        self.view.stop_requested.connect(self.stop_camera)
        self.view.logout_requested.connect(on_logout_callback)

    def start_camera(self, camera_index):
        if self.worker is not None:
            return

        self.worker = VideoWorker(camera_index=camera_index)
        self.worker.frame_ready.connect(self.view.update_video_frame)
        self.worker.fall_detected.connect(self.handle_fall_alert)
        self.worker.start()
        
        self.view.set_monitoring_state(True)
        self.view.log_event("INFO", f"Stream connected (Source {camera_index})")

    def stop_camera(self):
        if self.worker:
            try:
                self.worker.frame_ready.disconnect()
                self.worker.fall_detected.disconnect()
            except Exception:
                pass
                
            self.worker.stop()
            self.worker.wait()
            self.worker = None
            
            self.view.set_monitoring_state(False)
            self.view.log_event("INFO", "Stream disconnected")
            self.view.clear_video()

    def handle_fall_alert(self, message):
        now = time.time()
        if now - self._last_fall_ts < FALL_ALERT_COOLDOWN_S:
            return
        self._last_fall_ts = now
        self.falls_count += 1
        
        self.view.update_fall_count(str(self.falls_count))
        self.view.trigger_fall_alert(message)