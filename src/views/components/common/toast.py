"""Toasts: every success and error message the user sees (except the fall alert and inline errors).

`ToastHost` lives in the top-level window, so toasts survive navigation between screens.
Each `Toast` is painted entirely (no child widgets) and animates its own opacity and offset.
"""

from __future__ import annotations

import time

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QElapsedTimer,
    QEvent,
    QObject,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QAccessible, QAccessibleEvent, QColor, QPainter
from PySide6.QtWidgets import QWidget

from src.views import icons
from src.views.components.common.painting import shadow_pixmap, wrap_text
from src.views.strings import Toasts
from src.views.theme import Colors, Motion, Radius, Type

KINDS = {
    "success": (Colors.G600, "check-circle", 3500),
    "info": (Colors.P600, "info", 4000),
    "warning": (Colors.A600, "alert-triangle", 5000),
    "error": (Colors.R600, "alert-circle", 7000),
}

WIDTH = 360
_MIN_HEIGHT = 64
_PAD_TOP, _PAD_RIGHT, _PAD_BOTTOM, _PAD_LEFT = 12, 12, 12, 16
_ICON = 20
_CLOSE = 24
_TEXT_X = _PAD_LEFT + _ICON + 12
_TEXT_WIDTH = WIDTH - _TEXT_X - _PAD_RIGHT - _CLOSE - 8
_BLUR, _SHADOW_DY, _SHADOW_ALPHA = 24, 8, 0.16
_MARGIN_X = _BLUR
_MARGIN_TOP = _BLUR - _SHADOW_DY
_MARGIN_BOTTOM = _BLUR + _SHADOW_DY
_GAP = 8
_MAX_TOASTS = 3
_DEDUP_SECONDS = 2.0


