"""What the stage shows when there is no image: stopped, starting, source error or analysis finished."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from src.strings import Monitor
from src.views.components.common.empty_state import EmptyState
from src.views.theme import Colors


class StagePlaceholder(EmptyState):
    """What the video stage shows without an image: stopped, starting, error or finished.

    Signals:
        retry_clicked: "Try again" was pressed after a source error.
    """
    retry_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(on_dark=True, parent=parent)
        self.action_clicked.connect(self.retry_clicked)
        self.show_state("idle")

    def show_state(self, state: str, *, error: str | None = None, label: str = "", duration: str = "") -> None:
        """Shows the content of a monitoring state.

        Args:
            state: The monitoring state.
            error: The source's error message (error state).
            label: Name of the source (finished state).
            duration: How long the analysis took (finished state).
        """
        if state == "starting":
            title, text = Monitor.PLACEHOLDER["starting"]
            self.set_content(spinner=True, title=title, text=text)
        elif state == "stopping":
            self.set_content(spinner=True, icon_color=Colors.S300, title=Monitor.STATUS_TEXT["stopping"])
        elif state == "error":
            title, _ = Monitor.PLACEHOLDER["error"]
            self.set_content(icon="alert-triangle", icon_color=Colors.R300, title=title, text=error or "",
                             action=Monitor.TRY_AGAIN)
        elif state == "finished":
            title, template = Monitor.PLACEHOLDER["finished"]
            self.set_content(icon="check-circle", icon_color=Colors.G500, title=title,
                             text=template.format(label=label, duration=duration))
        else:
            title, text = Monitor.PLACEHOLDER["idle"]
            self.set_content(icon="camera", title=title, text=text)
