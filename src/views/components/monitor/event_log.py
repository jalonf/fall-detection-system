"""Event log: model/view table of the session's events, newest first, with a type filter."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import (
    QAbstractTableModel,
    QDateTime,
    QModelIndex,
    QRect,
    QRectF,
    QSettings,
    QSize,
    QSortFilterProxyModel,
    Qt,
    QTime,
    Slot,
)
from PySide6.QtGui import QAction, QColor, QGuiApplication, QKeySequence, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHeaderView,
    QMenu,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QToolTip,
    QWidget,
)

from src.views.components.common.badge import Badge
from src.views.components.common.button import make_button
from src.views.components.common.confirm_dialog import ConfirmDialog
from src.views.components.common.inputs import Combo
from src.views.components.common.panel import Panel
from src.views.components.common.toast import ToastHost
from src.views.strings import Log, Toasts, event_count
from src.views.theme import Colors, Type

ROW_HEIGHT = 36
HEADER_HEIGHT = 32
_PADDING = 12
BADGE_VARIANTS = {"INFO": "neutral", "ERROR": "danger", "ALERT": "danger-solid"}
SETTINGS_FILTER = "monitor/log_filter"
_ROOT = QModelIndex()


@dataclass(frozen=True)
class LogEntry:
    time: QTime
    kind: str
    message: str


class EventLogModel(QAbstractTableModel):
    TypeRole = Qt.ItemDataRole.UserRole + 1
    TimeRole = Qt.ItemDataRole.UserRole + 2
    MAX_ROWS = 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[LogEntry] = []      # newest first

    def rowCount(self, parent=_ROOT) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=_ROOT) -> int:
        return 0 if parent.isValid() else len(Log.COLUMNS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        entry = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return (entry.time.toString("HH:mm:ss"), entry.kind, entry.message)[index.column()]
        if role == self.TypeRole:
            return entry.kind
        if role == self.TimeRole:
            return entry.time
        if role == Qt.ItemDataRole.AccessibleTextRole:
            return f"{entry.time.toString('HH:mm:ss')}, {entry.kind}, {entry.message}"
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return Log.COLUMNS[section]
        return None

    def add_event(self, kind: str, message: str, when: QTime | None = None) -> None:
        if len(self._rows) >= self.MAX_ROWS:
            last = len(self._rows) - 1
            self.beginRemoveRows(QModelIndex(), last, last)
            self._rows.pop()
            self.endRemoveRows()
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._rows.insert(0, LogEntry(when or QTime.currentTime(), kind, message))
        self.endInsertRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._rows.clear()
        self.endResetModel()

    def entries(self) -> list[LogEntry]:
        return list(self._rows)


class EventFilterProxy(QSortFilterProxyModel):
    FILTERS: ClassVar[dict[str, frozenset[str] | None]] = {
        "all": None, "alerts": frozenset({"ALERT"}), "errors": frozenset({"ERROR"}), "info": frozenset({"INFO"}),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._key = "all"

    def set_filter(self, key: str) -> None:
        if key in self.FILTERS and key != self._key:
            self._key = key
            self.invalidateRowsFilter()

    def filter_key(self) -> str:
        return self._key

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        kinds = self.FILTERS[self._key]
        if kinds is None:
            return True
        index = self.sourceModel().index(source_row, 0, source_parent)
        return index.data(EventLogModel.TypeRole) in kinds


class EventTypeDelegate(QStyledItemDelegate):
    """Paints every cell: row background (ALERT R50, selection P50, hover N50), divider, time,
    type badge, description and the 3 px bar on ALERT rows."""

    def __init__(self, table: EventTable):
        super().__init__(table)
        self._table = table

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(option.rect.width(), ROW_HEIGHT)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        rect = option.rect
        kind = index.data(EventLogModel.TypeRole)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = index.row() == self._table.hovered_row
        painter.save()
        if selected:
            painter.fillRect(rect, QColor(Colors.P50))
        elif kind == "ALERT":
            painter.fillRect(rect, QColor(Colors.R50))
        elif hovered:
            painter.fillRect(rect, QColor(Colors.N50))
        painter.fillRect(QRect(rect.left(), rect.bottom(), rect.width(), 1), QColor(Colors.N150))

        column = index.column()
        if column == 0:
            if kind == "ALERT":
                painter.fillRect(QRect(rect.left(), rect.top(), 3, rect.height()), QColor(Colors.R600))
            painter.setFont(Type.font("body", tabular=True))
            painter.setPen(QColor(Colors.N600))
            painter.drawText(rect.adjusted(_PADDING, 0, -4, 0),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), index.data())
        elif column == 1:
            width = Badge.width_for(kind)
            badge = QRect(rect.left() + _PADDING, rect.top() + (rect.height() - 20) // 2, width, 20)
            Badge.paint(painter, QRectF(badge), kind, BADGE_VARIANTS.get(kind, "neutral"))
        else:
            painter.setFont(Type.font("body"))
            painter.setPen(QColor(Colors.N900))
            text_rect = rect.adjusted(_PADDING, 0, -_PADDING, 0)
            text = painter.fontMetrics().elidedText(index.data() or "", Qt.TextElideMode.ElideRight, text_rect.width())
            painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)
        painter.restore()


class EventTable(QTableView):
    def __init__(self, model, parent: QWidget | None = None):
        super().__init__(parent)
        self.hovered_row = -1
        self.setModel(model)
        self.setItemDelegate(EventTypeDelegate(self))
        vertical = self.verticalHeader()
        vertical.hide()
        vertical.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vertical.setDefaultSectionSize(ROW_HEIGHT)
        header = self.horizontalHeader()
        header.setFixedHeight(HEADER_HEIGHT)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setHighlightSections(False)
        header.setSectionsClickable(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 88)
        header.resizeSection(1, 96)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setMouseTracking(True)
        self.setAccessibleName(Log.TABLE_NAME)
        self.viewport().setAutoFillBackground(False)

        copy = QAction(self)
        copy.setShortcut(QKeySequence(QKeySequence.StandardKey.Copy))
        copy.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        copy.triggered.connect(self.copy_selection)
        self.addAction(copy)

    @Slot()
    def copy_selection(self) -> None:
        rows = sorted({index.row() for index in self.selectionModel().selectedRows()})
        model = self.model()
        lines = ["\t".join(model.index(row, column).data() or "" for column in range(3)) for row in rows]
        if lines:
            QGuiApplication.clipboard().setText("\n".join(lines))

    # ------------------------------------------------------------------ hover and tooltips
    def _set_hovered(self, row: int) -> None:
        if row == self.hovered_row:
            return
        for old in (self.hovered_row, row):
            if old >= 0:
                self.viewport().update(QRect(0, self.rowViewportPosition(old), self.viewport().width(), ROW_HEIGHT))
        self.hovered_row = row

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        self._set_hovered(self.rowAt(round(event.position().y())))

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self._set_hovered(-1)

    def viewportEvent(self, event) -> bool:
        if event.type() == event.Type.ToolTip:
            index = self.indexAt(event.pos())
            text = index.data() if index.isValid() and index.column() == 2 else None
            available = self.columnWidth(2) - 2 * _PADDING
            if text and self.fontMetrics().horizontalAdvance(text) > available:
                QToolTip.showText(event.globalPos(), text, self.viewport())
            else:
                QToolTip.hideText()
                event.ignore()
            return True
        return super().viewportEvent(event)

    # ------------------------------------------------------------------ empty state
    def paintEvent(self, event) -> None:
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
    def __init__(self, settings: QSettings, parent: QWidget | None = None):
        super().__init__(Log.TITLE, flush=True, parent=parent)
        self.setMinimumHeight(176)
        self._settings = settings
        self.model = EventLogModel(self)
        self.proxy = EventFilterProxy(self)
        self.proxy.setSourceModel(self.model)
        self.table = EventTable(self.proxy)
        self.body_layout().addWidget(self.table)

        self.filter_combo = Combo([label for _, label in Log.FILTERS], size="sm", width=132,
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
        self.setTabOrder(self.more, self.table)

        for signal in (self.proxy.rowsInserted, self.proxy.rowsRemoved, self.proxy.modelReset, self.proxy.layoutChanged):
            signal.connect(self._update_count)
        self._update_count()

    # ------------------------------------------------------------------ API
    def add_event(self, kind: str, message: str, when: QTime | None = None) -> None:
        self.model.add_event(kind, message, when)

    def total(self) -> int:
        return self.model.rowCount()

    def focus_table(self) -> None:
        self.table.setFocus(Qt.FocusReason.ShortcutFocusReason)
        if not self.table.currentIndex().isValid() and self.proxy.rowCount():
            self.table.selectRow(0)

    # ------------------------------------------------------------------ actions
    @Slot()
    def _update_count(self, *_args) -> None:
        self.set_subtitle(event_count(self.proxy.rowCount(), self.model.rowCount()))
        self.table.viewport().update()

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
        stamp = QDateTime.currentDateTime().toString("yyyyMMdd-HHmmss")
        default = str(Path.home() / Log.EXPORT_FILE_NAME.format(stamp=stamp))
        path, _ = QFileDialog.getSaveFileName(self, Log.EXPORT_DIALOG_TITLE, default, Log.EXPORT_FILTER)
        if not path:
            return
        toasts = ToastHost.for_widget(self)
        try:
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(Log.CSV_HEADER)
                for row in range(self.proxy.rowCount()):
                    writer.writerow([self.proxy.index(row, column).data() for column in range(3)])
        except OSError:
            toasts.error(Toasts.EXPORT_FAILED, title=Toasts.EXPORT_FAILED_TITLE)
            return
        toasts.success(Path(path).name, title=Toasts.EXPORTED_TITLE)

    @Slot()
    def confirm_clear(self) -> None:
        total = self.model.rowCount()
        if total == 0:
            return
        body = Log.CONFIRM_CLEAR_BODY_ONE if total == 1 else Log.CONFIRM_CLEAR_BODY.format(n=total)
        if ConfirmDialog.ask(self, Log.CONFIRM_CLEAR_TITLE, body, Log.CONFIRM_CLEAR_ACTION, destructive=True):
            self.model.clear()

