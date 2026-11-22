"""Monitoring screen for caregivers and medical staff: camera monitoring, event log and session."""

from __future__ import annotations

from src.views.base_monitor_view import BaseMonitorView
from src.views.strings import Monitor


class MonitorView(BaseMonitorView):
    SECTION = Monitor.SECTION_MONITORING
    CAN_ANALYSE_FILES = False
