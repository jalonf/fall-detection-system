"""Segmented control: equal-width checkable segments with nothing selected until the user picks."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Signal, Slot
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QSizePolicy, QWidget

from src.views.components.common.button import Button
from src.views.components.common.painting import crisp
from src.views.theme import Colors, Radius, Size, Type

_PADDING = 24   # 12 px each side of a segment's text


class SegmentedControl(QWidget):
    selection_changed = Signal(int)

    def __init__(self, labels: list[str] | tuple[str, ...], *, height: int = Size.H_MD,
                 accessible_name: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self._labels = tuple(labels)
        self._invalid = False
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self.buttons: list[Button] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        count = len(self._labels)
        for index, label in enumerate(self._labels):
            button = Button(label, "segment", None)
            button.setCheckable(True)
            button.setFixedHeight(height - 2)
            button.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            position = "only" if count == 1 else "first" if index == 0 else "last" if index == count - 1 else "middle"
            button.setProperty("position", position)
            button.setAccessibleName(label)
            self._group.addButton(button, index)
            layout.addWidget(button, 1)
            self.buttons.append(button)
        self._group.idClicked.connect(self._on_clicked)

        self.setFixedHeight(height)
        self.setMinimumWidth(self.minimum_width(self._labels))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if accessible_name:
            self.setAccessibleName(accessible_name)

    # ------------------------------------------------------------------ API
    @staticmethod
    def minimum_width(labels) -> int:
        metrics = QFontMetrics(Type.font("body-strong"))
        widest = max((metrics.horizontalAdvance(label) for label in labels), default=0)
        return len(labels) * (widest + _PADDING) + len(labels) + 1

    @staticmethod
    def fits(labels, width: int) -> bool:
        """True when the labels fit in `width` both summed and as equal-width segments."""
        metrics = QFontMetrics(Type.font("body-strong"))
        total = sum(metrics.horizontalAdvance(label) + _PADDING for label in labels)
        return total <= width and SegmentedControl.minimum_width(labels) <= width

    def selected(self) -> int:
        return self._group.checkedId()

    def set_selected(self, index: int) -> None:
        button = self._group.button(index)
        if button is not None:
            button.setChecked(True)

    def clear(self) -> None:
        self._group.setExclusive(False)
        for button in self.buttons:
            button.setChecked(False)
        self._group.setExclusive(True)

    def set_invalid(self, invalid: bool) -> None:
        if invalid != self._invalid:
            self._invalid = invalid
            self.update()

    def focus_target(self) -> QWidget:
        checked = self._group.checkedButton()
        return checked or self.buttons[0]

    @Slot(int)
    def _on_clicked(self, index: int) -> None:
        self.set_invalid(False)
        self.selection_changed.emit(index)

    # ------------------------------------------------------------------ painting
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = crisp(QRectF(self.rect()))
        painter.setBrush(QColor(Colors.N0 if self.isEnabled() else Colors.N100))
        painter.setPen(QPen(QColor(Colors.R600 if self._invalid else Colors.N300), 1))
        painter.drawRoundedRect(rect, Radius.R_MD, Radius.R_MD)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        divider = QColor(Colors.N200)
        for button in self.buttons[1:]:
            x = button.geometry().left() - 1
            painter.fillRect(x, 1, 1, self.height() - 2, divider)
        painter.end()
