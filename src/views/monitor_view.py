"""Monitoring screen for caregivers and medical staff: camera monitoring, event log and session."""

from __future__ import annotations

from src.views.base_monitor_view import BaseMonitorView
from src.views.strings import Monitor


class MonitorView(BaseMonitorView):
    """Monitoring screen of caregivers and medical staff: the shared screen as it is."""
    SECTION = Monitor.SECTION_MONITORING
    CAN_ANALYSE_FILES = False
