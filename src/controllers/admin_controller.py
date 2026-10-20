from src.controllers.base_monitor_controller import BaseMonitorController


class AdminController(BaseMonitorController):
    """
    Monitoring controller for the administrator: the same workflow as the standard
    one, plus the skeleton view and telemetry panel.
    """

    def _connect_worker(self, worker):
        super()._connect_worker(worker)
        worker.skeleton_frame_ready.connect(self.view.skeleton_panel.update_frame)
        worker.telemetry_data_ready.connect(self.view.skeleton_panel.update_telemetry)
