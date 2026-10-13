"""
Resolution-independent line icons drawn with QPainter (24x24 design grid).
No image assets required; every icon is rendered at 2x for crisp HiDPI output.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QLineEdit

from src.views.theme import Colors

_SCALE = 2


def _paths(name: str):
    """Return (list_of_paths, filled) for an icon expressed in a 24x24 grid."""
    paths = []
    filled = False

    if name == "play":
        p = QPainterPath()
        p.moveTo(8, 5)
        p.lineTo(19, 12)
        p.lineTo(8, 19)
        p.closeSubpath()
        paths.append(p)
        filled = True

    elif name == "stop":
        p = QPainterPath()
        p.addRoundedRect(QRectF(6, 6, 12, 12), 2.5, 2.5)
        paths.append(p)
        filled = True

    elif name == "camera":
        body = QPainterPath()
        body.addRoundedRect(QRectF(3, 7, 18, 13), 3, 3)
        top = QPainterPath()
        top.moveTo(8.5, 7)
        top.lineTo(10, 4.5)
        top.lineTo(14, 4.5)
        top.lineTo(15.5, 7)
        lens = QPainterPath()
        lens.addEllipse(QPointF(12, 13.5), 3.2, 3.2)
        paths.extend([body, top, lens])

    elif name == "upload":
        stem = QPainterPath()
        stem.moveTo(12, 15.5)
        stem.lineTo(12, 4.5)
        head = QPainterPath()
        head.moveTo(7.5, 9)
        head.lineTo(12, 4.5)
        head.lineTo(16.5, 9)
        tray = QPainterPath()
        tray.moveTo(4.5, 15)
        tray.lineTo(4.5, 19.5)
        tray.lineTo(19.5, 19.5)
        tray.lineTo(19.5, 15)
        paths.extend([stem, head, tray])

    elif name == "bell":
        dome = QPainterPath()
        dome.moveTo(6, 17)
        dome.lineTo(6, 11)
        dome.arcTo(QRectF(6, 5, 12, 12), 180, -180)
        dome.lineTo(18, 17)
        dome.closeSubpath()
        clapper = QPainterPath()
        clapper.moveTo(10, 20.5)
        clapper.lineTo(14, 20.5)
        paths.extend([dome, clapper])

    elif name == "logout":
        door = QPainterPath()
        door.moveTo(10, 4.5)
        door.lineTo(5, 4.5)
        door.lineTo(5, 19.5)
        door.lineTo(10, 19.5)
        shaft = QPainterPath()
        shaft.moveTo(9.5, 12)
        shaft.lineTo(20, 12)
        head = QPainterPath()
        head.moveTo(16, 8)
        head.lineTo(20, 12)
        head.lineTo(16, 16)
        paths.extend([door, shaft, head])

    elif name in ("eye", "eye_off"):
        outline = QPainterPath()
        outline.moveTo(2.5, 12)
        outline.cubicTo(6, 5.5, 18, 5.5, 21.5, 12)
        outline.cubicTo(18, 18.5, 6, 18.5, 2.5, 12)
        pupil = QPainterPath()
        pupil.addEllipse(QPointF(12, 12), 3, 3)
        paths.extend([outline, pupil])
        if name == "eye_off":
            slash = QPainterPath()
            slash.moveTo(4, 4)
            slash.lineTo(20, 20)
            paths.append(slash)

    elif name == "arrow_left":
        shaft = QPainterPath()
        shaft.moveTo(19, 12)
        shaft.lineTo(5, 12)
        head = QPainterPath()
        head.moveTo(11, 6)
        head.lineTo(5, 12)
        head.lineTo(11, 18)
        paths.extend([shaft, head])

    elif name == "check":
        p = QPainterPath()
        p.moveTo(5, 12.5)
        p.lineTo(10, 17.5)
        p.lineTo(19, 7.5)
        paths.append(p)

    elif name == "close":
        a = QPainterPath()
        a.moveTo(6.5, 6.5)
        a.lineTo(17.5, 17.5)
        b = QPainterPath()
        b.moveTo(17.5, 6.5)
        b.lineTo(6.5, 17.5)
        paths.extend([a, b])

    elif name == "info":
        ring = QPainterPath()
        ring.addEllipse(QPointF(12, 12), 9, 9)
        stem = QPainterPath()
        stem.moveTo(12, 11)
        stem.lineTo(12, 16.5)
        dot = QPainterPath()
        dot.moveTo(12, 7.8)
        dot.lineTo(12, 7.85)
        paths.extend([ring, stem, dot])

    elif name == "warning":
        tri = QPainterPath()
        tri.moveTo(12, 4)
        tri.lineTo(21, 19.5)
        tri.lineTo(3, 19.5)
        tri.closeSubpath()
        stem = QPainterPath()
        stem.moveTo(12, 10)
        stem.lineTo(12, 14.2)
        dot = QPainterPath()
        dot.moveTo(12, 16.9)
        dot.lineTo(12, 16.95)
        paths.extend([tri, stem, dot])

    elif name == "error":
        ring = QPainterPath()
        ring.addEllipse(QPointF(12, 12), 9, 9)
        a = QPainterPath()
        a.moveTo(9, 9)
        a.lineTo(15, 15)
        b = QPainterPath()
        b.moveTo(15, 9)
        b.lineTo(9, 15)
        paths.extend([ring, a, b])

    elif name == "mail":
        body = QPainterPath()
        body.addRoundedRect(QRectF(3.5, 5.5, 17, 13), 3, 3)
        flap = QPainterPath()
        flap.moveTo(4.5, 8)
        flap.lineTo(12, 13.2)
        flap.lineTo(19.5, 8)
        paths.extend([body, flap])

    elif name == "lock":
        body = QPainterPath()
        body.addRoundedRect(QRectF(5, 10.5, 14, 10), 3, 3)
        shackle = QPainterPath()
        shackle.moveTo(8.5, 10.5)
        shackle.lineTo(8.5, 7)
        shackle.arcTo(QRectF(8.5, 3.5, 7, 7), 180, -180)
        shackle.lineTo(15.5, 10.5)
        paths.extend([body, shackle])

    elif name == "user":
        head = QPainterPath()
        head.addEllipse(QPointF(12, 8), 3.6, 3.6)
        shoulders = QPainterPath()
        shoulders.moveTo(5, 20)
        shoulders.cubicTo(5, 15.5, 8.2, 14, 12, 14)
        shoulders.cubicTo(15.8, 14, 19, 15.5, 19, 20)
        paths.extend([head, shoulders])

    elif name == "phone":
        body = QPainterPath()
        body.addRoundedRect(QRectF(7, 3, 10, 18), 2.5, 2.5)
        speaker = QPainterPath()
        speaker.moveTo(11, 17.5)
        speaker.lineTo(13, 17.5)
        paths.extend([body, speaker])

    elif name == "note":
        body = QPainterPath()
        body.addRoundedRect(QRectF(5, 3.5, 14, 17), 3, 3)
        l1 = QPainterPath()
        l1.moveTo(8.5, 9)
        l1.lineTo(15.5, 9)
        l2 = QPainterPath()
        l2.moveTo(8.5, 13)
        l2.lineTo(13, 13)
        paths.extend([body, l1, l2])

    return paths, filled


def _render(name: str, color: str, size: int) -> QPixmap:
    pixmap = QPixmap(size * _SCALE, size * _SCALE)
    pixmap.fill(Qt.GlobalColor.transparent)
    pixmap.setDevicePixelRatio(_SCALE)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 24.0, size / 24.0)

    paths, filled = _paths(name)
    qcolor = QColor(color)
    pen = QPen(qcolor, 1.9 if not filled else 1.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(qcolor if filled else Qt.BrushStyle.NoBrush)

    for path in paths:
        painter.drawPath(path)

    painter.end()
    return pixmap


def icon(name: str, color: str = Colors.TEXT_INVERSE, size: int = 18,
         disabled: str = Colors.TEXT_SUBTLE) -> QIcon:
    """Build a QIcon with distinct normal and disabled renderings."""
    result = QIcon()
    result.addPixmap(_render(name, color, size), QIcon.Mode.Normal)
    result.addPixmap(_render(name, disabled, size), QIcon.Mode.Disabled)
    return result


def attach_password_toggle(edit: QLineEdit) -> QAction:
    """Add a show/hide eye button inside a password QLineEdit (UI-only behaviour)."""
    action = QAction(icon("eye", Colors.TEXT_MUTED), "", edit)
    action.setCheckable(True)
    action.setToolTip("Show password")

    def _toggle(checked: bool):
        edit.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
        action.setIcon(icon("eye_off" if checked else "eye", Colors.TEXT_MUTED))
        action.setToolTip("Hide password" if checked else "Show password")

    action.toggled.connect(_toggle)
    edit.addAction(action, QLineEdit.ActionPosition.TrailingPosition)
    return action


def attach_leading_icon(edit: QLineEdit, name: str) -> QAction:
    """Place a subtle, non-interactive icon at the start of a QLineEdit."""
    action = edit.addAction(icon(name, Colors.TEXT_SUBTLE, 18), QLineEdit.ActionPosition.LeadingPosition)
    return action
