from src.controllers.base_monitor_controller import BaseMonitorController


class MonitorController(BaseMonitorController):
    """
    Controller responsible for managing the video monitoring workflow,
    camera threads, and handling fall detection events in real time.
    """
