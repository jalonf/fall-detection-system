"""Base of the application's screens: the views `Navigator` shows one at a time."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget


class ScreenView(QWidget):
    """A whole screen of the window (the sign-in screen, a dashboard).

    `Navigator` tells it explicitly when it is entered and left, so a screen never has to guess
    from show and hide events (which also come from minimising the window or switching tabs).
    """

    def entered(self) -> None:
        """The screen has just become the current one (its transition may still be running)."""

    def left(self) -> None:
        """The screen is no longer shown and its transition has ended. A persistent screen may come back."""
