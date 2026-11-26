"""Button of the design system.

The stylesheet draws the bevel (fill, border, focus ring); the button paints its icon and
text itself so the 8 px icon gap, the loading spinner and a stable width are exact.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, QSize, Qt, QTimer, Slot
from PySide6.QtGui import QColor, QFontMetrics
from PySide6.QtWidgets import (
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
    QWidget,
)

from src.views import icons
from src.views.theme import Colors, Size, Type, set_props

_TEXT = {
    "primary": Colors.N0,
    "secondary": Colors.N900,
    "ghost": Colors.N700,
    "link": Colors.P600,
    "danger": Colors.R700,
    "on-dark": Colors.S100,
    "segment": Colors.N900,
}
_HEIGHT = {"sm": Size.H_SM, "md": Size.H_MD, "lg": Size.H_LG}
_PADDING = {"sm": 10, "md": 16, "lg": 16}
_ICON = 16
_GAP = 8


class Button(QPushButton):
    """Push button with a variant and a size; focus comes from the keyboard only.

    Args:
        text: Label.
        variant: primary, secondary, ghost, link, danger, on-dark or segment.
        size: sm (28 px), md (36 px), lg (40 px), or None for no fixed height.
        icon: Name of the icon drawn before the text, or None.
        parent: Parent widget.
    """

    def __init__(self, text: str = "", variant: str = "secondary", size: str | None = "md",
                 icon: str | None = None, parent: QWidget | None = None):
        super().__init__(text, parent)
        self._variant = variant
        self._size = size
        self._icon_name = icon
        self._reserved = 0
        self._loading = False
        self._idle_text = text
        self._frames: tuple = ()
        self._frame = 0
        self._spin = QTimer(self)
        self._spin.setInterval(80)
        self._spin.timeout.connect(self._advance_spinner)

        self.setProperty("variant", variant)
        if size:
            self.setProperty("size", size)
            self.setFixedHeight(_HEIGHT[size])
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        if variant == "link":
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    # ------------------------------------------------------------------ API
    def variant(self) -> str:
        """Returns the current variant."""
        return self._variant

    def set_variant(self, variant: str) -> None:
        """Changes the variant (and the stylesheet's look).

        Args:
            variant: primary, secondary, ghost, link, danger, on-dark or segment.
        """
        if variant != self._variant:
            self._variant = variant
            set_props(self, variant=variant)

    def set_icon_name(self, name: str | None) -> None:
        """Changes the icon drawn before the text.

        Args:
            name: Name of the icon, or None for no icon.
        """
        if name != self._icon_name:
            self._icon_name = name
            self.updateGeometry()
            self.update()

    def reserve_width(self, *texts: str) -> None:
        """Keeps the button as wide as its longest text, so changing the text never resizes it."""
        metrics = QFontMetrics(self._font())
        self._reserved = max(metrics.horizontalAdvance(text) for text in texts) if texts else 0
        self.updateGeometry()

    def set_loading(self, loading: bool, text: str | None = None) -> None:
        """Disables the button, optionally changes its text and shows a spinner in place of the icon."""
        if loading == self._loading:
            if loading and text:
                self.setText(text)
            return
        self._loading = loading
        if loading:
            self._idle_text = self.text()
            if text:
                self.setText(text)
            self._frames = icons.spinner_frames(Colors.N400 if self._variant != "on-dark" else Colors.S300)
            self._frame = 0
            self.setEnabled(False)
            self._spin.start()
        else:
            self._spin.stop()
            self.setText(self._idle_text)
            self.setEnabled(True)
        self.update()

    # ------------------------------------------------------------------ geometry
    def _font(self):
        if self._variant == "segment" and not self.isChecked():
            return Type.font("body")
        return Type.font("body-strong")

    def _content_width(self) -> int:
        metrics = QFontMetrics(Type.font("body-strong"))
        text_width = max(metrics.horizontalAdvance(self.text()), self._reserved)
        has_icon = bool(self._icon_name) or self._loading
        if not self.text():
            return _ICON if has_icon else 0
        return text_width + (_ICON + _GAP if has_icon else 0)

    def sizeHint(self) -> QSize:
        """Preferred size: text (or reserved width), icon and padding."""
        padding = 0 if self._variant == "link" else _PADDING.get(self._size or "md", 16)
        if not self.text() and self._icon_name:   # square icon button
            side = _HEIGHT.get(self._size or "md", Size.H_MD)
            return QSize(side, side)
        width = self._content_width() + 2 * padding + 2 + (4 if self._variant == "link" else 0)
        height = _HEIGHT.get(self._size, Type.line_height("body") + 4) if self._size else Size.H_MD
        return QSize(width, height)

    def minimumSizeHint(self) -> QSize:
        """The button never shrinks below its preferred size."""
        return self.sizeHint()

    # ------------------------------------------------------------------ painting
    @Slot()
    def _advance_spinner(self) -> None:
        self._frame = (self._frame + 1) % len(self._frames)
        self.update()   # repaint only; setIcon would post a relayout every frame

    def _text_color(self) -> str:
        if not self.isEnabled():
            return Colors.S300 if self._variant == "on-dark" else Colors.N400
        if self._variant == "segment" and self.isChecked():
            return Colors.N0
        return _TEXT.get(self._variant, Colors.N900)

    def paintEvent(self, event) -> None:
        """Paints the bevel from the stylesheet, then the icon (or spinner) and the text."""
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.text = ""
        painter.drawControl(QStyle.ControlElement.CE_PushButtonBevel, option)

        color = self._text_color()
        font = self._font()
        if self._variant == "link" and self.underMouse() and self.isEnabled():
            font.setUnderline(True)
        painter.setFont(font)
        painter.setPen(QColor(color))

        text = self.text()
        metrics = QFontMetrics(font)
        has_icon = bool(self._icon_name) or self._loading
        text_width = metrics.horizontalAdvance(text) if text else 0
        content = text_width + ((_ICON + (_GAP if text else 0)) if has_icon else 0)
        x = (self.width() - content) / 2
        rect = self.rect()

        if has_icon:
            icon_rect = QRect(round(x), (rect.height() - _ICON) // 2, _ICON, _ICON)
            if self._loading and self._frames:
                self._frames[self._frame].paint(painter, icon_rect)
            elif self._icon_name:
                pixmap = icons.icon_pixmap(self._icon_name, color, _ICON, self.devicePixelRatioF())
                painter.drawPixmap(icon_rect.topLeft(), pixmap)
            x += _ICON + _GAP
        if text:
            available = rect.width() - x
            shown = metrics.elidedText(text, Qt.TextElideMode.ElideRight, int(available)) if text_width > available else text
            painter.drawText(QRectF(x, 0, text_width + 1, rect.height()),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), shown)
        painter.end()

    def enterEvent(self, event) -> None:
        """Repaints a link button to underline it."""
        super().enterEvent(event)
        if self._variant == "link":
            self.update()

    def leaveEvent(self, event) -> None:
        """Repaints a link button to remove the underline."""
        super().leaveEvent(event)
        if self._variant == "link":
            self.update()

    def checkStateSet(self) -> None:
        """Repaints a checkable button when it is checked from code."""
        super().checkStateSet()
        self.update()


def make_button(text: str, variant: str = "secondary", size: str = "md", icon: str | None = None,
                *, tooltip: str = "", accessible_name: str = "", parent: QWidget | None = None) -> Button:
    """Factory for the design system's buttons."""
    button = Button(text, variant, size, icon, parent)
    if tooltip:
        button.setToolTip(tooltip)
    if accessible_name or not text:
        button.setAccessibleName(accessible_name or tooltip)
    return button