class Toast(QWidget):
    closed = Signal()

    def __init__(self, window: QWidget, kind: str, title: str, message: str, duration_ms: int):
        super().__init__(window)
        self.kind = kind
        self.message = message
        self._base_title = title
        self._count = 1
        self._duration = duration_ms
        self._remaining = duration_ms
        self._opacity = 0.0
        self._offset = -8.0
        self._closing = False
        self._hover_close = False
        self.created = time.monotonic()

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)
        self._clock = QElapsedTimer()

        self._animation = QParallelAnimationGroup(self)
        self._fade = QPropertyAnimation(self, b"opacity", self)
        self._slide = QPropertyAnimation(self, b"offset_y", self)
        for animation in (self._fade, self._slide):
            animation.setDuration(Motion.BASE)
            self._animation.addAnimation(animation)
        self._animation.finished.connect(self._on_animation_finished)

        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self._relayout()

    # ------------------------------------------------------------------ properties
    def _get_opacity(self) -> float:
        return self._opacity

    def _set_opacity(self, value: float) -> None:
        self._opacity = value
        self.update()

    def _get_offset(self) -> float:
        return self._offset

    def _set_offset(self, value: float) -> None:
        self._offset = value
        self.update()

    opacity = Property(float, _get_opacity, _set_opacity)
    offset_y = Property(float, _get_offset, _set_offset)

    # ------------------------------------------------------------------ content
    @property
    def title(self) -> str:
        return self._base_title if self._count == 1 else f"{self._base_title} ×{self._count}"

    def _lines(self) -> tuple[str, ...]:
        return wrap_text(self.message, Type.font("body"), _TEXT_WIDTH, 3)

    def card_height(self) -> int:
        lines = self._lines()
        height = _PAD_TOP + Type.line_height("title-sm") + _PAD_BOTTOM
        if lines:
            height += 2 + len(lines) * Type.line_height("body")
        return max(_MIN_HEIGHT, height)

    def _relayout(self) -> None:
        self.setFixedSize(WIDTH + 2 * _MARGIN_X, self.card_height() + _MARGIN_TOP + _MARGIN_BOTTOM)
        self.setAccessibleName(f"{self.title}. {self.message}")

    def card_offset(self) -> tuple[int, int]:
        """Position of the card inside the widget (the rest is room for the shadow)."""
        return _MARGIN_X, _MARGIN_TOP

    def _close_rect(self) -> QRect:
        return QRect(_MARGIN_X + WIDTH - _PAD_RIGHT - _CLOSE, _MARGIN_TOP + _PAD_TOP - 2, _CLOSE, _CLOSE)

    # ------------------------------------------------------------------ lifecycle
    def appear(self) -> None:
        self.show()
        self.raise_()
        self._run(1.0, 0.0, Motion.OUT)
        self._start_timer(self._duration)
        QAccessible.updateAccessibility(QAccessibleEvent(self, QAccessible.Event.Alert))

    def bump(self) -> None:
        """The same message arrived again: count it and restart the timer."""
        self._count += 1
        self.created = time.monotonic()
        self._relayout()
        self._start_timer(self._duration)
        self.update()

    @Slot()
    def dismiss(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._timer.stop()
        self._run(0.0, -8.0, Motion.IN)

    def is_closing(self) -> bool:
        return self._closing

    def _run(self, opacity: float, offset: float, curve) -> None:
        self._animation.stop()
        for animation, start, end in ((self._fade, self._opacity, opacity), (self._slide, self._offset, offset)):
            animation.setStartValue(start)
            animation.setEndValue(end)
            animation.setEasingCurve(QEasingCurve(curve))
        self._animation.start()

    @Slot()
    def _on_animation_finished(self) -> None:
        if self._closing:
            self.hide()
            self.closed.emit()
            self.deleteLater()

    def _start_timer(self, duration: int) -> None:
        self._remaining = duration
        if duration > 0 and not self.underMouse():
            self._clock.start()
            self._timer.start(duration)

    def pause(self) -> None:
        if self._timer.isActive():
            self._remaining = max(0, self._remaining - self._clock.elapsed())
            self._timer.stop()

    def resume(self) -> None:
        if self._duration > 0 and not self._closing and not self._timer.isActive():
            self._clock.start()
            self._timer.start(max(800, self._remaining))

    # ------------------------------------------------------------------ events
    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self.pause()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self._hover_close = False
        self.update()
        self.resume()

    def mouseMoveEvent(self, event) -> None:
        hover = self._close_rect().contains(event.position().toPoint())
        if hover != self._hover_close:
            self._hover_close = hover
            self.setCursor(Qt.CursorShape.PointingHandCursor if hover else Qt.CursorShape.ArrowCursor)
            self.update(self._close_rect())

    def mousePressEvent(self, event) -> None:
        if self._close_rect().contains(event.position().toPoint()):
            self.dismiss()
        event.accept()

    # ------------------------------------------------------------------ painting
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        painter.translate(0, self._offset)
        dpr = self.devicePixelRatioF()
        height = self.card_height()
        painter.drawPixmap(_MARGIN_X - _BLUR, _MARGIN_TOP - _BLUR,
                           shadow_pixmap(WIDTH, height, Radius.R_LG, _BLUR, _SHADOW_DY, _SHADOW_ALPHA, round(dpr, 2)))

        card = QRectF(_MARGIN_X + 0.5, _MARGIN_TOP + 0.5, WIDTH - 1, height - 1)
        painter.setPen(QColor(Colors.N200))
        painter.setBrush(QColor(Colors.N0))
        painter.drawRoundedRect(card, Radius.R_LG, Radius.R_LG)

        accent, icon_name, _ = KINDS[self.kind]
        painter.save()
        painter.setClipRect(QRectF(_MARGIN_X, _MARGIN_TOP, 3, height))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(accent))
        painter.drawRoundedRect(QRectF(_MARGIN_X, _MARGIN_TOP, 12, height), Radius.R_LG, Radius.R_LG)
        painter.restore()

        left, top = _MARGIN_X, _MARGIN_TOP
        painter.drawPixmap(left + _PAD_LEFT, top + _PAD_TOP, icons.icon_pixmap(icon_name, accent, _ICON, dpr))

        painter.setFont(Type.font("title-sm"))
        painter.setPen(QColor(Colors.N900))
        title_rect = QRectF(left + _TEXT_X, top + _PAD_TOP, _TEXT_WIDTH, Type.line_height("title-sm"))
        painter.drawText(title_rect, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                         painter.fontMetrics().elidedText(self.title, Qt.TextElideMode.ElideRight, _TEXT_WIDTH))

        painter.setFont(Type.font("body"))
        painter.setPen(QColor(Colors.N700))
        y = title_rect.bottom() + 2
        for line in self._lines():
            painter.drawText(QRectF(left + _TEXT_X, y, _TEXT_WIDTH, Type.line_height("body")),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), line)
            y += Type.line_height("body")

        close = self._close_rect()
        if self._hover_close:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(Colors.N100))
            painter.drawRoundedRect(QRectF(close), Radius.R_SM, Radius.R_SM)
        painter.drawPixmap(close.left() + 4, close.top() + 4, icons.icon_pixmap("x", Colors.N500, 16, dpr))


