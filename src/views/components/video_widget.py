from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QWidget


class VideoWidget(QWidget):
    """
    Shows the latest video frame, scaled to fit and centred, keeping its aspect ratio.

    It replaces a QLabel with a QPixmap: the frame is painted straight from the QImage
    with `drawImage`, so there is no QPixmap conversion and no scaled copy per frame,
    and a resize only needs a repaint. Without a frame it shows `placeholder` (if any)
    in the widget's text colour. Background, colour, font and radius come from the QSS.
    """

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._image = QImage()
        self._placeholder = placeholder

    def set_image(self, image: QImage) -> None:
        self._image = image
        self.update()

    def clear(self) -> None:
        self._image = QImage()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._image.isNull():
            if self._placeholder:
                painter.setPen(self.palette().color(self.foregroundRole()))
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._placeholder)
        else:
            size = self._image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            target = QRect(0, 0, size.width(), size.height())
            target.moveCenter(self.rect().center())
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(target, self._image)
        painter.end()
