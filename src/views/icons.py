"""FallSense icon set: 24-unit grid, 1.5 stroke, round caps and joins, no fill.

Icons take the colour of the text around them, so every request names its colour. Rendered
pixmaps are cached per (name, colour, size, device pixel ratio).
"""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QIcon,
    QImage,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer

from src.views.theme import Colors

ICONS: dict[str, str] = {
    "play": '<path d="M7.5 4.8v14.4a.8.8 0 0 0 1.2.7l11.3-7.2a.8.8 0 0 0 0-1.4L8.7 4.1a.8.8 0 0 0-1.2.7z"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="1.5"/>',
    "upload": '<path d="M12 15V4.5M7.5 9 12 4.5 16.5 9M4.5 15v3.5A1.5 1.5 0 0 0 6 20h12a1.5 1.5 0 0 0 1.5-1.5V15"/>',
    "camera": '<rect x="2.5" y="6.5" width="13" height="11" rx="2"/><path d="m15.5 10.5 4.7-3a.8.8 0 0 1 1.3.7v7.6a.8.8 0 0 1-1.3.7l-4.7-3"/>',
    "film": '<rect x="3.5" y="3.5" width="17" height="17" rx="2"/><path d="M7.5 3.5v17M16.5 3.5v17M3.5 8h4M3.5 12h17M3.5 16h4M16.5 8h4M16.5 16h4"/>',
    "alert-triangle": '<path d="M10.3 4.3 2.9 17.2A2 2 0 0 0 4.6 20.2h14.8a2 2 0 0 0 1.7-3L13.7 4.3a2 2 0 0 0-3.4 0z"/><path d="M12 9.5v4M12 16.8h.01"/>',
    "alert-circle": '<circle cx="12" cy="12" r="8.5"/><path d="M12 8v4.5M12 15.8h.01"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "check-circle": '<circle cx="12" cy="12" r="8.5"/><path d="m8.5 12.2 2.4 2.4 4.8-4.9"/>',
    "x": '<path d="m6.5 6.5 11 11M17.5 6.5l-11 11"/>',
    "info": '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8.2h.01"/>',
    "log-out": '<path d="M9.5 20H6a1.5 1.5 0 0 1-1.5-1.5v-13A1.5 1.5 0 0 1 6 4h3.5M15.5 16.5 20 12l-4.5-4.5M20 12H9.5"/>',
    "log-in": '<path d="M14.5 4H18a1.5 1.5 0 0 1 1.5 1.5v13A1.5 1.5 0 0 1 18 20h-3.5M10 16.5 14.5 12 10 7.5M14.5 12H4"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5a7.5 7.5 0 0 1 15 0"/>',
    "user-plus": '<circle cx="10" cy="8" r="4"/><path d="M3 20.5a7 7 0 0 1 14 0M19 8v6M16 11h6"/>',
    "mail": '<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    "lock": '<rect x="4.5" y="10.5" width="15" height="10" rx="2"/><path d="M8 10.5v-3a4 4 0 0 1 8 0v3"/>',
    "eye": '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
    "eye-off": '<path d="M10.6 5.6a9.7 9.7 0 0 1 1.4-.1c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-2.6 3.4M6.6 6.6C3.9 8.3 2.5 12 2.5 12S6 18.5 12 18.5a9.6 9.6 0 0 0 5.4-1.6M9.9 9.9a3 3 0 0 0 4.2 4.2M3.5 3.5l17 17"/>',
    "phone": '<path d="M20.5 16.4v2.6a1.7 1.7 0 0 1-1.9 1.7 17 17 0 0 1-7.3-2.6 16.6 16.6 0 0 1-5.1-5.1 17 17 0 0 1-2.6-7.4 1.7 1.7 0 0 1 1.7-1.9h2.6a1.7 1.7 0 0 1 1.7 1.5c.1.8.3 1.6.6 2.4a1.7 1.7 0 0 1-.4 1.8l-1.1 1.1a13.6 13.6 0 0 0 5.1 5.1l1.1-1.1a1.7 1.7 0 0 1 1.8-.4c.8.3 1.6.5 2.4.6a1.7 1.7 0 0 1 1.4 1.7z"/>',
    "chevron-down": '<path d="m6.5 9.5 5.5 5.5 5.5-5.5"/>',
    "chevron-left": '<path d="M14.5 6.5 9 12l5.5 5.5"/>',
    "chevron-right": '<path d="M9.5 6.5 15 12l-5.5 5.5"/>',
    "more-horizontal": '<path d="M6 12h.01M12 12h.01M18 12h.01" stroke-width="2.6"/>',
    "download": '<path d="M12 4.5V15M7.5 10.5 12 15l4.5-4.5M4.5 15v3.5A1.5 1.5 0 0 0 6 20h12a1.5 1.5 0 0 0 1.5-1.5V15"/>',
    "trash": '<path d="M4 6.5h16M9.5 6.5v-2h5v2M6 6.5l1 13a1.5 1.5 0 0 0 1.5 1.5h7a1.5 1.5 0 0 0 1.5-1.5l1-13M10 10.5v6M14 10.5v6"/>',
    "activity": '<path d="M3 12h4l2.5-6.5 5 13L17 12h4"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "bell": '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 2h-15zM10 20.5a2.2 2.2 0 0 0 4 0"/>',
    "shield": '<path d="M12 3.5 5 6v5.5c0 4.4 3 7.9 7 9 4-1.1 7-4.6 7-9V6z"/>',
}

