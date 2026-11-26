"""Dashboards: the screen a user sees once signed in.

A dashboard is a shell: the top bar (the mark, the tabs or the page's title, the date and the
account menu) over a stack of pages, one per tab. The pages do not know about each other or about the top bar; the dashboard switches
between them (with a short cross-fade) and applies the rules that link them.

* `AdminDashboardView`: one page, the administrators' monitoring (`AdminView`); no tabs.
* `CaregiverDashboardView`: two tabs, Monitoring (`MonitorView`) and Patients (`PatientsPage`).

Contract (used by `AppCoordinator`): the signal `logout_requested`, emitted once the user has
confirmed signing out; `monitoring` and, for caregivers, `patients` are the pages their controllers
drive.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from src.dtos.patient_summary import PatientSummary
from src.views.admin_view import AdminView
from src.views.base_monitor_view import BaseMonitorView
from src.views.components.common.confirm_dialog import ConfirmDialog
from src.views.components.common.page_transition import PageTransition
from src.views.components.common.shortcuts import add_shortcut
from src.views.components.common.toast import ToastHost
from src.views.components.monitor.topbar import Topbar
from src.views.components.patients.patients_page import PatientsPage
from src.views.monitor_view import MonitorView
from src.views.screen_view import ScreenView
from src.views.strings import Monitor
from src.views.theme import Motion, Size, Space

TAB_SHIFT = 12       # the page being left drifts this far towards the side it is left on


class DashboardView(ScreenView):
    """Top bar over one page per tab; the first page is always the monitoring one.

    Subclasses build the pages (`_make_monitoring`, `_make_other_pages`) and name the tabs (`TABS`,
    one per page) or, with a single page, give its `TITLE`.

    Signals:
        logout_requested: The user chose Sign out and confirmed it if a monitoring was running.

    Args:
        user_name: Name of the signed-in user.
        user_role: Their role, shown under the name.
        parent: Parent widget.
    """
    logout_requested = Signal()

    TITLE = ""
    TABS: tuple[str, ...] = ()

    def __init__(self, user_name: str = "", user_role: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self._signing_out = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.monitoring = self._make_monitoring()
        pages = [self.monitoring, *self._make_other_pages()]
        if self.TABS and len(self.TABS) != len(pages):
            raise ValueError("A dashboard with tabs needs one tab per page")

        self.topbar = Topbar(user_name, user_role, tabs=self.TABS, title=self.TITLE)
        self.topbar.sign_out_clicked.connect(self._request_sign_out)
        self.topbar.tab_changed.connect(self.show_tab)
        layout.addWidget(self.topbar)
        self._page_list: list[QWidget] = pages
        self._pages = QStackedWidget()
        for page in pages:
            self._pages.addWidget(page)
        layout.addWidget(self._pages, 1)
        self._tab_transition = PageTransition(self, shift=TAB_SHIFT, duration=Motion.SLOW, crossfade=True)

        add_shortcut(self, (Monitor.SIGN_OUT_SHORTCUT,), self._request_sign_out)
        self.monitoring.state_changed.connect(self._on_monitoring_state)
        self._connect_pages()

    # ------------------------------------------------------------------ hooks
    def _make_monitoring(self) -> BaseMonitorView:
        """Builds the monitoring page (the first tab)."""
        raise NotImplementedError

    def _make_other_pages(self) -> list[QWidget]:
        """Builds the pages of the other tabs, in order."""
        return []

    def _connect_pages(self) -> None:
        """Connects the pages to each other, once they all exist."""

    def _on_monitoring_state(self, _state: str) -> None:
        """The monitoring page changed state (e.g. to lock tabs while it runs)."""

    # ------------------------------------------------------------------ tabs
    @Slot(int)
    def show_tab(self, index: int) -> None:
        """Shows the page of a tab (ignored while that tab is locked)."""
        if self.TABS and not self.topbar.tabs[index].isEnabled():
            self.topbar.set_current_tab(self._pages.currentIndex())
            return
        forward = index > self._pages.currentIndex()
        self._tab_transition.slide(self._pages, self._page_list[index], forward)
        if self.TABS:
            self.topbar.set_current_tab(index)
        self._focus_page()

    def _focus_page(self) -> None:
        """The monitoring page takes the keyboard focus when shown, so its shortcuts work at once."""
        if self._pages.currentWidget() is self.monitoring:
            self.monitoring.setFocus(Qt.FocusReason.OtherFocusReason)

    def _lock_tab(self, index: int, locked: bool, reason: str) -> None:
        """Disables a tab (its tooltip says why) or enables it again."""
        self.topbar.set_tab_enabled(index, not locked, reason)

    # ------------------------------------------------------------------ signing out
    @Slot()
    def _request_sign_out(self) -> None:
        """Signs out, asking first if a monitoring is running (signing out stops it)."""
        if self._signing_out:
            return
        if self.monitoring.is_running() and not ConfirmDialog.ask(
                self, Monitor.CONFIRM_SIGN_OUT_TITLE, Monitor.CONFIRM_SIGN_OUT_BODY,
                Monitor.CONFIRM_SIGN_OUT_ACTION, destructive=True):
            return
        self._signing_out = True
        self.logout_requested.emit()

    # ------------------------------------------------------------------ life cycle
    def entered(self) -> None:
        """Closes the sign-in toasts; later toasts appear under the top bar."""
        host = ToastHost.for_widget(self)
        host.dismiss_all()      # "Signed in · Opening your dashboard…" has done its job
        host.set_top_inset(Size.TOPBAR + Space.S4)
        self._focus_page()


class AdminDashboardView(DashboardView):
    """Dashboard of the administrators (testers): only the monitoring page, in test mode."""
    TITLE = Monitor.ADMIN_TITLE

    def _make_monitoring(self) -> AdminView:
        return AdminView()


class CaregiverDashboardView(DashboardView):
    """Dashboard of caregivers and medical staff: Monitoring and Patients tabs.

    Rules that link the two pages:

    * the Patients page's list fills the monitoring page's patient selector;
    * with no patients the Monitoring tab is disabled and the Patients tab is shown (the first thing
      a new caregiver does is add the person they look after); with patients, the dashboard opens
      on Monitoring;
    * while a monitoring runs the Patients tab is locked, so the patient being monitored cannot be
      deleted.
    """
    TABS = (Monitor.TAB_MONITORING, Monitor.TAB_PATIENTS)
    MONITORING_TAB, PATIENTS_TAB = 0, 1

    monitoring: MonitorView

    def _make_monitoring(self) -> MonitorView:
        return MonitorView()

    def _make_other_pages(self) -> list[QWidget]:
        self.patients = PatientsPage()
        return [self.patients]

    def _connect_pages(self) -> None:
        self.patients.patients_changed.connect(self._on_patients_changed)
        self._refresh_locks()

    @Slot(list)
    def _on_patients_changed(self, patients: list[PatientSummary]) -> None:
        self.monitoring.set_patients(patients)
        self._refresh_locks()
        if not patients:
            self.show_tab(self.PATIENTS_TAB)

    def _on_monitoring_state(self, _state: str) -> None:
        self._refresh_locks()

    def _refresh_locks(self) -> None:
        self._lock_tab(self.PATIENTS_TAB, self.monitoring.is_running(), Monitor.TAB_PATIENTS_LOCKED)
        self._lock_tab(self.MONITORING_TAB, not self.monitoring.has_patients(), Monitor.TAB_MONITORING_LOCKED)
