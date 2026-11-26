"""Session card at the top of the monitoring screen's body.

It shows the patient, camera, status and duration: the main place where the monitoring
state shows. It is a card like the panels under it (N0 fill, N200 border, square
corners), separated from the top bar by the body's margin, so it reads as content rather
than as part of the header.

Each item is a small overline label with its value underneath, every value on a row of the same
height so the labels line up. The items are packed from the left, separated by thin dividers. The
first one is a selector with a badge next to it: caregivers pick the patient being monitored (with
their risk badge); administrators, who have no patients, pick a test profile (with a TEST MODE
badge). Then the camera's resolution and frame rate (set by that risk level; which camera is picked
shows once, in the selector under the video) or the video file's name, the status and the duration.

During a fall alert the card turns R50 with an R200 border and a 3 px R600 bar on the left (like
the alert rows of the event log), its status pulses and an Acknowledge button appears at the right
end, in space that was already empty, so no item moves.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.views.components.common.badge import Badge
from src.views.components.common.button import make_button
from src.views.components.common.painting import Divider, crisp
from src.views.components.common.status_indicator import StatusIndicator
from src.views.strings import EM_DASH, Monitor
from src.views.theme import (
    Colors,
    Radius,
    Size,
    Space,
    Type,
    make_label,
    make_tabular_label,
    set_props,
)

_SOURCE_WIDTH = 200


def _elide(label: QLabel, text: str, role: str, width: int, mode=Qt.TextElideMode.ElideRight) -> None:
    metrics = QFontMetrics(Type.font(role))
    label.setText(metrics.elidedText(text, mode, width))
    label.setToolTip(text if metrics.horizontalAdvance(text) > width else "")


class ContextBar(QWidget):
    """The session card (see the module docstring).

    Signals:
        acknowledge_clicked: The user acknowledged the fall alert.

    Args:
        caption: Overline of the first item ("PATIENT" or "TEST PROFILE").
        selector: The combo of the first item.
        badge: The badge next to it (risk level or TEST MODE).
        parent: Parent widget.
    """
    acknowledge_clicked = Signal()

    def __init__(self, caption: str, selector: QWidget, badge: Badge, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ContextBar")
        self.setFixedHeight(Size.CONTEXT_BAR)
        self._alert = False
        self._state = "idle"

        layout = self._layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.S5, 1, Space.S4, 1)     # inside the 1 px border
        layout.setSpacing(0)

        # The patient (or test profile) being monitored, and its badge.
        selector_row = QHBoxLayout()
        selector_row.setContentsMargins(0, 0, 0, 0)
        selector_row.setSpacing(Space.S2)
        selector_row.addWidget(selector)
        self.badge = badge
        selector_row.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self._add_item(layout, caption, selector_row)

        # Camera: its capture settings; video file: its name.
        source_row = QHBoxLayout()
        source_row.setContentsMargins(0, 0, 0, 0)
        source_row.setSpacing(Space.S2)
        self.source = make_label(EM_DASH, "body-strong")
        self.source_detail = make_label("", "caption", "secondary")
        source_row.addWidget(self.source)
        source_row.addWidget(self.source_detail, 0, Qt.AlignmentFlag.AlignVCenter)
        self.source_label = self._add_item(layout, Monitor.STRIP_CAMERA, source_row, divider=True)

        reserve = (*Monitor.STATUS_TEXT.values(), Monitor.STATUS_ALERT_COUNT.format(n=99))
        self.status = StatusIndicator(reserve=reserve)
        self._add_item(layout, Monitor.STRIP_STATUS, self.status, divider=True)

        self.duration = make_tabular_label(EM_DASH, "body-strong", "tertiary", sample="00:00:00")
        self._add_item(layout, Monitor.STRIP_DURATION, self.duration, divider=True)
        layout.addStretch(1)

        # Acknowledge, at the right end: it takes empty space, so nothing moves when it appears.
        self.acknowledge = make_button(Monitor.ACKNOWLEDGE, "danger", "md", "check", tooltip=Monitor.ACKNOWLEDGE_TIP)
        self.acknowledge.clicked.connect(self.acknowledge_clicked)
        policy = self.acknowledge.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.acknowledge.setSizePolicy(policy)
        self.acknowledge.hide()
        layout.addWidget(self.acknowledge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.set_state("idle")

    def _add_item(self, layout: QHBoxLayout, label: str, value, *, divider: bool = False) -> QLabel:
        if divider:
            layout.addSpacing(Space.S6)
            layout.addWidget(Divider(Colors.N150, vertical=True, length=32), 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addSpacing(Space.S6)
        column = QVBoxLayout()
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(2)
        column.addStretch(1)
        caption = make_label(label, "overline", "tertiary")
        column.addWidget(caption)
        # Every value sits on a row as tall as the selector, so the captions above them line up.
        row = QWidget()
        row.setFixedHeight(Size.H_SM)
        row_layout = value if isinstance(value, QHBoxLayout) else QHBoxLayout()
        if isinstance(value, QWidget):
            row_layout.addWidget(value, 0, Qt.AlignmentFlag.AlignVCenter)
            value.setAccessibleName(label.title())
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addStretch(1)
        row.setLayout(row_layout)
        column.addWidget(row)
        column.addStretch(1)
        layout.addLayout(column)
        return caption

    # ------------------------------------------------------------------ API
    def set_state(self, state: str) -> None:
        """`state` is a monitoring state; the status indicator uses the same names for its kinds."""
        self._state = str(state)
        if not self._alert:
            self.status.set_status(self._state, Monitor.STATUS_TEXT[self._state])

    def set_source(self, label: str | None, detail: str = "", tooltip: str = "", *, camera: bool = True) -> None:
        """Shows the camera's settings ("1280 × 720 · 15 fps"), or a video file's name and a detail."""
        self.source_label.setText(Monitor.STRIP_CAMERA if camera else Monitor.STRIP_FILE)
        if label:
            _elide(self.source, label, "body-strong", _SOURCE_WIDTH, Qt.TextElideMode.ElideMiddle)
            set_props(self.source, tone="")
        else:
            self.source.setText(EM_DASH)
            set_props(self.source, tone="tertiary")
        self.source_detail.setText(detail)
        self.source_detail.setVisible(bool(detail))
        self.source_detail.setToolTip(tooltip)
        self.source.setToolTip(self.source.toolTip() or tooltip)

    def set_duration(self, text: str | None) -> None:
        """Shows the run's duration.

        Args:
            text: "HH:MM:SS", or None for an em dash.
        """
        if text != self.duration.text():
            self.duration.setText(text or EM_DASH)
            set_props(self.duration, tone="" if text else "tertiary")

    def set_alert(self, active: bool, count: int = 1) -> None:
        """Shows the fall alert (with the number of falls since the last acknowledgement) or clears it."""
        changed = active != self._alert
        self._alert = active
        if active:
            text = Monitor.STATUS_TEXT["alert"] if count <= 1 else Monitor.STATUS_ALERT_COUNT.format(n=count)
            self.status.set_status("alert", text)
        else:
            self.status.set_status(self._state, Monitor.STATUS_TEXT[self._state])
        self.acknowledge.setVisible(active)
        if changed:
            self.update()

    def set_pulse_phase(self, phase: float) -> None:
        """Moves the status triangle along the alert pulse.

        Args:
            phase: 0 to 1.
        """
        self.status.set_pulse_phase(phase)

    # ------------------------------------------------------------------ painting
    def sizeHint(self) -> QSize:
        """Preferred size: its content's width and the fixed height."""
        return QSize(self._layout.sizeHint().width(), Size.CONTEXT_BAR)

    def paintEvent(self, event) -> None:
        """A card like `Panel`: fill and a 1 px border; red tones and a left bar during an alert."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        outline = QPainterPath()
        outline.addRoundedRect(crisp(QRectF(self.rect())), Radius.R_LG, Radius.R_LG)
        painter.fillPath(outline, QColor(Colors.R50 if self._alert else Colors.N0))
        if self._alert:
            painter.save()
            painter.setClipPath(outline)
            painter.fillRect(QRect(0, 0, 3, self.height()), QColor(Colors.R600))
            painter.restore()
        painter.setPen(QPen(QColor(Colors.R200 if self._alert else Colors.N200), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(outline)
