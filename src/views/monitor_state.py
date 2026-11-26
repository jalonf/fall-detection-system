"""States of a monitoring run, shared by the monitoring page and every component that shows them."""

from __future__ import annotations

from enum import StrEnum


class MonitorState(StrEnum):
    """States of a monitoring run. Being a StrEnum, each one equals its string ("live" == LIVE)."""
    IDLE = "idle"
    STARTING = "starting"
    LIVE = "live"
    STOPPING = "stopping"
    ERROR = "error"
    FINISHED = "finished"


RUNNING = (MonitorState.STARTING, MonitorState.LIVE, MonitorState.STOPPING)
STOPPED = (MonitorState.IDLE, MonitorState.ERROR, MonitorState.FINISHED)
