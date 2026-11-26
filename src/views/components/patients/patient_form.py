"""New patient form: one page of section cards on the dashboard's canvas, and a fixed action bar.

The health questionnaire (`domain.questionnaire`) is answered here, once per patient; the controller
turns the answers into the patient's risk level, which sets how the camera monitors them.

Layout: a link back to the patients, the title and one line on what the answers are for; then one
card per section (`SectionCard`): the patient (name, the profile questions and optional medical
notes), general condition, everyday activities (one matrix on a shared difficulty scale), health
conditions and medication. Each card's header numbers it and says how much of it is answered, so the
caregiver always sees what is left. The action bar under the page stays in view: the overall
progress, Cancel and Add patient.

Adding checks every question at once: the unanswered ones are marked inline, their cards turn red,
the bar says how many answers are missing and the page scrolls to the first one.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSize,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.domain.questionnaire import PATIENT, SECTIONS, questions_in
from src.dtos.patient_form_data import PatientFormData
from src.views import icons
from src.views.components.common.button import make_button
from src.views.components.common.callout import Callout
from src.views.components.common.confirm_dialog import ConfirmDialog
from src.views.components.common.form_field import FormField
from src.views.components.common.inputs import make_line_edit
from src.views.components.common.painting import transparent_scroll_area
from src.views.components.common.shortcuts import add_shortcut
from src.views.components.patients.questionnaire import (
    Answer,
    CheckAnswer,
    build_section,
)
from src.views.strings import PatientForm as Text
from src.views.theme import Colors, Motion, Space, Type, make_label, set_props

CONTENT = 820                                  # width of the form's column
CARD_PADDING = Space.S6
FIELDS_WIDTH = CONTENT - 2 - 2 * CARD_PADDING  # what the inputs of a card get
ACTION_BAR = 64
_MARKER = 24
_PROGRESS_WIDTH = 160


class NameAnswer(Answer):
    """The patient's full name: a required text field (it is not an input of the risk model)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(None, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit: QLineEdit = make_line_edit("", "user")
        self.edit.setMaxLength(120)
        self.edit.textChanged.connect(self._on_changed)
        self.field = FormField(Text.PATIENT_NAME, self.edit)
        layout.addWidget(self.field)

    def text(self) -> str:
        """The name, without surrounding spaces."""
        return self.edit.text().strip()

    def value(self) -> float | None:
        """Not a model input: 1 once a name is written, None before."""
        return 1.0 if self.text() else None

    def validate(self) -> bool:
        """Marks the field when it is empty; True when a name is written."""
        valid = self.is_answered()
        self.set_error(None if valid else Text.PATIENT_REQUIRED)
        return valid

    def set_error(self, message: str | None) -> None:
        """Red border and the message under the field, or no error."""
        super().set_error(message)
        self.field.set_error(message)

    def reset(self) -> None:
        """Empties the field."""
        self.edit.clear()
        self.set_error(None)

    def focus_target(self) -> QWidget:
        """The text field."""
        return self.edit


