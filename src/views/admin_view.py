from src.views.base_monitor_view import BaseMonitorView
from src.views.components.squeleton_panel import SkeletonPanel


class AdminView(BaseMonitorView):
    """
    Administrator monitoring view featuring extended management tools,
    video stream handling, skeleton telemetry, and administrative alert triggers.
    """

    SCREEN_NAME = "adminScreen"
    APP_TAGLINE = "Administrator Control Panel"

    def __init__(self, user_name="Admin", user_role="Administrator", parent=None):
        super().__init__(user_name, user_role, parent)

    def _add_sidebar_panels(self, sidebar_layout):
        # Skeleton telemetry is exclusive to the administrator view.
        self.skeleton_panel = SkeletonPanel()
        sidebar_layout.addWidget(self.skeleton_panel)

    def set_monitoring_state(self, active: bool):
        super().set_monitoring_state(active)
        self.skeleton_panel.set_streaming(active)

    def clear_video(self):
        super().clear_video()
        self.skeleton_panel.clear_video()
