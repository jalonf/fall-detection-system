"""Shows one screen at a time and owns the screens' life cycle.

A `Screen` is a view (a `ScreenView`) and the controllers that drive it. `Navigator.show(screen)`:

1. stops the controllers of the screen being left (`shutdown()`, e.g. it releases the camera) before
   anything else, so no thread outlives its screen;
2. cross-fades from the old view to the new one (`PageTransition`) and calls the new view's `entered()`;
3. once the fade ends, calls the old view's `left()` and destroys it, unless that screen is
   `persistent` (the sign-in screen, which is reused after every sign-out).

The navigator does not decide where to go: that is `AppCoordinator`'s job.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from src.views.components.common.page_transition import PageTransition
from src.views.screen_view import ScreenView
from src.views.theme import Motion

logger = logging.getLogger(__name__)


@dataclass(eq=False)
class Screen:
    """A view and the controllers that drive it (one per page of a dashboard).

    Attributes:
        view: The screen shown.
        controllers: Its controllers; their `shutdown()` (if any) is called when leaving the screen.
        persistent: Kept and reused after leaving it, instead of being destroyed.
    """
    view: ScreenView
    controllers: tuple[object, ...] = ()
    persistent: bool = False

    def name(self) -> str:
        """Returns the view's class name, for the log."""
        return type(self.view).__name__

    def stop(self) -> None:
        """Lets the controllers release what they hold (camera, threads). Controllers without it are skipped."""
        for controller in self.controllers:
            shutdown = getattr(controller, "shutdown", None)
            if callable(shutdown):
                shutdown()


class Navigator(QObject):
    """Shows the screens in the window's central widget. A QObject owned by the window.

    Args:
        window: The main window.
    """

    def __init__(self, window: QMainWindow):
        super().__init__(window)
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)
        window.setCentralWidget(host)
        # The fade overlay lives in the central widget, so the window's toasts stay above it.
        self._transition = PageTransition(host, shift=0, duration=Motion.PAGE, crossfade=True)
        self._transition.finished.connect(self._on_transition_finished)
        self._current: Screen | None = None
        self._leaving: list[Screen] = []

    @property
    def current(self) -> Screen | None:
        """The screen shown now, or None before the first one."""
        return self._current

    def show(self, screen: Screen) -> None:
        """Makes `screen` the visible one (see the module docstring for the steps)."""
        previous = self._current
        if previous is screen:
            return
        logger.info("Navigating from [%s] to [%s]", previous.name() if previous else "None", screen.name())
        self._transition.finish()        # a fade still running ends now: its screen is released
        if previous is not None:
            previous.stop()
            self._leaving.append(previous)
        if self._stack.indexOf(screen.view) < 0:
            self._stack.addWidget(screen.view)
        self._current = screen
        self._transition.slide(self._stack, screen.view)
        screen.view.entered()

    def shutdown(self) -> None:
        """Stops the current screen's controllers (the window is closing)."""
        self._transition.finish()
        if self._current is not None:
            self._current.stop()

    @Slot()
    def _on_transition_finished(self) -> None:
        leaving, self._leaving = self._leaving, []
        for screen in leaving:
            if screen is self._current:
                continue
            screen.view.left()
            if not screen.persistent:
                self._stack.removeWidget(screen.view)
                screen.view.deleteLater()
                logger.debug("Screen %s destroyed", screen.name())