# ---------------------------------------------------------------------- section cards
class _SectionMarker(QWidget):
    """The card's number in a 24 px circle; a tick once complete, red while answers are missing."""

    def __init__(self, number: int, parent: QWidget | None = None):
        super().__init__(parent)
        self._number = number
        self._state = "todo"
        self.setFixedSize(_MARKER, _MARKER)

    def set_state(self, state: str) -> None:
        """Changes the state: "todo", "done" or "error"."""
        if state != self._state:
            self._state = state
            self.update()

    def paintEvent(self, event) -> None:
        """Paints the circle and the number (or the tick)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        circle = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self._state == "done":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(Colors.P600))
            painter.drawEllipse(circle)
            painter.drawPixmap(4, 4, icons.icon_pixmap("check", Colors.N0, 16, self.devicePixelRatioF()))
            return
        error = self._state == "error"
        painter.setPen(QPen(QColor(Colors.R600 if error else Colors.N300), 1))
        painter.setBrush(QColor(Colors.R50 if error else Colors.N0))
        painter.drawEllipse(circle)
        painter.setFont(Type.font("caption-strong"))
        painter.setPen(QColor(Colors.R700 if error else Colors.N600))
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), str(self._number))


class SectionCard(QWidget):
    """One section of the form: a header (number, title, description and progress) over its fields.

    Args:
        number: Position of the section in the form.
        title: Its heading.
        description: One line under the heading.
        parent: Parent widget.
    """

    def __init__(self, number: int, title: str, description: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(CONTENT)
        self.answers: list[Answer] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        self.header = QWidget()
        header = QHBoxLayout(self.header)
        header.setContentsMargins(CARD_PADDING - 1, Space.S4, CARD_PADDING - 1, Space.S4)
        header.setSpacing(Space.S3)
        self.marker = _SectionMarker(number)
        header.addWidget(self.marker, 0, Qt.AlignmentFlag.AlignTop)
        text = QVBoxLayout()
        text.setContentsMargins(0, 2, 0, 0)
        text.setSpacing(2)
        text.addWidget(make_label(title, "title-sm"))
        text.addWidget(make_label(description, "caption", "secondary", wrap=True))
        header.addLayout(text, 1)
        self.progress = make_label("", "caption", "tertiary")
        self.progress.setContentsMargins(0, 4, 0, 0)       # centred on the title's line
        header.addWidget(self.progress, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.header)
        layout.addSpacing(1)          # the rule under the header

        self.body = QVBoxLayout()
        self.body.setContentsMargins(CARD_PADDING - 1, Space.S5, CARD_PADDING - 1, CARD_PADDING - 1)
        self.body.setSpacing(Space.S5)
        layout.addLayout(self.body)

    def required(self) -> list[Answer]:
        """The answers of this card that must be given (check boxes never need one)."""
        return [answer for answer in self.answers if answer.question is None or answer.question.required]

    def refresh(self) -> None:
        """Updates the header: how much is answered, and whether answers are missing."""
        required = self.required()
        answered = sum(answer.is_answered() for answer in required)
        missing = sum(answer.has_error() for answer in required)
        if missing:
            self.marker.set_state("error")
            text, tone = Text.SECTION_MISSING.format(n=missing), "danger"
        elif not required:                # only check boxes: nothing to complete
            self.marker.set_state("todo")
            text, tone = Text.SECTION_OPTIONAL, "tertiary"
        elif answered == len(required):
            self.marker.set_state("done")
            text, tone = Text.SECTION_DONE, "success"
        else:
            self.marker.set_state("todo")
            text, tone = Text.SECTION_PROGRESS.format(answered=answered, total=len(required)), "tertiary"
        self.progress.setText(text)
        set_props(self.progress, tone=tone)

    def paintEvent(self, event) -> None:
        """Paints the card (N0, N200 border) and the rule under its header."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.N200))
        painter.fillRect(self.rect().adjusted(1, 1, -1, -1), QColor(Colors.N0))
        rule = self.header.geometry().bottom() + 1
        painter.fillRect(QRect(1, rule, self.width() - 2, 1), QColor(Colors.N150))


# ---------------------------------------------------------------------- action bar
class _ProgressBar(QWidget):
    """A 4 px track whose fill glides to the share of answers given (G600 once complete)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._value = 0.0
        self.setFixedSize(_PROGRESS_WIDTH, 4)
        self._animation = QPropertyAnimation(self, b"value", self)
        self._animation.setDuration(Motion.BASE)
        self._animation.setEasingCurve(QEasingCurve(Motion.OUT))

    def _get_value(self) -> float:
        return self._value

    def _set_value(self, value: float) -> None:
        self._value = value
        self.update()

    value = Property(float, _get_value, _set_value)

    def set_share(self, share: float, animate: bool = True) -> None:
        """Moves the fill to `share` (0 to 1)."""
        self._animation.stop()
        if animate and self.isVisible():
            self._animation.setStartValue(self._value)
            self._animation.setEndValue(share)
            self._animation.start()
        else:
            self._set_value(share)

    def paintEvent(self, event) -> None:
        """Paints the track and the fill."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.N150))
        color = Colors.G600 if self._value >= 0.999 else Colors.P600
        painter.fillRect(QRectF(0, 0, self.width() * self._value, self.height()), QColor(color))


class _ActionBar(QWidget):
    """White bar fixed under the form: progress on the left, Cancel and Add patient on the right."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(ACTION_BAR)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 1, 0, 0)
        outer.addStretch(1)
        column = QWidget()
        column.setFixedWidth(CONTENT)
        outer.addWidget(column)
        outer.addStretch(1)
        self._outer = outer

        layout = QHBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.S3)
        progress = QVBoxLayout()
        progress.setContentsMargins(0, 0, 0, 0)
        progress.setSpacing(Space.S1)
        progress.addStretch(1)
        self.status = make_label("", "caption-strong", "secondary")
        progress.addWidget(self.status)
        self.bar = _ProgressBar()
        progress.addWidget(self.bar)
        progress.addStretch(1)
        layout.addLayout(progress)
        layout.addStretch(1)
        self.cancel = make_button(Text.CANCEL, "secondary", "md")
        layout.addWidget(self.cancel, 0, Qt.AlignmentFlag.AlignVCenter)
        self.submit = make_button(Text.ADD, "primary", "md", "user-plus")
        self.submit.reserve_width(Text.ADD, Text.ADDING)
        layout.addWidget(self.submit, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_scrollbar_inset(self, width: int) -> None:
        """Keeps the bar's column over the page's, which loses `width` px to the scroll bar."""
        self._outer.setContentsMargins(0, 1, width, 0)

    def paintEvent(self, event) -> None:
        """Paints the white bar and its top border."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.N0))
        painter.fillRect(QRect(0, 0, self.width(), 1), QColor(Colors.N200))


