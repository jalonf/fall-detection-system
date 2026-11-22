"""File dialogs that never block the main window.

A modal dialog (native or not) makes Qt disable the main window at the OS level, and Windows then
plays its "ding" whenever the user clicks it. These dialogs are non-modal: the caller connects
`fileSelected` and shows them.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QWidget


def make_file_dialog(parent: QWidget, title: str, name_filter: str, *, save: bool = False,
                     default_name: str = "", default_suffix: str = "") -> QFileDialog:
    """Configured, non-modal file dialog owned by `parent`'s window; deleted when closed."""
    dialog = QFileDialog(parent.window(), title, str(Path.home()), name_filter)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.setWindowModality(Qt.WindowModality.NonModal)
    dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    if save:
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        if default_name:
            dialog.selectFile(default_name)
        if default_suffix:
            dialog.setDefaultSuffix(default_suffix)
    else:
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    return dialog
