from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTime
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
    """
    Paints the event log as a timeline: a coloured dot per event type, a monospace
    time, the type name and a wrapped message. Only alerts get a tinted card, so
    the rare, important rows stand out from routine ones.
    """

    PAD_X = 12
    PAD_Y = 10
    GAP = 4
    LINE_H = 16
    V_MARGIN = 2
    DOT = 7
    INDENT = 17          # message and time start after the dot

    @staticmethod
    def _scheme(event_type: str):
        """Return (card background, card border, accent colour, type label)."""
        if event_type == "ALERT":
            return Colors.DANGER_SOFT, Colors.DANGER_BORDER, Colors.DANGER, "Alert"
        if event_type == "INFO":
            return None, None, Colors.PRIMARY, "Info"
        return None, None, Colors.TEXT_MUTED, event_type.capitalize()

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
        text_w = max(width - 2 * self.PAD_X - self.INDENT, 40)
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
        background, border, accent, label = self._scheme(event_type)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

        card = QRectF(option.rect).adjusted(0, self.V_MARGIN, 0, -self.V_MARGIN)

        # Row surface: tinted for alerts, subtle highlight on hover / selection.
        if background is not None:
            painter.setPen(QPen(QColor(border), 1))
            painter.setBrush(QColor(background))
            painter.drawRoundedRect(card.adjusted(0.5, 0.5, -0.5, -0.5), Radius.MD, Radius.MD)
        elif selected or hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(Colors.HOVER_TINT if hovered and not selected else Colors.PRIMARY_SOFT))
            painter.drawRoundedRect(card, Radius.MD, Radius.MD)
        else:
            # Hairline between routine rows keeps the list readable without boxes.
            painter.setPen(QPen(QColor(Colors.BORDER), 1))
            painter.drawLine(
                QPointF(card.left() + self.PAD_X, card.bottom()),
                QPointF(card.right() - self.PAD_X, card.bottom()),
            )

        x = card.left() + self.PAD_X
        y = card.top() + self.PAD_Y

        # Type dot, vertically centred on the first line
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(accent))
        painter.drawEllipse(QPointF(x + self.DOT / 2, y + self.LINE_H / 2), self.DOT / 2, self.DOT / 2)

        text_x = x + self.INDENT

        # Time (monospace)
        time_text = str(index.data(ROLE_TIME) or "")
        time_font = mono_font(11)
        painter.setFont(time_font)
        painter.setPen(QColor(Colors.TEXT_MUTED))
        time_w = QFontMetrics(time_font).horizontalAdvance(time_text)
        painter.drawText(
            QRectF(text_x, y, time_w + 2, self.LINE_H),
            time_text,
            QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
        )

        # Type name, right-aligned in the accent colour
        label_font = QFont(option.font)
        label_font.setPixelSize(11)
        label_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(label_font)
        painter.setPen(QColor(Colors.DANGER_TEXT if event_type == "ALERT" else accent))
        painter.drawText(
            QRectF(card.left() + self.PAD_X, y, card.width() - 2 * self.PAD_X, self.LINE_H),
            label,
            QTextOption(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
        )

        # Message
        msg_font = QFont(option.font)
        msg_font.setPixelSize(12)
        painter.setFont(msg_font)
        painter.setPen(QColor(Colors.TEXT_MAIN if event_type == "ALERT" else Colors.TEXT_BODY))
        msg_opt = QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        msg_opt.setWrapMode(QTextOption.WrapMode.WordWrap)
        msg_rect = QRectF(
            text_x,
            y + self.LINE_H + self.GAP,
            card.width() - 2 * self.PAD_X - self.INDENT,
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
        self.event_list.setMouseTracking(True)
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
