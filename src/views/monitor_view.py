from src.views.base_monitor_view import BaseMonitorView


class MonitorView(BaseMonitorView):
    """
    Main real-time monitoring view without skeleton panels,
    focusing solely on the video feed, system status, and event logs.
    """

    SCREEN_NAME = "monitorScreen"
    APP_TAGLINE = "Monitor Panel"

    def __init__(self, user_name="User", user_role="Family / Caregiver", parent=None):
        super().__init__(user_name, user_role, parent)
