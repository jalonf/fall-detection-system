from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from src.views.icons import icon
from src.views.theme import Colors, set_prop

_EMPTY = "—"


class _ElidedLabel(QLabel):
    """A QLabel that shortens long text with an ellipsis instead of widening the layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._full_text = ""
        self.setMinimumWidth(1)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def set_full_text(self, text: str):
        self._full_text = text
        self._elide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide()

    def _elide(self):
        elided = self.fontMetrics().elidedText(
            self._full_text, Qt.TextElideMode.ElideMiddle, max(self.width(), 1)
        )
        if elided != self.text():
            self.setText(elided)


class CameraInfoCard(QFrame):
    """
    Read-only strip showing the camera configuration currently in effect:
    the selected source, the resolution of the incoming frames and the measured
    frame rate. It is always visible under the video stage.

    Purely presentational: it never talks to the capture pipeline. The owner
    (VideoPanel) feeds it with values the UI already has.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cameraInfo")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._source = ""
        self._file_path: str | None = None
        self._active = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 18, 10)
        layout.setSpacing(14)

        self._tile = QLabel()
        self._tile.setObjectName("cameraIcon")
        self._tile.setProperty("state", "idle")
        self._tile.setFixedSize(36, 36)
        self._tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tile.setPixmap(icon("camera", Colors.PRIMARY, 20).pixmap(QSize(20, 20)))
        layout.addWidget(self._tile)

        self._source_value = _ElidedLabel()
        self._source_value.setObjectName("cameraValue")
        self._add_cell(layout, "Source", self._source_value, stretch=3)
        self._add_divider(layout)

        self._resolution_value = QLabel(_EMPTY)
        self._resolution_value.setObjectName("metricValue")
        self._add_cell(layout, "Resolution", self._resolution_value, stretch=2)
        self._add_divider(layout)

        self._fps_value = QLabel(_EMPTY)
        self._fps_value.setObjectName("metricValue")
        self._add_cell(layout, "Frame rate", self._fps_value, stretch=2)

        self.reset_stream()

    # ---------------------------------------------------------------- build
    @staticmethod
    def _add_cell(layout: QHBoxLayout, caption: str, value: QLabel, stretch: int):
        column = QVBoxLayout()
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(2)
        cap = QLabel(caption)
        cap.setObjectName("metricCaption")
        column.addWidget(cap)
        column.addWidget(value)
        layout.addLayout(column, stretch)

    @staticmethod
    def _add_divider(layout: QHBoxLayout):
        divider = QFrame()
        divider.setObjectName("cameraInfoDivider")
        divider.setFixedSize(1, 28)
        layout.addWidget(divider)

    # ------------------------------------------------------------------ API
    def set_source(self, text: str):
        """Selected capture source (as listed in the source selector)."""
        self._source = text
        self._refresh_source()

    def show_file(self, path: str):
        """Remember an uploaded video; it replaces the source label while analysis is active."""
        self._file_path = path
        self._refresh_source()

    def clear_file(self):
        self._file_path = None
        self._refresh_source()

    def set_active(self, active: bool):
        self._active = active
        set_prop(self._tile, "state", "active" if active else "idle")
        if not active:
            self._file_path = None
            self.reset_stream()
        self._refresh_source()

    def set_stream(self, width: int, height: int, fps: float):
        self._set_value(self._resolution_value, f"{width}×{height}")
        self._set_value(self._fps_value, f"{fps:.0f} fps")

    def reset_stream(self):
        self._set_value(self._resolution_value, None)
        self._set_value(self._fps_value, None)

    # ------------------------------------------------------------- internals
    def _refresh_source(self):
        if self._active and self._file_path:
            self._source_value.set_full_text(Path(self._file_path).name)
            self._source_value.setToolTip(self._file_path)
        else:
            self._source_value.set_full_text(self._source or _EMPTY)
            self._source_value.setToolTip("")

    @staticmethod
    def _set_value(label: QLabel, text: str | None):
        label.setText(text if text else _EMPTY)
        set_prop(label, "empty", text is None)
