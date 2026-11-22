"""Health questionnaire fields, generated from `QUESTIONS`. Nothing is preselected."""

from __future__ import annotations

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from src.dtos.questionnaire import CHECK, CHOICE, NUMBER, QUESTIONS, Question
from src.views.components.common.form_field import FieldMessage, FormField
from src.views.components.common.inputs import CheckBox, RadioButton, make_line_edit
from src.views.components.common.painting import Divider
from src.views.components.common.segmented_control import SegmentedControl
from src.views.strings import Register
from src.views.theme import Colors, Space, make_label, set_props

COLUMN = 600
HALF = (COLUMN - Space.S4) // 2        # 292


class RadioGroup(QWidget):
    """Radio buttons in two columns (used when the options do not fit a segmented control)."""

    selection_changed = Signal(int)

    def __init__(self, labels: tuple[str, ...], accessible_name: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
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
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self._group.idClicked.connect(self.selection_changed)
        if accessible_name:
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
        """Marks the options as invalid (red) or valid.

        Args:
            invalid: True to show the error state.
        """
        for button in self.buttons:
            set_props(button, invalid=invalid)

    def focus_target(self) -> QWidget:
        """Returns the widget to focus: the checked option, or the first one."""
        return self._group.checkedButton() or self.buttons[0]


class QuestionField(QWidget):
    """One question: CHOICE (segmented control or radios), NUMBER (text field) or CHECK (check box)."""

    changed = Signal()

    def __init__(self, question: Question, parent: QWidget | None = None):
        super().__init__(parent)
        self.question = question
        self._error = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Exactly one input is created, depending on the question's kind.
        self.options: SegmentedControl | RadioGroup | None = None     # CHOICE
        self.edit: QLineEdit | None = None                            # NUMBER
        self.check: CheckBox | None = None                            # CHECK
        self.field: FormField | None = None
        self._message: FieldMessage | None = None

        if question.kind == CHOICE:
            labels = tuple(label for label, _ in question.options)
            title = make_label(question.text, "body-strong", "body", wrap=True)
            layout.addWidget(title)
            layout.addSpacing(Space.S2)
            if SegmentedControl.fits(labels, COLUMN):
                self.options = SegmentedControl(labels, accessible_name=question.text)
            else:
                self.options = RadioGroup(labels, question.text)
            self.options.selection_changed.connect(self._on_changed)
            layout.addWidget(self.options)
            self._message = FieldMessage()
            layout.addWidget(self._message)
        elif question.kind == NUMBER:
            placeholder = Register.NUMBER_PLACEHOLDER.format(minimum=question.minimum, maximum=question.maximum)
            self.edit = make_line_edit(placeholder, clearable=False)
            self.edit.setValidator(QIntValidator(question.minimum, question.maximum, self.edit))
            self.edit.textChanged.connect(self._on_changed)
            self.field = FormField(question.text, self.edit)
            self.field.setFixedWidth(HALF)
            layout.addWidget(self.field)
        elif question.kind == CHECK:
            self.check = CheckBox(question.text)
            self.check.toggled.connect(self._on_changed)
            layout.addWidget(self.check)
        else:
            raise ValueError(f"Unknown question kind: {question.kind!r}")

    # ------------------------------------------------------------------ API
    def value(self) -> float | None:
        """Exactly one input exists, chosen by the question's kind in the constructor."""
        q = self.question
        if self.options is not None:          # CHOICE
            index = self.options.selected()
            return float(q.options[index][1]) if index >= 0 else None
        if self.edit is not None:             # NUMBER
            text = self.edit.text().strip()
            if not text.lstrip("-").isdigit():
                return None
            number = int(text)
            return float(number) if q.minimum <= number <= q.maximum else None
        return 1.0 if self.check is not None and self.check.isChecked() else 0.0   # CHECK

    def validate(self) -> bool:
        """Shows the inline error when the question is unanswered; True when it is valid."""
        if self.value() is not None:
            self.set_error(None)
            return True
        if self.question.kind == NUMBER:
            self.set_error(Register.NUMBER_RANGE.format(minimum=self.question.minimum, maximum=self.question.maximum))
        else:
            self.set_error(Register.CHOICE_REQUIRED)
        return False

    def set_error(self, message: str | None) -> None:
        """Shows an inline error under the question, or clears it.

        Args:
            message: The error, or None to clear it.
        """
        self._error = message is not None
        if self.field is not None:
            self.field.set_error(message)
        elif self.options is not None and self._message is not None:
            self.options.set_invalid(self._error)
            self._message.set_error(message)
            self.options.setAccessibleDescription(message or "")

    def reset(self) -> None:
        """Clears the answer and the error."""
        if self.options is not None:
            self.options.clear()
        if self.edit is not None:
            self.edit.clear()
        if self.check is not None:
            self.check.setChecked(False)
        self.set_error(None)

    def focus_target(self) -> QWidget:
        """Returns the widget to focus to answer this question."""
        if self.options is not None:
            return self.options.focus_target()
        if self.edit is not None:
            return self.edit
        return self.check if self.check is not None else self

    @Slot()
    def _on_changed(self, *_args) -> None:
        if self._error and self.value() is not None:
            self.set_error(None)
        self.changed.emit()


class QuestionStep(QWidget):
    """All the questions of one step of the sign-up form, grouped by section.

    Consecutive NUMBER questions share a row; consecutive CHECK questions form a two-column grid.

    Args:
        step: The step (PROFILE, DAILY_LIFE or HEALTH).
        parent: Parent widget.
    """

    def __init__(self, step: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.fields: list[QuestionField] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        questions = [q for q in QUESTIONS if q.step == step]
        groups: list[tuple[str, list[Question]]] = []
        for question in questions:
            kind = question.kind
            same_group = (groups and not question.section and groups[-1][0] == kind and kind in (CHECK, NUMBER)
                          and not (kind == NUMBER and len(groups[-1][1]) == 2))
            if same_group:
                groups[-1][1].append(question)
            else:
                groups.append((kind, [question]))

        for index, (kind, members) in enumerate(groups):
            section = members[0].section
            if section:
                if index:
                    layout.addSpacing(Space.S6)
                layout.addWidget(make_label(section.upper(), "overline", "secondary"))
                layout.addSpacing(Space.S1)
                layout.addWidget(Divider(Colors.N150))
                layout.addSpacing(Space.S3)
            elif index:
                layout.addSpacing(Space.S5)

            fields = [QuestionField(q) for q in members]
            self.fields.extend(fields)
            if kind == CHECK:
                grid = QGridLayout()
                grid.setContentsMargins(0, 0, 0, 0)
                grid.setHorizontalSpacing(Space.S4)
                grid.setVerticalSpacing(10)
                for position, field in enumerate(fields):
                    grid.addWidget(field, position // 2, position % 2)
                grid.setColumnStretch(0, 1)
                grid.setColumnStretch(1, 1)
                layout.addLayout(grid)
            elif kind == NUMBER:
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(Space.S4)
                for field in fields:
                    row.addWidget(field)
                row.addStretch(1)
                layout.addLayout(row)
            else:
                layout.addWidget(fields[0])

    def answers(self) -> dict[str, float]:
        """Returns the answers of this step.

        Returns:
            Model feature -> value; None for questions not answered yet.
        """
        return {field.question.key: field.value() for field in self.fields}

    def validate(self) -> list[tuple[QWidget, QWidget]]:
        """Validates every question; returns (widget to scroll to, widget to focus) for the invalid ones."""
        return [(field, field.focus_target()) for field in self.fields if not field.validate()]

    def reset(self) -> None:
        """Clears every answer and error of this step."""
        for field in self.fields:
            field.reset()
