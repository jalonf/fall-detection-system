from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QFont, QPainter, QPixmap, QRadialGradient
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.views.components.pose_backdrop import PoseBackdrop
from src.views.theme import APP_NAME, Colors, set_prop, with_alpha

_DOT_PITCH = 24
_COLUMN_MAX = 1000
_LARGE_FROM = 1100       # panel widths where the type steps up / down (see `[scale=...]` in the QSS)
_SMALL_BELOW = 640

_EYEBROW = (
    f'{APP_NAME[:-5].upper()}<span style="color: {Colors.PRIMARY};">{APP_NAME[-5:].upper()}</span>'
)
_HEADLINE = (
    "Real-time fall detection<br>and "
    f'<span style="color: {Colors.PRIMARY};">risk monitoring</span>'
)
_DESCRIPTION = (
    f"{APP_NAME} follows a patient's posture through a camera with MediaPipe Pose and a "
    "recurrent neural network, and alerts the caregiver the moment a fall happens."
)
# (value, caption)
_FACTS = (("33", "pose landmarks"), ("2", "parallel threads"), ("15–30", "FPS by risk level"))


class BrandPanel(QWidget):
    """
    Left side of the authentication screen, on the canvas colour: one centred column with
    the name in capitals, the fall-sequence figure drawn straight on the canvas, the headline with a
    short description, and three key figures under a hairline. A faint dot grid and a soft
    glow behind it run behind everything. Column and type grow with the window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("brandPanel")
        self._dots: QPixmap | None = None
        self._dots_dpr = 0.0
        self._build_ui()

    def _build_ui(self):
        # The content is one column, centred in the panel and capped in width so it keeps
        # its proportions on very large screens.
        outer = QHBoxLayout(self)
        outer.setContentsMargins(48, 40, 24, 40)
        outer.setSpacing(0)

        column = QWidget()
        column.setMaximumWidth(_COLUMN_MAX)
        outer.addStretch(1)
        outer.addWidget(column, 100)
        outer.addStretch(1)

        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)

        layout.addLayout(self._build_eyebrow())
        layout.addSpacing(28)

        self.pose_figure = PoseBackdrop()
        self.pose_figure.setMaximumHeight(520)
        layout.addWidget(self.pose_figure, 10)
        layout.addSpacing(40)

        headline = QLabel(_HEADLINE)
        headline.setObjectName("brandHeadline")
        headline.setTextFormat(Qt.TextFormat.RichText)
        headline.setWordWrap(True)
        layout.addWidget(headline)
        layout.addSpacing(14)

        description = QLabel(_DESCRIPTION)
        description.setObjectName("brandDesc")
        description.setWordWrap(True)
        description.setMaximumWidth(680)
        layout.addWidget(description)
        layout.addSpacing(32)

        rule = QFrame()
        rule.setObjectName("brandRule")
        rule.setFixedHeight(1)
        layout.addWidget(rule)
        layout.addSpacing(16)
        layout.addLayout(self._build_facts())

        layout.addStretch(1)

    @staticmethod
    def _build_eyebrow() -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(16)

        accent = QFrame()
        accent.setObjectName("brandAccent")
        accent.setFixedSize(34, 4)
        row.addWidget(accent, 0, Qt.AlignmentFlag.AlignVCenter)

        eyebrow = QLabel(_EYEBROW)
        eyebrow.setObjectName("brandEyebrow")
        eyebrow.setTextFormat(Qt.TextFormat.RichText)
        font = eyebrow.font()
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 5.0)
        eyebrow.setFont(font)
        row.addWidget(eyebrow, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        return row

    @staticmethod
    def _build_facts() -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        for index, (value, caption) in enumerate(_FACTS):
            if index:
                divider = QFrame()
                divider.setObjectName("brandRule")
                divider.setFixedWidth(1)
                row.addSpacing(22)
                row.addWidget(divider)
                row.addSpacing(22)

            cell = QVBoxLayout()
            cell.setContentsMargins(0, 0, 0, 0)
            cell.setSpacing(1)
            value_label = QLabel(value)
            value_label.setObjectName("brandFactValue")
            caption_label = QLabel(caption)
            caption_label.setObjectName("brandFactCaption")
            cell.addWidget(value_label)
            cell.addWidget(caption_label)
            row.addLayout(cell, 1)
        return row

    # ------------------------------------------------------------------ paint
    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        set_prop(self, "scale", "lg" if width >= _LARGE_FROM else "sm" if width < _SMALL_BELOW else "md")

    def paintEvent(self, event):
        painter = QPainter(self)
        glow = QRadialGradient(QPointF(self.width() * 0.45, self.height() * 0.42), self.width() * 0.6)
        glow.setColorAt(0.0, with_alpha(Colors.PRIMARY, 22))
        glow.setColorAt(1.0, with_alpha(Colors.PRIMARY, 0))
        painter.fillRect(self.rect(), QBrush(glow))
        painter.fillRect(self.rect(), QBrush(self._dot_tile()))
        painter.end()

    def _dot_tile(self) -> QPixmap:
        """One cell of the dot grid, rendered once per device pixel ratio."""
        dpr = self.devicePixelRatioF()
        if self._dots is not None and self._dots_dpr == dpr:
            return self._dots

        side = int(_DOT_PITCH * dpr)
        tile = QPixmap(side, side)
        tile.setDevicePixelRatio(dpr)
        tile.fill(Qt.GlobalColor.transparent)
        painter = QPainter(tile)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(with_alpha(Colors.BORDER_STRONG, 130))
        painter.drawEllipse(QPointF(_DOT_PITCH / 2.0, _DOT_PITCH / 2.0), 0.9, 0.9)
        painter.end()

        self._dots, self._dots_dpr = tile, dpr
        return tile
