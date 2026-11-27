"""Inputs of the health questionnaire, built from `domain.questionnaire`. Nothing is preselected.

Every input answers one question and offers the same small interface (`Answer`): its value, whether
it is answered, validation with an inline error, reset and the widget to focus. `build_section`
lays out the questions of one section:

* consecutive choices that share one scale (the everyday activities) form a `ScaleMatrix`: one row
  per question and one column per answer, so the scale is read once instead of once per question;
* a number followed by a short choice (age and sex) share a row;
* consecutive check boxes form a grid of two or three columns;
* any other choice is a full-width segmented control (two columns of radio buttons if it does not
  fit); a number is a half-width field.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, QSize, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFontMetrics, QIntValidator, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.domain.questionnaire import CHECK, CHOICE, NUMBER, Question
from src.strings import Form
from src.views.components.common.form_field import FieldMessage, FormField
from src.views.components.common.inputs import CheckBox, RadioButton, make_line_edit
from src.views.components.common.segmented_control import SegmentedControl
from src.views.theme import Colors, Size, Space, Type, make_label, set_props

SCALE_ROW = 44           # height of a row of the scale matrix
_SCALE_COLUMN = 112      # width of each answer column of the matrix
_INDICATOR = 16          # the matrix's radio circles


# ---------------------------------------------------------------------- one question
class Answer(QWidget):
    """Base of the questionnaire's inputs: one question and its answer.

    Signals:
        changed: The answer changed.
    """

    changed = Signal()

    def __init__(self, question: Question | None, parent: QWidget | None = None):
        super().__init__(parent)
        self.question = question       # None for a field that is not an input of the model
        self._error = False

    def value(self) -> float | None:
        """The answer, as the number the model expects, or None while unanswered."""
        raise NotImplementedError

    def is_answered(self) -> bool:
        """True when the question has a valid answer."""
        return self.value() is not None

    def validate(self) -> bool:
        """Shows the inline error when the question is unanswered; True when it is valid."""
        if self.is_answered():
            self.set_error(None)
            return True
        if self.question.kind == NUMBER:
            self.set_error(Form.NUMBER_RANGE.format(minimum=self.question.minimum, maximum=self.question.maximum))
        else:
            self.set_error(Form.CHOICE_REQUIRED)
        return False

    def set_error(self, message: str | None) -> None:
        """Shows an inline error under the question, or clears it (None)."""
        self._error = message is not None

    def has_error(self) -> bool:
        """True while the question is marked as missing its answer."""
        return self._error

    def reset(self) -> None:
        """Clears the answer and the error."""
        raise NotImplementedError

    def focus_target(self) -> QWidget:
        """Returns the widget to focus to answer this question."""
        return self

    @Slot()
    def _on_changed(self, *_args) -> None:
        if self._error and self.is_answered():
            self.set_error(None)
        self.changed.emit()


class RadioGroup(QWidget):
    """Radio buttons in two columns, for a choice whose options do not fit a segmented control."""

    selection_changed = Signal(int)

    def __init__(self, labels: tuple[str, ...], accessible_name: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self._group = QButtonGroup(self)
        self.buttons: list[RadioButton] = []
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(Space.S4)
        grid.setVerticalSpacing(Space.S2)
        for index, label in enumerate(labels):
            button = RadioButton(label)
            self._group.addButton(button, index)
            grid.addWidget(button, index // 2, index % 2)
            self.buttons.append(button)
        self._group.idClicked.connect(self.selection_changed)
        self.setAccessibleName(accessible_name)

    def selected(self) -> int:
        """Returns the index of the checked option, or -1."""
        return self._group.checkedId()

    def clear(self) -> None:
        """Unchecks every option."""
        self._group.setExclusive(False)
        for button in self.buttons:
            button.setChecked(False)
        self._group.setExclusive(True)

    def set_invalid(self, invalid: bool) -> None:
        """Marks the options as invalid (red) or valid."""
        for button in self.buttons:
            set_props(button, invalid=invalid)

    def focus_target(self) -> QWidget:
        """Returns the checked option, or the first one."""
        return self._group.checkedButton() or self.buttons[0]


class ChoiceAnswer(Answer):
    """A choice: its text, then a segmented control as wide as the card (radios if it does not fit)."""

    def __init__(self, question: Question, width: int, parent: QWidget | None = None):
        super().__init__(question, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        title = make_label(question.text, "body-strong", "body", wrap=True)
        title.setMinimumHeight(Type.line_height("body-strong"))     # as tall as a FormField label
        layout.addWidget(title)
        layout.addSpacing(6)            # as in FormField, so labels line up across a row
        labels = tuple(label for label, _ in question.options)
        if SegmentedControl.fits(labels, width):
            self.options: SegmentedControl | RadioGroup = SegmentedControl(
                labels, height=Size.H_LG, accessible_name=question.text)
        else:
            self.options = RadioGroup(labels, question.text)
        self.options.selection_changed.connect(self._on_changed)
        layout.addWidget(self.options)
        self._message = FieldMessage()
        layout.addWidget(self._message)

    def value(self) -> float | None:
        """The chosen option's value, or None."""
        index = self.options.selected()
        return float(self.question.options[index][1]) if index >= 0 else None

    def set_error(self, message: str | None) -> None:
        """Red border and the message under the options, or no error."""
        super().set_error(message)
        self.options.set_invalid(self._error)
        self._message.set_error(message)
        self.options.setAccessibleDescription(message or "")

    def reset(self) -> None:
        """Clears the choice and the error."""
        self.options.clear()
        self.set_error(None)

    def focus_target(self) -> QWidget:
        """The checked option, or the first one."""
        return self.options.focus_target()


