"""Context strip under the top bar: patient, camera, status and duration — the main place where the
monitoring state shows.

Each item is a small overline label with its value underneath: the patient's name with a risk
badge, the camera with the resolution and frame rate it runs at (set by the patient's risk level),
the status and the duration. During a fall alert the strip turns R50, its status pulses and an
Acknowledge button appears on the right.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.views.components.common.badge import Badge
from src.views.components.common.button import make_button
from src.views.components.common.painting import Divider
from src.views.components.common.status_indicator import StatusIndicator
from src.views.strings import EM_DASH, Monitor
from src.views.theme import (
    Colors,
    Size,
    Space,
    Type,
    make_label,
    make_tabular_label,
    set_props,
)

RISK_VARIANTS = {"LOW": "success", "MEDIUM": "warning", "HIGH": "danger"}
_PATIENT_WIDTH = 260
_SOURCE_WIDTH = 200


def _elide(label: QLabel, text: str, role: str, width: int, mode=Qt.TextElideMode.ElideRight) -> None:
    metrics = QFontMetrics(Type.font(role))
    label.setText(metrics.elidedText(text, mode, width))
    label.setToolTip(text if metrics.horizontalAdvance(text) > width else "")


class ContextBar(QWidget):
    acknowledge_clicked = Signal()

    def __init__(self, patient_name: str | None, risk_level: str | None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ContextBar")
        self.setFixedHeight(Size.CONTEXT_BAR)
        self._alert = False
        self._state = "idle"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.S6, 0, Space.S6, 1)
        layout.setSpacing(0)

        # Patient: name and risk badge.
        patient_row = QHBoxLayout()
        patient_row.setContentsMargins(0, 0, 0, 0)
        patient_row.setSpacing(Space.S2)
        self.patient = make_label("", "title-sm")
        if patient_name:
            _elide(self.patient, patient_name, "title-sm", _PATIENT_WIDTH)
        else:
            self.patient.setText(EM_DASH)
            set_props(self.patient, tone="tertiary")
        self.patient.setAccessibleName(Monitor.PATIENT)
        patient_row.addWidget(self.patient)
        level = (risk_level or "").strip().upper()
        self.risk: Badge | None = None
        if level in RISK_VARIANTS:
            self.risk = Badge(Monitor.RISK_BADGE.format(level=level), RISK_VARIANTS[level])
            patient_row.addWidget(self.risk, 0, Qt.AlignmentFlag.AlignVCenter)
        self._add_item(layout, Monitor.STRIP_PATIENT, patient_row)

        # Camera / source: name and its capture settings.
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

        self.acknowledge = make_button(Monitor.ACKNOWLEDGE, "danger", "md", "check", tooltip=Monitor.ACKNOWLEDGE_TIP)
        self.acknowledge.hide()
        self.acknowledge.clicked.connect(self.acknowledge_clicked)
        layout.addWidget(self.acknowledge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.set_state("idle")

    def _add_item(self, layout: QHBoxLayout, label: str, value, *, divider: bool = False) -> QLabel:
        if divider:
            layout.addSpacing(Space.S6)
            layout.addWidget(Divider(Colors.N150, vertical=True, length=32))
            layout.addSpacing(Space.S6)
        column = QVBoxLayout()
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(Space.S1)
        column.addStretch(1)
        caption = make_label(label, "overline", "tertiary")
        column.addWidget(caption)
        if isinstance(value, QWidget):
            column.addWidget(value, 0, Qt.AlignmentFlag.AlignLeft)
            value.setAccessibleName(label.title())
        else:
            column.addLayout(value)
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
        """Shows the camera (or video file) and a short detail such as "1280 × 720 · 15 fps"."""
        self.source_label.setText(Monitor.STRIP_CAMERA if camera else Monitor.STRIP_FILE)
        if label:
            _elide(self.source, label, "body-strong", _SOURCE_WIDTH, Qt.TextElideMode.ElideMiddle)
            set_props(self.source, tone="primary")
        else:
            self.source.setText(EM_DASH)
            set_props(self.source, tone="tertiary")
        self.source_detail.setText(detail)
        self.source_detail.setVisible(bool(detail))
        self.source_detail.setToolTip(tooltip)
        self.source.setToolTip(self.source.toolTip() or tooltip)

    def set_duration(self, text: str | None) -> None:
        if text != self.duration.text():
            self.duration.setText(text or EM_DASH)
            set_props(self.duration, tone="primary" if text else "tertiary")

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
        self.status.set_pulse_phase(phase)

    def status_text(self) -> str:
        return self.status.text()

    # ------------------------------------------------------------------ painting
    def sizeHint(self) -> QSize:
        return QSize(1120, Size.CONTEXT_BAR)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.R50 if self._alert else Colors.N0))
        painter.fillRect(QRect(0, self.height() - 1, self.width(), 1), QColor(Colors.R200 if self._alert else Colors.N200))
