"""List of the caregiver's patients: a page heading, then a table card or an empty state.

Layout: the heading (title, counter, one line about what patients are for) with "Add patient" on
its right, and under it a card that is as tall as its rows, so a short list does not sit in a large
empty box; with many patients the card reaches the bottom of the page and its rows scroll.

Each row shows the name (and the medical notes under it), the risk badge, how many falls are stored,
the latest one and when the patient was added; the bin button at the end asks to delete them. With
no patients the card holds an empty state whose button adds the first one.
"""

from __future__ import annotations

import datetime

from PySide6.QtCore import QDate, QDateTime, QLocale, QRect, QSize, Qt, QTime, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.dtos.patient_summary import PatientSummary
from src.strings import Patients
from src.views.components.common.badge import Badge, risk_badge
from src.views.components.common.button import make_button
from src.views.components.common.empty_state import EmptyState
from src.views.components.common.painting import Surface
from src.views.theme import Colors, Space, Type, make_label

_LOCALE = QLocale(QLocale.Language.Spanish, QLocale.Country.Spain)
ROW_HEIGHT = 60
HEADER_HEIGHT = 36
# Fixed widths of the columns after the name, which takes the rest; the last one holds the bin button.
COLUMN_WIDTHS = (140, 80, 180, 130, 40)
EMPTY_HEIGHT = 320               # the empty state's card


def format_date(value: datetime.datetime | None, pattern: str) -> str:
    """Formats a date the way the interface shows dates ("3 nov 2026").

    Args:
        value: The date, or None.
        pattern: A Qt date pattern.

    Returns:
        The text, or "" for None.
    """
    if value is None:
        return ""
    when = QDateTime(QDate(value.year, value.month, value.day), QTime(value.hour, value.minute, value.second))
    return _LOCALE.toString(when, pattern)


def falls_text(count: int) -> str:
    """Returns "sin caídas guardadas", "1 caída guardada" or "n caídas guardadas"."""
    if count == 0:
        return Patients.FALLS_NONE
    return Patients.FALLS_ONE if count == 1 else Patients.FALLS_MANY.format(n=count)


def _columns(layout: QHBoxLayout, name: QWidget, cells: list[QWidget]) -> None:
    """Lays a row out in the table's columns: the name stretches, the others are fixed."""
    layout.addWidget(name, 1)
    for cell, width in zip(cells, COLUMN_WIDTHS, strict=True):
        cell.setFixedWidth(width)
        layout.addWidget(cell, 0, Qt.AlignmentFlag.AlignVCenter)


def _card() -> Surface:
    """N0 surface with a 1 px N200 border, on the page's N50 canvas."""
    return Surface(Colors.N0, border=Colors.N200)


class _FitScrollArea(QScrollArea):
    """Frameless scroll area that asks for the height of its content (so the card hugs its rows)."""

    def __init__(self, widget: QWidget, parent: QWidget | None = None):
        super().__init__(parent)
        self._content = widget
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(widget)
        self.viewport().setAutoFillBackground(False)
        widget.setAutoFillBackground(False)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), self._content.sizeHint().height())

    def minimumSizeHint(self) -> QSize:
        return QSize(0, min(ROW_HEIGHT * 2, self._content.sizeHint().height()))


class _Ruled(QWidget):
    """A row with a 1 px N150 rule under it (none under the last row: the card's border closes it)."""

    ruled = True

    def paintEvent(self, event) -> None:
        if self.ruled:
            QPainter(self).fillRect(QRect(0, self.height() - 1, self.width(), 1), QColor(Colors.N150))


class _HeaderRow(QWidget):
    """The column captions, on an N50 band with an N200 rule under it (like a panel's header)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(HEADER_HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.S4, 0, Space.S4, 1)
        self._layout = layout
        layout.setSpacing(Space.S4)
        name, *others = Patients.COLUMNS
        _columns(layout, make_label(name, "overline", "tertiary"),
                 [make_label(caption, "overline", "tertiary") for caption in others] + [QWidget()])

    def set_scrollbar_inset(self, width: int) -> None:
        """Keeps the captions over their columns while the rows' scroll bar takes `width` px."""
        self._layout.setContentsMargins(Space.S4, 0, Space.S4 + width, 1)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.N50))
        painter.fillRect(QRect(0, self.height() - 1, self.width(), 1), QColor(Colors.N200))


