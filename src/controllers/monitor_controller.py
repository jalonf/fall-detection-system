"""Controller of the caregivers' and medical staff's monitoring screen."""

from src.controllers.base_monitor_controller import BaseMonitorController


class MonitorController(BaseMonitorController):
    """Monitoring controller of caregivers and medical staff.

    It uses the shared workflow as it is: the camera follows the patient's risk level, and
    each fall is stored and e-mailed to the user.
    """
