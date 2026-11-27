"""Event log: a feed of the session's events, newest first, with a type filter.

Each event is a two-line row (type badge and time, then the description), so the log reads
naturally in a narrow, tall column without cutting the descriptions.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import (
    QAbstractTableModel,
    QDateTime,
    QModelIndex,
    QPersistentModelIndex,
    QRect,
    QRectF,
    QSettings,
    QSize,
    QSortFilterProxyModel,
    Qt,
    QTime,
    Slot,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QFontMetrics,
    QGuiApplication,
    QKeySequence,
    QPainter,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QListView,
    QMenu,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolTip,
    QWidget,
)

from src.strings import Log, event_count
from src.views.components.common.badge import Badge
from src.views.components.common.button import make_button
from src.views.components.common.confirm_dialog import ConfirmDialog
from src.views.components.common.inputs import Combo
from src.views.components.common.panel import Panel
from src.views.theme import Colors, Type

ROW_HEIGHT = 56
_PADDING = 16
BADGE_VARIANTS = {"INFO": "neutral", "ERROR": "danger", "ALERT": "danger-solid"}
SETTINGS_FILTER = "monitor/log_filter"
_FILTER_CHROME = 48     # popup row: 12 px before the text, 36 after it for the check mark
_ROOT = QModelIndex()


@dataclass(frozen=True)
class LogEntry:
    """One event of the log: when, its type (INFO, ERROR or ALERT) and its description."""
    time: QTime
    kind: str
    message: str


class EventLogModel(QAbstractTableModel):
    """The session's events, newest first, at most `MAX_ROWS`."""
    TypeRole = Qt.ItemDataRole.UserRole + 1
    TimeRole = Qt.ItemDataRole.UserRole + 2
    MessageRole = Qt.ItemDataRole.UserRole + 3
    MAX_ROWS = 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[LogEntry] = []      # newest first

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT) -> int:
        """Returns the number of events (it is a flat list)."""
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT) -> int:
        """Returns the number of columns: time, type and description."""
        return 0 if parent.isValid() else len(Log.COLUMNS)

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Returns an event's time, type or description for the display and custom roles."""
        if not index.isValid():
            return None
        entry = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return (entry.time.toString("HH:mm:ss"), Log.KIND_LABELS.get(entry.kind, entry.kind),
                    entry.message)[index.column()]
        if role == self.TypeRole:
            return entry.kind
        if role == self.TimeRole:
            return entry.time
        if role == self.MessageRole:
            return entry.message
        if role == Qt.ItemDataRole.AccessibleTextRole:
            label = Log.KIND_LABELS.get(entry.kind, entry.kind)
            return f"{entry.time.toString('HH:mm:ss')}, {label}, {entry.message}"
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        """Returns the column titles."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return Log.COLUMNS[section]
        return None

    def add_event(self, kind: str, message: str, when: QTime | None = None) -> None:
        """Adds an event at the top, dropping the oldest one past `MAX_ROWS`.

        Args:
            kind: "INFO", "ERROR" or "ALERT".
            message: Description.
            when: Time of the event; None uses the current time.
        """
        if len(self._rows) >= self.MAX_ROWS:
            last = len(self._rows) - 1
            self.beginRemoveRows(QModelIndex(), last, last)
            self._rows.pop()
            self.endRemoveRows()
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._rows.insert(0, LogEntry(when or QTime.currentTime(), kind, message))
        self.endInsertRows()

    def clear(self) -> None:
        """Removes every event."""
        self.beginResetModel()
        self._rows.clear()
        self.endResetModel()


class EventFilterProxy(QSortFilterProxyModel):
    """Shows all the events, or only those of one type."""
    FILTERS: ClassVar[dict[str, frozenset[str] | None]] = {
        "all": None, "alerts": frozenset({"ALERT"}), "errors": frozenset({"ERROR"}), "info": frozenset({"INFO"}),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._key = "all"

    def set_filter(self, key: str) -> None:
        """Changes the filter.

        Args:
            key: "all", "alerts", "errors" or "info".
        """
        if key in self.FILTERS and key != self._key:
            self._key = key
            self.invalidateRowsFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        """Accepts the events whose type the filter shows."""
        kinds = self.FILTERS[self._key]
        if kinds is None:
            return True
        index = self.sourceModel().index(source_row, 0, source_parent)
        return index.data(EventLogModel.TypeRole) in kinds


class EventFeedDelegate(QStyledItemDelegate):
    """Paints each event as a two-line row: badge and time, then the description.

    ALERT rows get an R50 fill and a 3 px R600 bar; selection P50; hover N50.
    """

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        """Every row is `ROW_HEIGHT` tall."""
        return QSize(option.rect.width(), ROW_HEIGHT)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        """Paints one event (see the class docstring)."""
        rect = option.rect
        kind = index.data(EventLogModel.TypeRole) or "INFO"
        time = index.data(EventLogModel.TimeRole)
        message = index.data(EventLogModel.MessageRole) or ""
        painter.save()
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(Colors.P50))
        elif kind == "ALERT":
            painter.fillRect(rect, QColor(Colors.R50))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(rect, QColor(Colors.N50))
        if kind == "ALERT":
            painter.fillRect(QRect(rect.left(), rect.top(), 3, rect.height()), QColor(Colors.R600))
        painter.fillRect(QRect(rect.left(), rect.bottom(), rect.width(), 1), QColor(Colors.N150))

        x = rect.left() + _PADDING
        width = rect.width() - 2 * _PADDING
        label = Log.KIND_LABELS.get(kind, kind)
        badge_width = Badge.width_for(label)
        Badge.paint(painter, QRectF(x, rect.top() + 8, badge_width, 20), label, BADGE_VARIANTS.get(kind, "neutral"))
        painter.setFont(Type.font("caption", tabular=True))
        painter.setPen(QColor(Colors.N600))
        painter.drawText(QRect(x + badge_width + 8, rect.top() + 8, width - badge_width - 8, 20),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                         time.toString("HH:mm:ss") if time is not None else "")

        painter.setFont(Type.font("body"))
        painter.setPen(QColor(Colors.N900))
        text = painter.fontMetrics().elidedText(message, Qt.TextElideMode.ElideRight, width)
        painter.drawText(QRect(x, rect.top() + 30, width, 20),
                         int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)
        painter.restore()


class EventList(QListView):
    """The list of events, with copy (Ctrl+C) and tooltips for cut descriptions."""
    def __init__(self, model, parent: QWidget | None = None):
        super().__init__(parent)
        self.setModel(model)
        self.setModelColumn(0)
        self.setItemDelegate(EventFeedDelegate(self))
        self.setUniformItemSizes(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setFrameShape(QListView.Shape.NoFrame)
        self.setMouseTracking(True)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.viewport().setAutoFillBackground(False)
        self.setAccessibleName(Log.TABLE_NAME)

        copy = QAction(self)
        copy.setShortcut(QKeySequence(QKeySequence.StandardKey.Copy))
        copy.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        copy.triggered.connect(self.copy_selection)
        self.addAction(copy)

    @Slot()
    def copy_selection(self) -> None:
        """Copies the selected events as tab-separated lines (time, type, description)."""
        rows = sorted({index.row() for index in self.selectionModel().selectedIndexes()})
        model = self.model()
        lines = ["\t".join(model.index(row, column).data() or "" for column in range(3)) for row in rows]
        if lines:
            QGuiApplication.clipboard().setText("\n".join(lines))

    def viewportEvent(self, event) -> bool:
        """Shows a tooltip only for descriptions cut by the row's width."""
        if event.type() == event.Type.ToolTip:
            index = self.indexAt(event.pos())
            text = index.data(EventLogModel.MessageRole) if index.isValid() else None
            available = self.viewport().width() - 2 * _PADDING
            if text and QFontMetrics(Type.font("body")).horizontalAdvance(text) > available:
                QToolTip.showText(event.globalPos(), text, self.viewport())
            else:
                QToolTip.hideText()
                event.ignore()
            return True
        return super().viewportEvent(event)

    def paintEvent(self, event) -> None:
        """Paints the rows, or a message when there are none to show."""
        super().paintEvent(event)
        model = self.model()
        if model.rowCount() == 0:
            source = model.sourceModel() if isinstance(model, QSortFilterProxyModel) else model
            text = Log.EMPTY if source.rowCount() == 0 else Log.EMPTY_FILTERED
            painter = QPainter(self.viewport())
            painter.setFont(Type.font("body"))
            painter.setPen(QColor(Colors.N500))
            painter.drawText(self.viewport().rect(), int(Qt.AlignmentFlag.AlignCenter), text)


