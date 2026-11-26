"""Keyboard shortcuts of a page."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QWidget


def add_shortcut(widget: QWidget, keys: tuple[str, ...], slot: Callable[[], object]) -> QAction:
    """Adds a shortcut that works while the focus is anywhere inside `widget`.

    Args:
        widget: The page that owns the shortcut.
        keys: Its key sequences, e.g. ("Ctrl+Return", "Ctrl+Enter").
        slot: What it does.

    Returns:
        The action, e.g. to enable or disable the shortcut.
    """
    action = QAction(widget)
    action.setShortcuts([QKeySequence(key) for key in keys])
    action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
    action.triggered.connect(slot)
    widget.addAction(action)
    return action
