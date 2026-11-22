"""Painting helpers shared by the painted components: soft shadows, wrapped text, small widgets."""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QImage,
    QPainter,
    QPainterPath,
    QPixmap,
    QTextLayout,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsBlurEffect,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QScrollArea,
    QSizePolicy,
    QWidget,
)

from src.views import icons
from src.views.theme import Colors


# ---------------------------------------------------------------------- shadows
@lru_cache(maxsize=48)
def shadow_pixmap(width: int, height: int, radius: int, blur: int, offset_y: int, alpha: float,
                  dpr: float) -> QPixmap:
    """Gaussian shadow of a rounded rectangle, `blur` pixels of margin on every side.

    The pixmap is (width + 2 * blur) x (height + 2 * blur) logical pixels; draw it at the card's
    top-left minus `blur`. It is blurred once and cached, so floating widgets above live video
    never blur again while they repaint.
    """
    full = QSize(width + 2 * blur, height + 2 * blur)
    source = QImage(round(full.width() * dpr), round(full.height() * dpr), QImage.Format.Format_ARGB32_Premultiplied)
    source.fill(Qt.GlobalColor.transparent)
    painter = QPainter(source)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(dpr, dpr)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(0, 0, 0, round(255 * alpha)))
    painter.drawRoundedRect(QRectF(blur, blur + offset_y, width, height), radius, radius)
    painter.end()

    scene = QGraphicsScene()
    item = QGraphicsPixmapItem(QPixmap.fromImage(source))
    effect = QGraphicsBlurEffect()
    effect.setBlurRadius(blur * dpr)
    effect.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
    item.setGraphicsEffect(effect)
    scene.addItem(item)
    result = QImage(source.size(), QImage.Format.Format_ARGB32_Premultiplied)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    scene.render(painter, QRectF(result.rect()), QRectF(source.rect()))
    painter.end()

    pixmap = QPixmap.fromImage(result)
    pixmap.setDevicePixelRatio(dpr)
    return pixmap


# ---------------------------------------------------------------------- text
_FONTS: dict[str, QFont] = {}


@lru_cache(maxsize=256)
def _wrapped(text: str, font_key: str, width: int, max_lines: int) -> tuple[str, ...]:
    if not text:
        return ()
    font = _FONTS[font_key]
    layout = QTextLayout(text, font)
    layout.beginLayout()
    spans: list[tuple[int, int]] = []
    while len(spans) < max_lines:
        line = layout.createLine()
        if not line.isValid():
            break
        line.setLineWidth(width)
        spans.append((line.textStart(), line.textLength()))
    layout.endLayout()

    lines = [text[start:start + length].rstrip() for start, length in spans]
    last_start = spans[-1][0] if spans else 0
    if spans and last_start + spans[-1][1] < len(text):
        metrics = QFontMetricsF(font)
        rest = text[last_start:].replace("\n", " ")
        lines[-1] = metrics.elidedText(rest, Qt.TextElideMode.ElideRight, width)
    return tuple(lines)


def wrap_text(text: str, font: QFont, width: int, max_lines: int = 3) -> tuple[str, ...]:
    """Lines of `text` wrapped to `width`; the last one is elided when more would be needed."""
    key = font.key()
    _FONTS.setdefault(key, QFont(font))
    return _wrapped(text, key, max(1, int(width)), max_lines)


def draw_lines(painter: QPainter, lines: tuple[str, ...], x: float, y: float, width: float,
               line_height: int, align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft) -> float:
    """Draws one line per `line_height`; returns the y below the last line."""
    for line in lines:
        painter.drawText(QRectF(x, y, width, line_height), int(align | Qt.AlignmentFlag.AlignVCenter), line)
        y += line_height
    return y


def rounded_path(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path


def crisp(rect: QRectF, pen_width: float = 1.0) -> QRectF:
    """Rectangle shifted half a pen so a 1 px stroke falls on whole pixels."""
    half = pen_width / 2
    return rect.adjusted(half, half, -half, -half)


# ---------------------------------------------------------------------- small widgets
class IconView(QWidget):
    """A painted icon, rendered for the screen it is on."""

    def __init__(self, name: str, color: str, size: int = 16, parent: QWidget | None = None):
        super().__init__(parent)
        self._name = name
        self._color = color
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_icon(self, name: str, color: str | None = None) -> None:
        self._name = name
        if color:
            self._color = color
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(0, 0, icons.icon_pixmap(self._name, self._color, self._size, self.devicePixelRatioF()))


class Divider(QWidget):
    """A 1 px line: horizontal (fills the width) or vertical with a fixed length."""

    def __init__(self, color: str = Colors.N150, *, vertical: bool = False, length: int = 0,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._color = QColor(color)
        if vertical:
            self.setFixedWidth(1)
            if length:
                self.setFixedHeight(length)
        else:
            self.setFixedHeight(1)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event) -> None:
        QPainter(self).fillRect(self.rect(), self._color)


def transparent_scroll_area(widget: QWidget, *, horizontal: bool = False) -> QScrollArea:
    """Frameless scroll area that lets its parent's background show through."""
    area = QScrollArea()
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setWidgetResizable(True)
    area.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAsNeeded if horizontal else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )
    area.setWidget(widget)
    area.viewport().setAutoFillBackground(False)
    widget.setAutoFillBackground(False)
    return area
