from PySide6.QtCore import QRectF, QSize, Qt, QTime
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QTextOption
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
)

from src.views.theme import Colors, Radius, Space, mono_font

ROLE_TYPE = Qt.ItemDataRole.UserRole
ROLE_TIME = Qt.ItemDataRole.UserRole + 1
ROLE_MESSAGE = Qt.ItemDataRole.UserRole + 2


class _EventDelegate(QStyledItemDelegate):
    """Paints each event as a card: time, a typed badge and a wrapped message."""

    PAD_X = 12
    PAD_Y = 10
    GAP = 5
    LINE_H = 16
    V_MARGIN = 2

    @staticmethod
    def _scheme(event_type: str):
        """Return (background, border, badge_text, badge_background)."""
        if event_type == "ALERT":
            return Colors.DANGER_SOFT, Colors.DANGER_BORDER, Colors.DANGER, Colors.DANGER_SOFT_STRONG
        if event_type == "INFO":
            return Colors.SURFACE, Colors.BORDER, Colors.PRIMARY, Colors.PRIMARY_SOFT
        return Colors.SURFACE, Colors.BORDER, Colors.TEXT_MUTED, Colors.SURFACE_ALT

    def _available_width(self, option) -> int:
        view = self.parent()
        if isinstance(view, QAbstractItemView):
            return max(int(view.viewport().width()), 120)
        return max(int(option.rect.width()), 120)

    def sizeHint(self, option, index):
        width = self._available_width(option)
        if index.data(ROLE_TYPE) is None:
            return QSize(width, 56)

        font = QFont(option.font)
        font.setPixelSize(12)
        metrics = QFontMetrics(font)
        text_w = max(width - 2 * self.PAD_X, 40)
        message = str(index.data(ROLE_MESSAGE) or "")
        msg_h = metrics.boundingRect(
            0, 0, text_w, 10000, int(Qt.TextFlag.TextWordWrap), message
        ).height()
        total = self.PAD_Y + self.LINE_H + self.GAP + msg_h + self.PAD_Y + 2 * self.V_MARGIN
        return QSize(width, total)

    def paint(self, painter, option, index):
        event_type = index.data(ROLE_TYPE)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Empty-state hint row
        if event_type is None:
            font = QFont(option.font)
            font.setPixelSize(12)
            painter.setFont(font)
            painter.setPen(QColor(Colors.TEXT_SUBTLE))
            text_opt = QTextOption(Qt.AlignmentFlag.AlignCenter)
            text_opt.setWrapMode(QTextOption.WrapMode.WordWrap)
            painter.drawText(
                QRectF(option.rect),
                str(index.data(Qt.ItemDataRole.DisplayRole) or ""),
                text_opt,
            )
            painter.restore()
            return

        event_type = str(event_type)
        background, border, badge_fg, badge_bg = self._scheme(event_type)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)

        card = QRectF(option.rect).adjusted(0, self.V_MARGIN, 0, -self.V_MARGIN)
        painter.setPen(QPen(QColor(Colors.PRIMARY if selected else border), 1))
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(card.adjusted(0.5, 0.5, -0.5, -0.5), Radius.MD, Radius.MD)

        x = card.left() + self.PAD_X
        y = card.top() + self.PAD_Y

        # Time (monospace)
        time_text = str(index.data(ROLE_TIME) or "")
        time_font = mono_font(11)
        painter.setFont(time_font)
        painter.setPen(QColor(Colors.TEXT_MUTED))
        time_w = QFontMetrics(time_font).horizontalAdvance(time_text)
        painter.drawText(
            QRectF(x, y, time_w + 2, self.LINE_H),
            time_text,
            QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
        )

        # Type badge
        badge_font = QFont(option.font)
        badge_font.setPixelSize(10)
        badge_font.setWeight(QFont.Weight.Bold)
        badge_w = QFontMetrics(badge_font).horizontalAdvance(event_type) + 16
        badge_rect = QRectF(x + time_w + 10, y, badge_w, self.LINE_H)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(badge_bg))
        painter.drawRoundedRect(badge_rect, self.LINE_H / 2, self.LINE_H / 2)
        painter.setFont(badge_font)
        painter.setPen(QColor(badge_fg))
        painter.drawText(badge_rect, event_type, QTextOption(Qt.AlignmentFlag.AlignCenter))

        # Message
        msg_font = QFont(option.font)
        msg_font.setPixelSize(12)
        painter.setFont(msg_font)
        painter.setPen(QColor(Colors.TEXT_MAIN if event_type == "ALERT" else Colors.TEXT_BODY))
        msg_opt = QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        msg_opt.setWrapMode(QTextOption.WrapMode.WordWrap)
        msg_rect = QRectF(
            x,
            y + self.LINE_H + self.GAP,
            card.width() - 2 * self.PAD_X,
            card.bottom() - (y + self.LINE_H + self.GAP) - 2,
        )
        painter.drawText(msg_rect, str(index.data(ROLE_MESSAGE) or ""), msg_opt)

        painter.restore()


class EventLog(QFrame):
    """Component for displaying system events and alerts with a formal layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("panel")
        self._empty_hint_active = False
        self._build_ui()

    def _build_ui(self):
        log_wrapper = QVBoxLayout(self)
        log_wrapper.setContentsMargins(*Space.PANEL)
        log_wrapper.setSpacing(10)

        log_header = QHBoxLayout()
        log_title = QLabel("Event log")
        log_title.setObjectName("sectionTitle")
        log_header.addWidget(log_title)
        log_header.addStretch()

        clear_btn = QPushButton("Clear log")
        clear_btn.setObjectName("subtle")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_events)
        log_header.addWidget(clear_btn)
        log_wrapper.addLayout(log_header)

        self.event_list = QListWidget()
        self.event_list.setObjectName("eventLog")
        self.event_list.setMinimumHeight(120)
        self.event_list.setWordWrap(True)
        self.event_list.setFrameShape(QFrame.Shape.NoFrame)
        self.event_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.event_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.event_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.event_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.event_list.setItemDelegate(_EventDelegate(self.event_list))
        log_wrapper.addWidget(self.event_list, 1)
        self._refresh_empty_log_hint()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Wrapped messages change height with the available width.
        self.event_list.doItemsLayout()

    def add_event(self, event_type: str, message: str):
        if self._empty_hint_active:
            self.event_list.clear()
            self._empty_hint_active = False

        timestamp = QTime.currentTime().toString("HH:mm:ss")
        item = QListWidgetItem(f"[{timestamp}]  {event_type}  —  {message}")
        item.setData(ROLE_TYPE, event_type)
        item.setData(ROLE_TIME, timestamp)
        item.setData(ROLE_MESSAGE, message)
        self.event_list.insertItem(0, item)

    def clear_events(self):
        self.event_list.clear()
        self._refresh_empty_log_hint()

    def _refresh_empty_log_hint(self):
        self.event_list.clear()
        hint = QListWidgetItem("System nominal. No alerts recorded.")
        hint.setFlags(Qt.ItemFlag.NoItemFlags)
        self.event_list.addItem(hint)
        self._empty_hint_active = True
