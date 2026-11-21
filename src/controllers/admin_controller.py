from src.controllers.base_monitor_controller import BaseMonitorController
from src.dtos.frame_packet import FramePacket


class AdminController(BaseMonitorController):
    """
    Monitoring controller for the administrator: the same workflow as the standard
    one, plus the skeleton view and telemetry panel.
    """

    def _show_frame(self, packet: FramePacket):
        super()._show_frame(packet)
        self.view.skeleton_panel.update_frame(packet.skeleton)
        self.view.skeleton_panel.update_telemetry(packet.telemetry)
