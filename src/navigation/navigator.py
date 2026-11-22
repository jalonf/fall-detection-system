"""Shows one screen at a time and owns the screens' life cycle.

A `Screen` is a view and the controller that drives it. `Navigator.show(screen)`:

1. stops the controller of the screen being left (`shutdown()`, e.g. it releases the camera) before
   anything else, so no worker outlives its screen;
2. cross-fades from the old view to the new one;
3. once the fade ends, destroys the old view, unless that screen is `persistent` (the sign-in screen,
   which is reused after every sign-out).

The navigator does not decide where to go: that is `AppCoordinator`'s job.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation, Slot
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

logger = logging.getLogger(__name__)

FADE_MS = 400


@dataclass(eq=False)
class Screen:
    view: QWidget
    controller: object | None = None
    persistent: bool = False      # kept and reused after leaving it, instead of being destroyed

    def name(self) -> str:
        return type(self.view).__name__

    def stop(self) -> None:
        """Lets the controller release what it holds (camera, threads). Controllers without it are skipped."""
        shutdown = getattr(self.controller, "shutdown", None)
        if callable(shutdown):
            shutdown()


class Navigator(QObject):
    """A QObject owned by the window, so the end of each fade reaches it as a real Qt slot."""

    def __init__(self, window: QMainWindow):
        super().__init__(window)
        self._window = window
        self._stack = QStackedWidget()
        window.setCentralWidget(self._stack)
        self._current: Screen | None = None
        # The running cross-fade, if any: (overlay, animation, what to do when it ends).
        self._fade: tuple[QLabel, QPropertyAnimation, Callable[[], None]] | None = None

    @property
    def current(self) -> Screen | None:
        return self._current

    def show(self, screen: Screen) -> None:
        """Makes `screen` the visible one (see the module docstring for the steps)."""
        previous = self._current
        if previous is screen:
            return
        logger.info("Navigating from [%s] to [%s]", previous.name() if previous else "None", screen.name())
        self._finish_fade()      # a fade still running ends now: its overlay and clean-up are never lost
        if previous is not None:
            previous.stop()
        if self._stack.indexOf(screen.view) < 0:
            self._stack.addWidget(screen.view)
        self._current = screen

        if previous is None:
            self._stack.setCurrentWidget(screen.view)
            return
        self._cross_fade(screen.view, lambda: self._dispose(previous))

    def shutdown(self) -> None:
        """Stops the current screen's controller (the window is closing)."""
        self._finish_fade()
        if self._current is not None:
            self._current.stop()

    # ------------------------------------------------------------------ internals
    def _dispose(self, screen: Screen) -> None:
        if screen.persistent or screen is self._current:
            return
        self._stack.removeWidget(screen.view)
        screen.view.deleteLater()
        logger.debug("Screen %s destroyed", screen.name())

    def _cross_fade(self, target: QWidget, on_finished: Callable[[], None]) -> None:
        """Covers the window with a picture of the old view, switches underneath and fades the picture out."""
        overlay = QLabel(self._window)
        overlay.setPixmap(self._stack.currentWidget().grab())
        overlay.setGeometry(self._window.rect())
        overlay.show()
        overlay.raise_()
        self._stack.setCurrentWidget(target)

        # The effect and the animation are children of the overlay, so they live exactly as long as it does.
        effect = QGraphicsOpacityEffect(overlay)
        overlay.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", overlay)
        animation.setDuration(FADE_MS)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._fade = (overlay, animation, on_finished)
        animation.finished.connect(self._finish_fade)
        animation.start()

    @Slot()
    def _finish_fade(self) -> None:
        if self._fade is None:
            return
        overlay, animation, on_finished = self._fade
        self._fade = None
        animation.stop()
        overlay.hide()
        overlay.deleteLater()
        on_finished()
