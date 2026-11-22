"""Session panel: source, start time, duration, falls and events of this session (no status row)."""

from __future__ import annotations

from PySide6.QtCore import QTime
from PySide6.QtWidgets import QWidget

from src.views.components.common.key_value_list import KeyValueList
from src.views.components.common.panel import Panel
from src.views.strings import Session


class SessionPanel(Panel):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(Session.TITLE, parent=parent)
        self.values = KeyValueList([
            ("source", Session.SOURCE),
            ("started", Session.STARTED),
            ("duration", Session.DURATION),
            ("falls", Session.FALLS),
            ("events", Session.EVENTS),
        ])
        self.body_layout().addWidget(self.values)
        self.set_falls(0)
        self.set_events(0)

    def set_source(self, label: str | None) -> None:
        self.values.set_value("source", label)

    def set_started(self, time: QTime | None) -> None:
        self.values.set_value("started", time.toString("HH:mm:ss") if time is not None else None)

    def set_duration(self, text: str | None) -> None:
        self.values.set_value("duration", text)

    def set_falls(self, count: int) -> None:
        self.values.set_value("falls", str(count), tone="danger" if count > 0 else None)

    def set_events(self, count: int) -> None:
        self.values.set_value("events", str(count))