class NumberAnswer(Answer):
    """A whole number in a range, in a text field with the range as its placeholder."""

    def __init__(self, question: Question, parent: QWidget | None = None):
        super().__init__(question, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        placeholder = Form.NUMBER_PLACEHOLDER.format(minimum=question.minimum, maximum=question.maximum)
        self.edit: QLineEdit = make_line_edit(placeholder, clearable=False)
        self.edit.setValidator(QIntValidator(question.minimum, question.maximum, self.edit))
        self.edit.textChanged.connect(self._on_changed)
        self.field = FormField(question.text, self.edit)
        layout.addWidget(self.field)

    def value(self) -> float | None:
        """The number, or None when it is empty or out of range."""
        text = self.edit.text().strip()
        if not text.isdigit():
            return None
        number = int(text)
        return float(number) if self.question.minimum <= number <= self.question.maximum else None

    def set_error(self, message: str | None) -> None:
        """Red border and the message under the field, or no error."""
        super().set_error(message)
        self.field.set_error(message)

    def reset(self) -> None:
        """Empties the field and clears the error."""
        self.edit.clear()
        self.set_error(None)

    def focus_target(self) -> QWidget:
        """The text field."""
        return self.edit


class CheckAnswer(Answer):
    """A yes / no question as a check box; left empty it means "no", so it is always answered."""

    def __init__(self, question: Question, parent: QWidget | None = None):
        super().__init__(question, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.check = CheckBox(question.text)
        self.check.toggled.connect(self._on_changed)
        layout.addWidget(self.check)

    def value(self) -> float:
        """1 when ticked, 0 otherwise."""
        return 1.0 if self.check.isChecked() else 0.0

    def reset(self) -> None:
        """Unticks the box."""
        self.check.setChecked(False)

    def focus_target(self) -> QWidget:
        """The check box."""
        return self.check


# ---------------------------------------------------------------------- the scale matrix
class ScaleOption(QAbstractButton):
    """One cell of the scale matrix: a radio circle centred in the cell; the whole cell is clickable."""

    def __init__(self, accessible_name: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(_SCALE_COLUMN, SCALE_ROW)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setAccessibleName(accessible_name)
        self.invalid = False

    def sizeHint(self) -> QSize:
        """The cell's fixed size."""
        return QSize(_SCALE_COLUMN, SCALE_ROW)

    def paintEvent(self, event) -> None:
        """Paints the circle: empty, hovered, checked (P600 with a white dot), invalid or focused."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        circle = QRectF((self.width() - _INDICATOR) / 2, (self.height() - _INDICATOR) / 2, _INDICATOR, _INDICATOR)
        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(Colors.P600))
            painter.drawEllipse(circle)
            painter.setBrush(QColor(Colors.N0))
            painter.drawEllipse(circle.center(), 3, 3)
        else:
            border = Colors.R600 if self.invalid else Colors.N600 if self.underMouse() else Colors.N400
            painter.setPen(QPen(QColor(border), 1))
            painter.setBrush(QColor(Colors.N0))
            painter.drawEllipse(circle.adjusted(0.5, 0.5, -0.5, -0.5))
        if self.hasFocus():
            painter.setPen(QPen(QColor(Colors.P600), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(circle.adjusted(-3, -3, 3, 3))


class ScaleRow(Answer):
    """One question of the scale matrix: its text, then one `ScaleOption` per answer of the scale."""

    def __init__(self, question: Question, label_width: int, parent: QWidget | None = None):
        super().__init__(question, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.ruled = True
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        text = QVBoxLayout()
        text.setContentsMargins(Space.S3, Space.S2, Space.S3, Space.S2)
        text.setSpacing(0)
        text.addStretch(1)
        self.label = make_label(question.text, "body", wrap=True)
        text.addWidget(self.label)
        self._message = make_label("", "caption", "danger")
        self._message.hide()
        text.addWidget(self._message)
        text.addStretch(1)
        holder = QWidget()
        holder.setFixedWidth(label_width)
        holder.setLayout(text)
        layout.addWidget(holder)

        self._group = QButtonGroup(self)
        self.buttons: list[ScaleOption] = []
        for index, (option, _value) in enumerate(question.options):
            button = ScaleOption(f"{question.text}: {option}")
            self._group.addButton(button, index)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
            self.buttons.append(button)
        self._group.idClicked.connect(self._on_changed)
        self.setMinimumHeight(SCALE_ROW)
        self.setAccessibleName(question.text)

    def value(self) -> float | None:
        """The chosen answer's value, or None."""
        index = self._group.checkedId()
        return float(self.question.options[index][1]) if index >= 0 else None

    def set_error(self, message: str | None) -> None:
        """Red circles and the message under the question's text, or no error."""
        super().set_error(message)
        for button in self.buttons:
            button.invalid = self._error
            button.update()
        self._message.setText(message or "")
        self._message.setVisible(self._error)
        self.setAccessibleDescription(message or "")
        self.update()

    def reset(self) -> None:
        """Clears the answer and the error."""
        self._group.setExclusive(False)
        for button in self.buttons:
            button.setChecked(False)
        self._group.setExclusive(True)
        self.set_error(None)

    def focus_target(self) -> QWidget:
        """The chosen answer, or the first one."""
        return self._group.checkedButton() or self.buttons[0]

    def enterEvent(self, event) -> None:
        """Highlights the row under the pointer."""
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event) -> None:
        """Removes the highlight."""
        super().leaveEvent(event)
        self.update()

    def paintEvent(self, event) -> None:
        """Paints the hover band (R50 while invalid) and the rule under the row."""
        painter = QPainter(self)
        if self._error:
            painter.fillRect(self.rect(), QColor(Colors.R50))
        elif self.underMouse():
            painter.fillRect(self.rect(), QColor(Colors.N50))
        if self.ruled:
            painter.fillRect(QRect(0, self.height() - 1, self.width(), 1), QColor(Colors.N150))


class ScaleMatrix(QWidget):
    """Several questions answered on the same scale: a header with the answers, then one row each.

    Args:
        questions: The questions; they all have the same options (the first one's labels head the columns).
        width: Width of the matrix.
        parent: Parent widget.
    """

    def __init__(self, questions: list[Question], width: int, parent: QWidget | None = None):
        super().__init__(parent)
        columns = len(questions[0].options)
        label_width = width - columns * _SCALE_COLUMN
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(_ScaleHeader([label for label, _ in questions[0].options], label_width))
        self.rows = [ScaleRow(question, label_width) for question in questions]
        for row in self.rows:
            layout.addWidget(row)
        self.rows[-1].ruled = False
        self.setFixedWidth(width)


class _ScaleHeader(QWidget):
    """The matrix's column captions, on an N50 band with a rule under it."""

    def __init__(self, labels: list[str], label_width: int, parent: QWidget | None = None):
        super().__init__(parent)
        self._labels = labels
        self._label_width = label_width
        metrics = QFontMetrics(Type.font("caption-strong"))
        text = max(metrics.boundingRect(QRect(0, 0, _SCALE_COLUMN - Space.S2, 200), int(Qt.TextFlag.TextWordWrap),
                                        label).height() for label in labels)
        self.setFixedHeight(text + 2 * Space.S2 + 1)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event) -> None:
        """Paints the band, the captions centred over their columns and the rule."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.N50))
        painter.fillRect(QRect(0, self.height() - 1, self.width(), 1), QColor(Colors.N200))
        painter.setFont(Type.font("caption-strong"))
        painter.setPen(QColor(Colors.N600))
        for index, label in enumerate(self._labels):
            cell = QRect(self._label_width + index * _SCALE_COLUMN + Space.S1, 0, _SCALE_COLUMN - Space.S2,
                         self.height() - 1)
            painter.drawText(cell, int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), label)


# ---------------------------------------------------------------------- a section's layout
def _same_scale(first: Question, second: Question) -> bool:
    return first.kind == second.kind == CHOICE and first.options == second.options


def _joins(group: list[Question], question: Question, width: int) -> bool:
    """True when `question` joins the group before it.

    It does when it has the same scale, when both are check boxes, or when it is a short choice
    after a lone number (the two share a row).
    """
    last = group[-1]
    if _same_scale(last, question) or last.kind == question.kind == CHECK:
        return True
    labels = tuple(label for label, _ in question.options)
    return (len(group) == 1 and last.kind == NUMBER and question.kind == CHOICE
            and SegmentedControl.fits(labels, (width - Space.S4) // 2))


def _check_columns(questions: list[Question], width: int) -> int:
    """Three columns when every label fits a third of the width, otherwise two."""
    metrics = QFontMetrics(Type.font("body"))
    third = (width - 2 * Space.S4) // 3
    widest = max(metrics.horizontalAdvance(question.text) for question in questions)
    return 3 if widest + 24 <= third else 2


def build_section(questions: tuple[Question, ...], width: int) -> tuple[QVBoxLayout, list[Answer]]:
    """Lays out the questions of one section (see the module docstring).

    Args:
        questions: The section's questions, in order.
        width: Width the inputs get (the card's content).

    Returns:
        The layout and every answer input, in order.
    """
    groups: list[list[Question]] = []
    for question in questions:
        if groups and _joins(groups[-1], question, width):
            groups[-1].append(question)
        else:
            groups.append([question])

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(Space.S5)
    answers: list[Answer] = []
    half = (width - Space.S4) // 2
    for group in groups:
        first = group[0]
        if first.kind == CHOICE and len(group) > 1:
            matrix = ScaleMatrix(group, width)
            answers.extend(matrix.rows)
            layout.addWidget(matrix)
        elif first.kind == CHECK:
            columns = _check_columns(group, width) if len(group) > 1 else 1
            grid = QGridLayout()
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(Space.S4)
            grid.setVerticalSpacing(Space.S3)
            for position, question in enumerate(group):
                answer = CheckAnswer(question)
                answers.append(answer)
                grid.addWidget(answer, position // columns, position % columns)
            for column in range(columns):
                grid.setColumnStretch(column, 1)
            layout.addLayout(grid)
        elif first.kind == NUMBER:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(Space.S4)
            for question in group:
                answer = NumberAnswer(question) if question.kind == NUMBER else ChoiceAnswer(question, half)
                answer.setFixedWidth(half)
                answers.append(answer)
                row.addWidget(answer, 0, Qt.AlignmentFlag.AlignTop)
            row.addStretch(1)
            layout.addLayout(row)
        else:
            answer = ChoiceAnswer(first, width)
            answers.append(answer)
            layout.addWidget(answer)
    return layout, answers