_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
)


def app_dpr() -> float:
    """Device pixel ratio of the primary screen (1.0 before the application exists)."""
    app = QGuiApplication.instance()
    return app.devicePixelRatio() if app is not None else 1.0


@lru_cache(maxsize=512)
def _render(name: str, color: str, size: int, dpr: float) -> QPixmap:
    svg = _SVG.format(color=color, body=ICONS[name]).encode("utf-8")
    renderer = QSvgRenderer(QByteArray(svg))
    side = max(1, round(size * dpr))
    image = QImage(side, side, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, side, side))
    painter.end()
    pixmap = QPixmap.fromImage(image)
    pixmap.setDevicePixelRatio(dpr)
    return pixmap


def icon_pixmap(name: str, color: str, size: int = 16, dpr: float | None = None) -> QPixmap:
    """Pixmap of an icon, rendered for `dpr` (the primary screen's when omitted)."""
    return _render(name, color, size, round(dpr if dpr is not None else app_dpr(), 2))


@lru_cache(maxsize=256)
def _icon(name: str, color: str, size: int, disabled: str, dpr: float) -> QIcon:
    result = QIcon()
    result.addPixmap(_render(name, color, size, dpr), QIcon.Mode.Normal, QIcon.State.Off)
    result.addPixmap(_render(name, disabled, size, dpr), QIcon.Mode.Disabled, QIcon.State.Off)
    return result


def icon(name: str, color: str, size: int = 16, *, disabled: str = Colors.N400) -> QIcon:
    """QIcon with a normal and a disabled (N400) pixmap."""
    return _icon(name, color, size, disabled, round(app_dpr(), 2))


SPINNER_FRAMES = 12


@lru_cache(maxsize=32)
def _spinner_frames(color: str, size: int, dpr: float) -> tuple[QIcon, ...]:
    frames = []
    side = max(1, round(size * dpr))
    stroke = 2.0 * dpr if size >= 16 else 1.75 * dpr
    for index in range(SPINNER_FRAMES):
        image = QImage(side, side, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(color), stroke)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        inset = stroke / 2 + dpr
        rect = QRectF(inset, inset, side - 2 * inset, side - 2 * inset)
        painter.translate(QPointF(side / 2, side / 2))
        painter.rotate(index * 360 / SPINNER_FRAMES)
        painter.translate(QPointF(-side / 2, -side / 2))
        painter.drawArc(rect, 90 * 16, -270 * 16)
        painter.end()
        pixmap = QPixmap.fromImage(image)
        pixmap.setDevicePixelRatio(dpr)
        frames.append(QIcon(pixmap))
    return tuple(frames)


def spinner_frames(color: str, size: int = 16) -> tuple[QIcon, ...]:
    """Twelve pre-rendered frames of a 270-degree arc, for spinners inside buttons."""
    return _spinner_frames(color, size, round(app_dpr(), 2))
