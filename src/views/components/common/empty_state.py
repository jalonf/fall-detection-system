"""Empty state: a 32 px icon in a 56 px tile, a title, a line of text and an optional action."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal, Slot
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from src.views import icons
from src.views.components.common.button import Button
from src.views.components.common.painting import draw_lines, wrap_text
from src.views.components.common.spinner import make_rotation, paint_arc
from src.views.theme import Colors, Type

_TILE = 40          # room for the 32 px icon (painted without a tile behind it)
_ICON = 32
_MAX_TEXT = 360


class EmptyState(QWidget):
    """Centred icon (or spinner), title, text and optional action, for areas with no content.

    Args:
        on_dark: Drawn on the dark video stage.
        primary_action: The action is the only way forward (a primary button, not a secondary one).
        parent: Parent widget.

    Signals:
        action_clicked: The action button was pressed.
    """
    action_clicked = Signal()

    def __init__(self, *, on_dark: bool = False, primary_action: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self._on_dark = on_dark
        self._icon: str | None = None
        self._icon_color: str | None = None
        self._spinner = False
        self._title = ""
        self._text = ""
        self._angle = 0.0
        self._rotation = make_rotation(self, self._on_angle)
        variant = "on-dark" if on_dark else "primary" if primary_action else "secondary"
        self._action = Button("", variant, "md", parent=self)
        self._action.hide()
        self._action.clicked.connect(self.action_clicked)
        if on_dark:
            self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def set_content(self, *, icon: str | None = None, icon_color: str | None = None, spinner: bool = False,
                    title: str = "", text: str = "", action: str | None = None) -> None:
        """Changes what is shown.

        Args:
            icon: Name of the icon, or None.
            icon_color: Colour of the icon (or spinner); None uses the default.
            spinner: Show a spinner instead of the icon.
            title: Title.
            text: Line of text under the title.
            action: Text of the action button, or None to hide it.
        """
        self._icon, self._icon_color, self._spinner = icon, icon_color, spinner
        self._title, self._text = title, text
        self.setAccessibleName(title)
        self.setAccessibleDescription(text)
        if action:
            self._action.setText(action)
            self._action.adjustSize()
            self._action.show()
        else:
            self._action.hide()
        if spinner and self.isVisible():
            self._rotation.start()
        elif not spinner:
            self._rotation.stop()
        self._place_action()
        self.update()

    def action_button(self) -> Button:
        """Returns the action button."""
        return self._action

    @Slot("QVariant")
    def _on_angle(self, angle) -> None:
        self._angle = float(angle)
        self.update(self._tile_rect().toAlignedRect())

    def showEvent(self, event) -> None:
        """Starts the spinner if it is shown."""
        super().showEvent(event)
        if self._spinner:
            self._rotation.start()

    def hideEvent(self, event) -> None:
        """Stops the spinner while hidden."""
        super().hideEvent(event)
        self._rotation.stop()

    def resizeEvent(self, event) -> None:
        """Keeps the action button under the text."""
        super().resizeEvent(event)
        self._place_action()

    # ------------------------------------------------------------------ layout
    def _text_width(self) -> int:
        return min(_MAX_TEXT, max(120, self.width() - 48))

    def _lines(self) -> tuple[str, ...]:
        return wrap_text(self._text, Type.font("body"), self._text_width(), 3)

    def _content_height(self) -> int:
        height = _TILE + 12 + Type.line_height("title-sm")
        lines = self._lines()
        if lines:
            height += 4 + len(lines) * Type.line_height("body")
        if self._action.isVisibleTo(self):
            height += 20 + self._action.height()
        return height

    def _top(self) -> float:
        return max(8.0, (self.height() - self._content_height()) / 2)

    def _tile_rect(self) -> QRectF:
        return QRectF((self.width() - _TILE) / 2, self._top(), _TILE, _TILE)

    def _place_action(self) -> None:
        if not self._action.isVisibleTo(self):
            return
        bottom = self._top() + self._content_height()
        self._action.move(round((self.width() - self._action.width()) / 2), round(bottom - self._action.height()))

    # ------------------------------------------------------------------ painting
    def paintEvent(self, event) -> None:
        """Paints the icon (or spinner), the title and the wrapped text, centred."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._on_dark:
            painter.fillRect(self.rect(), QColor(Colors.S900))

        # The icon sits straight on the background: no tile, no box around it.
        tile = self._tile_rect()
        icon_rect = QRectF(tile.center().x() - _ICON / 2, tile.center().y() - _ICON / 2, _ICON, _ICON)
        default_color = Colors.S300 if self._on_dark else Colors.N500
        if self._spinner:
            spinner_rect = QRectF(tile.center().x() - 12, tile.center().y() - 12, 24, 24)
            paint_arc(painter, spinner_rect, self._angle, self._icon_color or (Colors.S100 if self._on_dark else Colors.P600))
        elif self._icon:
            pixmap = icons.icon_pixmap(self._icon, self._icon_color or default_color, _ICON, self.devicePixelRatioF())
            painter.drawPixmap(icon_rect.topLeft(), pixmap)

        y = tile.bottom() + 12
        painter.setFont(Type.font("title-sm"))
        painter.setPen(QColor(Colors.S100 if self._on_dark else Colors.N900))
        width = self._text_width()
        x = (self.width() - width) / 2
        title = painter.fontMetrics().elidedText(self._title, Qt.TextElideMode.ElideRight, width)
        y = draw_lines(painter, (title,), x, y, width, Type.line_height("title-sm"), Qt.AlignmentFlag.AlignHCenter)
        lines = self._lines()
        if lines:
            painter.setFont(Type.font("body"))
            painter.setPen(QColor(Colors.S300 if self._on_dark else Colors.N600))
            draw_lines(painter, lines, x, y + 4, width, Type.line_height("body"), Qt.AlignmentFlag.AlignHCenter)