# ---------------------------------------------------------------------- the form
class PatientForm(QWidget):
    """The new patient form (see the module docstring).

    Signals:
        submitted(PatientFormData): The validated form.
        cancelled: The user went back to the list without adding the patient.
    """
    submitted = Signal(PatientFormData)
    cancelled = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._busy = False
        self._attempted = False          # Add was pressed: from then on, missing answers are counted
        self._scroll_animation: QPropertyAnimation | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(Space.S6, 0, Space.S6, 0)
        row.addStretch(1)
        self._column = QWidget()
        self._column.setFixedWidth(CONTENT)
        row.addWidget(self._column)
        row.addStretch(1)
        self.scroll: QScrollArea = transparent_scroll_area(page)
        outer.addWidget(self.scroll, 1)
        self.actions = _ActionBar()
        outer.addWidget(self.actions)
        bar = self.scroll.verticalScrollBar()
        bar.rangeChanged.connect(lambda _low, high: self.actions.set_scrollbar_inset(bar.sizeHint().width() if high else 0))

        column = QVBoxLayout(self._column)
        column.setContentsMargins(0, Space.S6, 0, Space.S8)
        column.setSpacing(0)
        self.back_link = make_button(Text.BACK_TO_PATIENTS, "link", "sm", "chevron-left")
        column.addWidget(self.back_link, 0, Qt.AlignmentFlag.AlignLeft)
        column.addSpacing(Space.S3)
        column.addWidget(make_label(Text.TITLE, "title-lg"))
        column.addSpacing(Space.S1)
        column.addWidget(make_label(Text.SUBTITLE, "body", "secondary", wrap=True))
        column.addSpacing(Space.S6)

        self.error = Callout("", "danger")       # errors from the controller that belong to no field
        self._error_box = QWidget()
        error_layout = QVBoxLayout(self._error_box)
        error_layout.setContentsMargins(0, 0, 0, Space.S4)
        error_layout.addWidget(self.error)
        self._error_box.hide()
        column.addWidget(self._error_box)

        self.cards: list[SectionCard] = []
        for number, section in enumerate(SECTIONS, start=1):
            card = SectionCard(number, section.title, section.description)
            self._fill(card, section)
            for answer in card.answers:
                answer.changed.connect(self._refresh)
            column.addWidget(card)
            column.addSpacing(Space.S4)
            self.cards.append(card)
        column.addStretch(1)

        self.back_link.clicked.connect(self._cancel)
        self.actions.cancel.clicked.connect(self._cancel)
        self.actions.submit.clicked.connect(self._submit)
        add_shortcut(self, ("Ctrl+Return", "Ctrl+Enter"), self._submit)
        self._refresh(animate=False)

    def _fill(self, card: SectionCard, section) -> None:
        """Adds a section's inputs to its card; the patient's card also has the name and the notes."""
        if section is PATIENT:
            self.name = NameAnswer()
            card.answers.append(self.name)
            card.body.addWidget(self.name)
        layout, answers = build_section(questions_in(section), FIELDS_WIDTH)
        card.body.addLayout(layout)
        card.answers.extend(answers)
        if section is PATIENT:
            self.notes = QPlainTextEdit()
            self.notes.setPlaceholderText(Text.MEDICAL_NOTES_PLACEHOLDER)
            self.notes.setFixedHeight(76)
            self.notes.setTabChangesFocus(True)
            card.body.addWidget(FormField(Text.MEDICAL_NOTES, self.notes, optional=True))

    # ------------------------------------------------------------------ state
    def _answers(self) -> list[Answer]:
        return [answer for card in self.cards for answer in card.answers]

    def _required(self) -> list[Answer]:
        return [answer for card in self.cards for answer in card.required()]

    @Slot()
    def _refresh(self, animate: bool = True) -> None:
        """Updates every card's header and the action bar after an answer changed."""
        for card in self.cards:
            card.refresh()
        required = self._required()
        answered = sum(answer.is_answered() for answer in required)
        missing = sum(answer.has_error() for answer in required)
        if self._attempted and missing:
            text, tone = (Text.MISSING_ONE if missing == 1 else Text.MISSING_MANY.format(n=missing)), "danger"
        else:
            text, tone = Text.PROGRESS.format(answered=answered, total=len(required)), "secondary"
        self.actions.status.setText(text)
        set_props(self.actions.status, tone=tone)
        self.actions.bar.set_share(answered / len(required) if required else 1.0, animate=animate)

    def is_dirty(self) -> bool:
        """True once anything has been written, chosen or ticked."""
        if self.notes.toPlainText().strip():
            return True
        return any(answer.value() if isinstance(answer, CheckAnswer) else answer.is_answered()
                   for answer in self._answers())

    # ------------------------------------------------------------------ actions
    @Slot()
    def _cancel(self) -> None:
        """Back to the list, asking first when something would be lost."""
        if self._busy:
            return
        if self.is_dirty() and not ConfirmDialog.ask(self, Text.DISCARD_TITLE, Text.DISCARD_BODY,
                                                     Text.DISCARD_ACTION, destructive=True):
            return
        self.cancelled.emit()

    @Slot()
    def _submit(self) -> None:
        """Validates every question; marks and shows what is missing, or sends the form."""
        if self._busy or not self.isVisible():
            return
        self._error_box.hide()
        self._attempted = True
        invalid = [answer for answer in self._required() if not answer.validate()]
        self._refresh()
        if invalid:
            self._scroll_to(invalid[0])
            return
        self.set_busy(True)
        self.submitted.emit(self.collect())

    def collect(self) -> PatientFormData:
        """Builds the DTO sent to the controller from the validated form.

        Returns:
            The patient and their answers to the health questionnaire.
        """
        answers = {answer.question.key: answer.value() for answer in self._answers() if answer.question is not None}
        return PatientFormData(
            name=self.name.text(),
            medical_notes=self.notes.toPlainText().strip(),
            risk_answers={key: value for key, value in answers.items() if value is not None},
        )

    def _scroll_to(self, answer: Answer) -> None:
        """Scrolls smoothly until the answer is in view, and focuses it."""
        bar = self.scroll.verticalScrollBar()
        start = bar.value()
        self.scroll.ensureWidgetVisible(answer, 0, Space.S8)
        end = bar.value()
        bar.setValue(start)
        answer.focus_target().setFocus(Qt.FocusReason.OtherFocusReason)
        if start != end:
            self._scroll_animation = QPropertyAnimation(bar, b"value", self)
            self._scroll_animation.setDuration(Motion.SLOW)
            self._scroll_animation.setEasingCurve(QEasingCurve(Motion.OUT))
            self._scroll_animation.setStartValue(start)
            self._scroll_animation.setEndValue(end)
            self._scroll_animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    # ------------------------------------------------------------------ API (PatientsPage)
    def focus_first(self) -> None:
        """Focuses the patient's name."""
        self.name.edit.setFocus(Qt.FocusReason.OtherFocusReason)

    def set_busy(self, busy: bool) -> None:
        """Locks the form while the controller adds the patient.

        Args:
            busy: True to lock it (and show the spinner), False to unlock it.
        """
        self._busy = busy
        self._column.setEnabled(not busy)
        self.actions.cancel.setEnabled(not busy)
        self.actions.submit.set_loading(busy, Text.ADDING)

    def is_busy(self) -> bool:
        """True while the controller is handling the form."""
        return self._busy

    def show_message_error(self, message: str) -> None:
        """The controller could not add the patient: unlock and explain it at the top of the form."""
        self.set_busy(False)
        self.error.set_message(message)
        self._error_box.show()
        self.scroll.verticalScrollBar().setValue(0)

    def reset(self) -> None:
        """Clears every answer and error and scrolls back to the top."""
        self.set_busy(False)
        self._attempted = False
        self._error_box.hide()
        for answer in self._answers():
            answer.reset()
        self.notes.clear()
        self._refresh(animate=False)
        self.scroll.verticalScrollBar().setValue(0)

    # ------------------------------------------------------------------ keyboard
    def keyPressEvent(self, event) -> None:
        """Enter presses the focused button or moves to the next field; Esc does nothing."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.accept()
            focused = QApplication.focusWidget()
            if isinstance(focused, QAbstractButton):
                focused.click()
            elif isinstance(focused, QLineEdit):
                self.focusNextChild()
            return
        if event.key() == Qt.Key.Key_Escape:
            event.accept()
            return
        super().keyPressEvent(event)

    def sizeHint(self) -> QSize:
        """Preferred size: the column and its margins."""
        return QSize(CONTENT + 2 * Space.S6, 720)

