"""Controller of the administration (testing) screen."""

import logging
import os

from PySide6.QtCore import Slot

from src.controllers.base_monitor_controller import BaseMonitorController
from src.domain.monitoring_profiles import MonitoringStrategy, strategy_for
from src.domain.roles import is_admin
from src.dtos.frame_packet import FramePacket
from src.strings import Messages, risk_level_label
from src.threads.video_thread import strategy_for_file

logger = logging.getLogger(__name__)


class AdminController(BaseMonitorController):
    """Controller of the administrators, the application's testers.

    They have no patient: everything runs in test mode, so falls are shown and logged but
    never stored or e-mailed. On top of the standard workflow they choose the camera's test
    profile (the settings and model of a risk level), analyse video files, and see the
    skeleton view and the telemetry panel.

    Args:
        view: The AdminView (monitoring page) it drives.
        current_user: The signed-in administrator.

    Raises:
        PermissionError: If `current_user` is not an administrator.
    """

    SENDS_ALERTS = False

    def __init__(self, view, current_user):
        if not is_admin(current_user):
            raise PermissionError("The administration screen is only for administrators")
        super().__init__(view, current_user, patient=None)
        self.view.upload_requested.connect(self.start_video_file)

    def _camera_strategy(self) -> MonitoringStrategy:
        """The camera follows the test profile chosen in the view; there is no alert thread, so nothing is stored."""
        strategy = strategy_for(self.view.test_profile())
        self.view.log_event("INFO", Messages.TEST_MODE.format(level=risk_level_label(strategy.name)))
        return strategy

    @Slot(str)
    def start_video_file(self, file_path):
        """Starts analysing a video file in test mode, unless a source is already running.

        Args:
            file_path: The video file chosen in the view.
        """
        if self.video_thread is not None:
            logger.warning("Attempted to process a video file, but a monitoring is already running.")
            return

        # The file's own frame rate picks the model; there is no alert thread, so nothing is stored or e-mailed.
        self._start(file_path, strategy_for_file(file_path), Messages.PROCESSING_FILE.format(name=os.path.basename(file_path)))

    def _show_frame(self, packet: FramePacket):
        super()._show_frame(packet)
        self.view.show_pose(packet.skeleton, packet.telemetry)