class PatientRow(_Ruled):
    """One patient.

    Signals:
        delete_clicked(int): The bin button was pressed (the patient's id).
    """
    delete_clicked = Signal(int)

    def __init__(self, patient: PatientSummary, parent: QWidget | None = None):
        super().__init__(parent)
        self.patient = patient
        self.setFixedHeight(ROW_HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.S4, 0, Space.S4, 1)
        layout.setSpacing(Space.S4)

        identity = self._identity = QWidget()
        text = QVBoxLayout(identity)
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(0)
        text.addStretch(1)
        self.name = make_label(patient.name, "body-strong")
        text.addWidget(self.name)
        if patient.medical_notes:
            self.notes = make_label("", "caption", "secondary")
            self.notes.setToolTip(patient.medical_notes)
            text.addWidget(self.notes)
        else:
            self.notes = None
        text.addStretch(1)

        risk = Badge(*risk_badge(patient.risk_level))
        risk_cell = QWidget()
        risk_layout = QHBoxLayout(risk_cell)
        risk_layout.setContentsMargins(0, 0, 0, 0)
        risk_layout.addWidget(risk, 0, Qt.AlignmentFlag.AlignVCenter)
        risk_layout.addStretch(1)

        falls = make_label(str(patient.fall_count), "body", None if patient.fall_count else "tertiary")
        if patient.last_fall_at is None:
            last_fall = make_label(Patients.NO_FALLS, "body", "tertiary")
        else:
            last_fall = make_label(format_date(patient.last_fall_at, Patients.DATE_TIME_FORMAT), "body")
        added = make_label(format_date(patient.added_at, Patients.DATE_FORMAT), "body", "secondary")

        self.delete = make_button("", "ghost", "sm", "trash", tooltip=Patients.DELETE_TIP.format(name=patient.name))
        self.delete.clicked.connect(lambda: self.delete_clicked.emit(self.patient.id))
        _columns(layout, identity, [risk_cell, falls, last_fall, added, self.delete])

    def resizeEvent(self, event) -> None:
        """Elides the name and the notes to the width of their column."""
        super().resizeEvent(event)
        width = self._identity.width()
        self._elide(self.name, self.patient.name, "body-strong", width)
        if self.notes is not None:
            self._elide(self.notes, " ".join(self.patient.medical_notes.split()), "caption", width)

    @staticmethod
    def _elide(label: QLabel, text: str, role: str, width: int) -> None:
        label.setText(QFontMetrics(Type.font(role)).elidedText(text, Qt.TextElideMode.ElideRight, max(0, width)))


class PatientList(QWidget):
    """The Patients page's list: heading with the counter and "Add patient", then the table or the empty state.

    Signals:
        add_clicked: The user wants to add a patient.
        delete_clicked(int): The user wants to delete this patient (asked to confirm afterwards).
    """
    add_clicked = Signal()
    delete_clicked = Signal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(self._build_heading())
        layout.addSpacing(Space.S5)

        self.table = _card()
        self.table.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        table_layout = QVBoxLayout(self.table)
        table_layout.setContentsMargins(1, 1, 1, 1)
        table_layout.setSpacing(0)
        self._header = _HeaderRow()
        table_layout.addWidget(self._header)
        self._rows_widget = QWidget()
        self._rows = QVBoxLayout(self._rows_widget)
        self._rows.setContentsMargins(0, 0, 0, 0)
        self._rows.setSpacing(0)
        self._rows.addStretch(1)
        self._area = _FitScrollArea(self._rows_widget)
        bar = self._area.verticalScrollBar()
        bar.rangeChanged.connect(lambda _low, high: self._header.set_scrollbar_inset(bar.sizeHint().width() if high else 0))
        table_layout.addWidget(self._area)
        layout.addWidget(self.table)

        self.empty_card = _card()
        self.empty_card.setFixedHeight(EMPTY_HEIGHT)
        empty_layout = QVBoxLayout(self.empty_card)
        empty_layout.setContentsMargins(1, 1, 1, 1)
        self.empty = EmptyState(primary_action=True)
        self.empty.set_content(icon="user-plus", title=Patients.EMPTY_TITLE, text=Patients.EMPTY_TEXT,
                               action=Patients.ADD)
        self.empty.action_clicked.connect(self.add_clicked)
        empty_layout.addWidget(self.empty)
        layout.addWidget(self.empty_card)
        layout.addStretch(1)

        self.rows: list[PatientRow] = []
        self.set_patients([])

    def _build_heading(self) -> QHBoxLayout:
        heading = QHBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(Space.S4)
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(Space.S1)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(Space.S3)
        title_row.addWidget(make_label(Patients.TITLE, "title-lg"))
        self.counter = make_label("", "body", "tertiary")
        title_row.addWidget(self.counter, 0, Qt.AlignmentFlag.AlignBottom)
        title_row.addStretch(1)
        text.addLayout(title_row)
        text.addWidget(make_label(Patients.SUBTITLE, "body", "secondary"))
        heading.addLayout(text, 1)
        self.add_button = make_button(Patients.ADD, "primary", "md", "user-plus")
        self.add_button.clicked.connect(self.add_clicked)
        heading.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignVCenter)
        return heading

    def set_patients(self, patients: list[PatientSummary]) -> None:
        """Shows these patients (oldest first), or the empty state when there are none.

        Args:
            patients: The caregiver's patients.
        """
        focused = QApplication.focusWidget()
        had_focus = focused is not None and self.isAncestorOf(focused)
        for row in self.rows:          # out of the layout now; deleted when control returns to Qt
            self._rows.removeWidget(row)
            row.hide()
            row.deleteLater()
        self.rows = []
        for patient in patients:
            row = PatientRow(patient)
            row.delete_clicked.connect(self.delete_clicked)
            self._rows.insertWidget(self._rows.count() - 1, row)
            self.rows.append(row)
        if self.rows:
            self.rows[-1].ruled = False
        count = len(patients)
        self.counter.setText("" if count == 0 else Patients.COUNT_ONE if count == 1
                             else Patients.COUNT_MANY.format(n=count))
        self.add_button.setVisible(count > 0)       # the empty state has its own button
        self.table.setVisible(bool(patients))
        self.empty_card.setVisible(not patients)
        self._area.updateGeometry()                 # the card grows or shrinks with the rows
        if had_focus:           # the focused row (or empty state) may be gone: never land on a bin button
            self.focus_add()

    def focus_add(self) -> None:
        """Focuses the button that adds a patient (the one in the empty state when there are none)."""
        target = self.add_button if self.rows else self.empty.action_button()
        target.setFocus(Qt.FocusReason.OtherFocusReason)
