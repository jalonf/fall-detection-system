"""Patients page of the caregivers' screen: the list of patients, and the form that adds one.

Both sit on the dashboard's N50 canvas: the list in a centred column (at most `CONTENT_MAX` wide, so
the table does not stretch across a wide screen), the form as a narrower column of section cards.
Opening and closing the form slides between the two, so the form never just pops up.

Contract (used by `PatientsController`): the page emits `add_requested(PatientFormData)` and
`delete_requested(int)` (the deletion is confirmed here first); the controller answers with
`set_patients`, `show_patient_added`, `show_patient_deleted` or `show_error`.
"""

from __future__ import annotations

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from src.dtos.patient_form_data import PatientFormData
from src.dtos.patient_summary import PatientSummary
from src.views.components.common.confirm_dialog import ConfirmDialog
from src.views.components.common.page_transition import PageTransition
from src.views.components.common.painting import Surface
from src.views.components.common.toast import ToastHost
from src.views.components.patients.patient_form import PatientForm
from src.views.components.patients.patient_list import PatientList, falls_text
from src.views.strings import Patients
from src.views.theme import Colors, Space

CONTENT_MAX = 1200          # widest the list gets; on wider screens it is centred


class _ListSurface(Surface):
    """The list's page: N50 canvas whose side margins centre a column at most `CONTENT_MAX` wide."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(Colors.N50, parent=parent)
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(Space.S6, Space.S8, Space.S6, Space.S6)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        side = max(Space.S6, (self.width() - CONTENT_MAX) // 2)
        self.content_layout.setContentsMargins(side, Space.S8, side, Space.S6)


class PatientsPage(QWidget):
    """The list of patients and the new patient form, one at a time.

    Signals:
        add_requested(PatientFormData): The completed new patient form.
        delete_requested(int): The user confirmed deleting this patient.
        patients_changed(list): The list shown changed (the `PatientSummary` list).
    """
    add_requested = Signal(PatientFormData)
    delete_requested = Signal(int)
    patients_changed = Signal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._patients: list[PatientSummary] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._list_page = _ListSurface()
        self.list = PatientList()
        self.list.add_clicked.connect(self.open_form)
        self.list.delete_clicked.connect(self._confirm_delete)
        self._list_page.content_layout.addWidget(self.list)
        self._stack.addWidget(self._list_page)

        self._form_page = Surface(Colors.N50)     # opaque, so the slide's snapshots are too
        form_layout = QVBoxLayout(self._form_page)
        form_layout.setContentsMargins(0, 0, 0, 0)
        self.form = PatientForm()
        self.form.submitted.connect(self.add_requested)
        self.form.cancelled.connect(self.close_form)
        form_layout.addWidget(self.form)
        self._stack.addWidget(self._form_page)

        self._transition = PageTransition(self, background=Colors.N50)
        self._transition.finished.connect(self._focus_current)

    # ------------------------------------------------------------------ contract
    def set_patients(self, patients: list[PatientSummary]) -> None:
        """Shows the caregiver's patients.

        Args:
            patients: Oldest first.
        """
        self._patients = list(patients)
        self.list.set_patients(self._patients)
        self.patients_changed.emit(self._patients)

    def show_patient_added(self, name: str, risk_level: str) -> None:
        """The patient was saved: back to the list, with a toast that gives their risk level."""
        self.close_form()
        ToastHost.for_widget(self).success(Patients.ADDED.format(name=name, level=risk_level),
                                           title=Patients.ADDED_TITLE)

    def show_patient_deleted(self, name: str) -> None:
        """The patient was deleted."""
        ToastHost.for_widget(self).success(Patients.DELETED.format(name=name), title=Patients.DELETED_TITLE)

    def show_error(self, message: str) -> None:
        """The controller could not save or delete: in the form while it is open, otherwise a toast."""
        if self.is_form_open():
            self.form.show_message_error(message)
        else:
            ToastHost.for_widget(self).notify("error", message)

    # ------------------------------------------------------------------ API

    def is_form_open(self) -> bool:
        """True while the new patient form is shown."""
        return self._stack.currentWidget() is self._form_page

    @Slot()
    def open_form(self) -> None:
        """Slides in an empty new patient form."""
        if self._transition.is_running():
            return
        self.form.reset()
        self._transition.slide(self._stack, self._form_page, forward=True)

    @Slot()
    def close_form(self) -> None:
        """Slides back to the list (the form is emptied the next time it opens)."""
        self.form.set_busy(False)
        self._transition.slide(self._stack, self._list_page, forward=False)

    @Slot()
    def _focus_current(self) -> None:
        """After a slide: the form's first field, or "Add patient" (never a row's bin button)."""
        if self.is_form_open():
            self.form.focus_first()
        else:
            self.list.focus_add()

    @Slot(int)
    def _confirm_delete(self, patient_id: int) -> None:
        patient = next((p for p in self._patients if p.id == patient_id), None)
        if patient is None:
            return
        body = Patients.CONFIRM_DELETE_BODY.format(falls=falls_text(patient.fall_count))
        if ConfirmDialog.ask(self, Patients.CONFIRM_DELETE_TITLE.format(name=patient.name), body,
                             Patients.CONFIRM_DELETE_ACTION, destructive=True):
            self.delete_requested.emit(patient_id)