class ToastHost(QObject):
    """One per top-level window. Stacks up to three toasts in the top-right corner, or in the
    bottom-right one when a screen asks for it (`set_bottom_inset`)."""

    def __init__(self, window: QWidget):
        super().__init__(window)
        self._window = window
        self._toasts: list[Toast] = []          # newest first
        self._anchor = "top"
        self._inset = 16
        self._right = 16
        self._raise_timer = QTimer(self)
        self._raise_timer.setSingleShot(True)
        self._raise_timer.setInterval(0)
        self._raise_timer.timeout.connect(self._raise_all)
        window.installEventFilter(self)

    @classmethod
    def for_widget(cls, widget: QWidget) -> ToastHost:
        window = widget.window()
        host = window.findChild(ToastHost, options=Qt.FindChildOption.FindDirectChildrenOnly)
        return host if host is not None else cls(window)

    # ------------------------------------------------------------------ API
    def notify(self, kind: str, message: str, *, title: str | None = None, duration_ms: int | None = None) -> Toast:
        title = title or Toasts.KIND_TITLES[kind]
        duration = KINDS[kind][2] if duration_ms is None else duration_ms
        now = time.monotonic()
        for toast in self._toasts:
            if (not toast.is_closing() and toast.kind == kind and toast.message == message
                    and now - toast.created < _DEDUP_SECONDS):
                toast.bump()
                self._reposition()
                return toast

        toast = Toast(self._window, kind, title, message, duration)
        toast.closed.connect(self._on_closed)
        self._toasts.insert(0, toast)
        open_toasts = [t for t in self._toasts if not t.is_closing()]
        for extra in open_toasts[_MAX_TOASTS:]:
            extra.dismiss()
        self._reposition()
        toast.appear()
        return toast

    def success(self, message: str, *, title: str | None = None, duration_ms: int | None = None) -> Toast:
        return self.notify("success", message, title=title, duration_ms=duration_ms)

    def error(self, message: str, *, title: str | None = None, duration_ms: int | None = None) -> Toast:
        return self.notify("error", message, title=title, duration_ms=duration_ms)

    def warning(self, message: str, *, title: str | None = None, duration_ms: int | None = None) -> Toast:
        return self.notify("warning", message, title=title, duration_ms=duration_ms)

    def info(self, message: str, *, title: str | None = None, duration_ms: int | None = None) -> Toast:
        return self.notify("info", message, title=title, duration_ms=duration_ms)

    def dismiss(self, toast: Toast | None) -> None:
        if toast is not None and toast in self._toasts:
            toast.dismiss()

    def set_top_inset(self, pixels: int) -> None:
        """Stacks the toasts downwards from `pixels` below the top edge, newest first."""
        if (self._anchor, self._inset, self._right) != ("top", pixels, 16):
            self._anchor, self._inset, self._right = "top", pixels, 16
            self._reposition()

    def set_bottom_inset(self, pixels: int, right: int = 24) -> None:
        """Stacks the toasts upwards from `pixels` above the bottom edge (and `right` from the right
        edge), newest nearest the edge."""
        if (self._anchor, self._inset, self._right) != ("bottom", pixels, right):
            self._anchor, self._inset, self._right = "bottom", pixels, right
            self._reposition()

    def toasts(self) -> list[Toast]:
        return [toast for toast in self._toasts if not toast.is_closing()]

    # ------------------------------------------------------------------ placement
    @Slot()
    def _on_closed(self) -> None:
        toast = self.sender()
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._reposition()

    def _reposition(self) -> None:
        right = self._window.width() - self._right
        if self._anchor == "top":
            y = self._inset
            for toast in self._toasts:
                card_x, card_y = toast.card_offset()
                toast.move(right - WIDTH - card_x, y - card_y)
                y += toast.card_height() + _GAP
            return
        bottom = self._window.height() - self._inset
        for toast in self._toasts:
            card_x, card_y = toast.card_offset()
            top = bottom - toast.card_height()
            toast.move(right - WIDTH - card_x, top - card_y)
            bottom = top - _GAP

    @Slot()
    def _raise_all(self) -> None:
        for toast in reversed(self._toasts):
            toast.raise_()

    def eventFilter(self, watched, event) -> bool:
        if watched is self._window:
            if event.type() == QEvent.Type.Resize:
                self._reposition()
            elif event.type() == QEvent.Type.ChildAdded and self._toasts:
                # Something new (e.g. the router's transition overlay) may cover the toasts.
                self._raise_timer.start()
        return False
