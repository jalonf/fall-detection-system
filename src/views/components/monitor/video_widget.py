"""Video surface: draws the latest QImage fitted with KeepAspectRatio on the stage colour.

Built for up to 30 fps without layout work: the size hint never changes, the target rectangle is
only recomputed on resize or when the frame size changes, and new frames only call `update()`.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.views.theme import Colors


class VideoWidget(QWidget):
    """Draws the latest frame fitted with KeepAspectRatio on the stage colour.

    Args:
        background: Colour around the image (and of the empty state).
        radius: Corner radius; corners are painted with `corner_color`.
        corner_color: Colour outside the rounded corners, or None.
        parent: Parent widget.
    """
    def __init__(self, background: str = Colors.STAGE, *, radius: int = 0, corner_color: str | None = None,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._background = QColor(background)
        self._radius = radius
        self._corner_color = QColor(corner_color) if corner_color else None
        self._image: QImage | None = None
        self._target = QRect()
        self._bands: tuple[QRect, ...] = ()

    # ------------------------------------------------------------------ API
    def set_image(self, image: QImage) -> None:
        """Shows a new frame; the target rectangle is only recomputed when the size changes.

        Args:
            image: The frame.
        """
        resized = self._image is None or image.size() != self._image.size()
        self._image = image
        if resized:
            self._update_target()
        self.update()

    def clear(self) -> None:
        """Removes the image."""
        if self._image is not None:
            self._image = None
            self._update_target()
            self.update()

    def has_image(self) -> bool:
        """True while an image is shown."""
        return self._image is not None

    def sizeHint(self) -> QSize:
        """Preferred size: 16:9."""
        return QSize(640, 360)

    def minimumSizeHint(self) -> QSize:
        """Smallest size of the video."""
        return QSize(160, 90)

    # ------------------------------------------------------------------ geometry
    def resizeEvent(self, event) -> None:
        """Recomputes where the image goes."""
        super().resizeEvent(event)
        self._update_target()

    def _update_target(self) -> None:
        rect = self.rect()
        if self._image is None or self._image.isNull() or rect.isEmpty():
            self._target = QRect()
            self._bands = (rect,)
            return
        size = self._image.size().scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRect(0, 0, size.width(), size.height())
        target.moveCenter(rect.center())
        self._target = target
        bands = []
        if target.left() > rect.left():
            bands.append(QRect(rect.left(), rect.top(), target.left() - rect.left(), rect.height()))
            bands.append(QRect(target.right() + 1, rect.top(), rect.right() - target.right(), rect.height()))
        if target.top() > rect.top():
            bands.append(QRect(rect.left(), rect.top(), rect.width(), target.top() - rect.top()))
            bands.append(QRect(rect.left(), target.bottom() + 1, rect.width(), rect.bottom() - target.bottom()))
        self._bands = tuple(bands)

    # ------------------------------------------------------------------ painting
    def paint_empty(self, painter: QPainter) -> None:
        """Hook: drawn over the background when there is no image."""

    def paint_overlay(self, painter: QPainter) -> None:
        """Hook: drawn over the image or the empty state."""

    def paintEvent(self, event) -> None:
        """Paints the image fitted in the widget (or the empty state) and the overlay."""
        painter = QPainter(self)
        if self._image is None:
            painter.fillRect(self.rect(), self._background)
            self.paint_empty(painter)
        else:
            for band in self._bands:
                painter.fillRect(band, self._background)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(self._target, self._image)
        self.paint_overlay(painter)
        if self._radius and self._corner_color is not None:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            outside = QPainterPath()
            outside.addRect(QRectF(self.rect()))
            inside = QPainterPath()
            inside.addRoundedRect(QRectF(self.rect()), self._radius, self._radius)
            painter.fillPath(outside.subtracted(inside), self._corner_color)