class EventLogPanel(Panel):
    """Event log panel: the list, its type filter and the export / clear menu.

    Args:
        settings: Where the chosen filter is remembered.
        parent: Parent widget.
    """
    def __init__(self, settings: QSettings, parent: QWidget | None = None):
        super().__init__(Log.TITLE, flush=True, parent=parent)
        self.setMinimumHeight(200)
        self._settings = settings
        self.model = EventLogModel(self)
        self.proxy = EventFilterProxy(self)
        self.proxy.setSourceModel(self.model)
        self.events = EventList(self.proxy)
        self.body_layout().addWidget(self.events)

        # Just wide enough for the longest filter in its popup row (bold when current, check mark).
        widest = max(QFontMetrics(Type.font("body-strong")).horizontalAdvance(label) for _, label in Log.FILTERS)
        self.filter_combo = Combo([label for _, label in Log.FILTERS], size="sm", width=widest + _FILTER_CHROME,
                                  accessible_name=Log.FILTER_NAME)
        keys = [key for key, _ in Log.FILTERS]
        saved = str(settings.value(SETTINGS_FILTER, "all"))
        self.filter_combo.setCurrentIndex(keys.index(saved) if saved in keys else 0)
        self.proxy.set_filter(keys[self.filter_combo.currentIndex()])
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        self.add_action(self.filter_combo)

        self.more = make_button("", "ghost", "sm", "more-horizontal", tooltip=Log.MORE)
        self.menu = QMenu(self)
        self.export_action = self.menu.addAction(Log.EXPORT)
        self.clear_action = self.menu.addAction(Log.CLEAR)
        self.export_action.triggered.connect(self.export_csv)
        self.clear_action.triggered.connect(self.confirm_clear)
        self.menu.aboutToShow.connect(self._sync_menu)
        self.more.clicked.connect(self._open_menu)
        self.add_action(self.more)
        self.setTabOrder(self.filter_combo, self.more)
        self.setTabOrder(self.more, self.events)

        for signal in (self.proxy.rowsInserted, self.proxy.rowsRemoved, self.proxy.modelReset, self.proxy.layoutChanged):
            signal.connect(self._update_count)
        self._update_count()

    # ------------------------------------------------------------------ API
    def add_event(self, kind: str, message: str, when: QTime | None = None) -> None:
        """Adds an event to the log.

        Args:
            kind: "INFO", "ERROR" or "ALERT".
            message: Description.
            when: Time of the event; None uses the current time.
        """
        self.model.add_event(kind, message, when)

    def total(self) -> int:
        """Returns the number of events in the log, whatever the filter shows."""
        return self.model.rowCount()

    @Slot()
    def focus_events(self) -> None:
        """Focuses the list (Ctrl+L) and selects the newest event if none is."""
        self.events.setFocus(Qt.FocusReason.ShortcutFocusReason)
        if not self.events.currentIndex().isValid() and self.proxy.rowCount():
            self.events.setCurrentIndex(self.proxy.index(0, 0))

    # ------------------------------------------------------------------ actions
    @Slot()
    def _update_count(self, *_args) -> None:
        self.set_subtitle(event_count(self.proxy.rowCount(), self.model.rowCount()))
        self.events.viewport().update()

    @Slot(int)
    def _on_filter_changed(self, index: int) -> None:
        key = Log.FILTERS[index][0]
        self.proxy.set_filter(key)
        self._settings.setValue(SETTINGS_FILTER, key)
        self._update_count()

    @Slot()
    def _open_menu(self) -> None:
        self.menu.popup(self.more.mapToGlobal(self.more.rect().bottomLeft()))

    @Slot()
    def _sync_menu(self) -> None:
        has_rows = self.model.rowCount() > 0
        self.export_action.setEnabled(self.proxy.rowCount() > 0)
        self.clear_action.setEnabled(has_rows)

    @Slot()
    def export_csv(self) -> None:
        """Opens Windows' save dialog (native, so it is modal) and writes the visible rows."""
        stamp = QDateTime.currentDateTime().toString("yyyyMMdd-HHmmss")
        default = str(Path.home() / Log.EXPORT_FILE_NAME.format(stamp=stamp))
        path, _ = QFileDialog.getSaveFileName(self, Log.EXPORT_DIALOG_TITLE, default, Log.EXPORT_FILTER)
        if path:
            self._write_csv(path)

    def _write_csv(self, path: str) -> None:
        try:
            # UTF-8 with a BOM: without it Excel on Windows reads accented file names as mojibake.
            with open(path, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(Log.CSV_HEADER)
                for row in range(self.proxy.rowCount()):
                    writer.writerow([self.proxy.index(row, column).data() for column in range(3)])
        except OSError:
            self.add_event("ERROR", Log.EXPORT_FAILED.format(name=Path(path).name))

    @Slot()
    def confirm_clear(self) -> None:
        """Asks for confirmation and clears the log."""
        total = self.model.rowCount()
        if total == 0:
            return
        body = Log.CONFIRM_CLEAR_BODY_ONE if total == 1 else Log.CONFIRM_CLEAR_BODY.format(n=total)
        if ConfirmDialog.ask(self, Log.CONFIRM_CLEAR_TITLE, body, Log.CONFIRM_CLEAR_ACTION, destructive=True):
            self.model.clear()

