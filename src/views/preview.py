"""Preview harness for the views: no camera, no database, no models.

    python -m src.views.preview                     interactive: sign in, then the monitoring screen
    python -m src.views.preview --admin             ... with the administration screen
    python -m src.views.preview --shots DIR         screenshots of every state at 1120x720, 1366x768, 1920x1080
    python -m src.views.preview --shots DIR --size 1366x768
    python -m src.views.preview --perf              counts side-panel resizes during 30 fps playback

Fake controllers replay the same call sequences as the real ones (see BaseMonitorController).
At start-up it checks the colour contrast and that the toast rules still match the controllers.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from collections.abc import Callable
from pathlib import Path

ALLOWED_QT_MODULES = {"QtCore", "QtGui", "QtWidgets", "QtSvg"}
SIZES = ((1120, 720), (1366, 768), (1920, 1080))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m src.views.preview", description=__doc__.splitlines()[0])
    parser.add_argument("--shots", metavar="DIR", help="save screenshots of every state into DIR")
    parser.add_argument("--admin", action="store_true", help="interactive mode: use the administration screen")
    parser.add_argument("--size", metavar="WxH", help="window size (default: the three design sizes in --shots)")
    parser.add_argument("--perf", action="store_true", help="measure relayouts of the side panels while playing")
    parser.add_argument("--native-dpr", action="store_true", help="keep the screen's scaling in --shots")
    return parser.parse_args(argv)


ARGS = _parse_args(sys.argv[1:])
if (ARGS.shots or ARGS.perf) and not ARGS.native_dpr:
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"      # screenshots in logical pixels

from PySide6.QtCore import QObject, QPoint, QSettings, Qt, QTimer, Slot
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from src.dtos.registration_data import RegistrationData
from src.views.admin_view import AdminView
from src.views.auth_view import AuthView
from src.views.base_monitor_view import BaseMonitorView
from src.views.components.common.confirm_dialog import ConfirmDialog
from src.views.components.common.toast import ToastHost
from src.views.monitor_view import MonitorView
from src.views.strings import Monitor, check_toast_rules
from src.views.theme import APP_NAME, Colors, ThemeManager, check_contrast


# ---------------------------------------------------------------------- synthetic media
def synthetic_frame(t: float, width: int = 1280, height: int = 720) -> QImage:
    """A moving gradient with a stick figure, standing in for a camera frame."""
    image = QImage(width, height, QImage.Format.Format_RGB32)
    painter = QPainter(image)
    shift = (t * 0.08) % 1.0
    gradient = QLinearGradient(0, 0, width, height)
    gradient.setColorAt(0.0, QColor.fromHsvF(shift, 0.30, 0.50))
    gradient.setColorAt(1.0, QColor.fromHsvF((shift + 0.35) % 1.0, 0.35, 0.22))
    painter.fillRect(image.rect(), gradient)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    _stick_figure(painter, width / 2 + math.sin(t) * width * 0.15, height * 0.18, height * 0.6, QColor("#5BD18B"), 4)
    painter.end()
    return image


def synthetic_skeleton(t: float) -> QImage:
    image = QImage(360, 480, QImage.Format.Format_RGB32)
    image.fill(QColor(Colors.STAGE))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    _stick_figure(painter, 180 + math.sin(t) * 10, 60, 380, QColor("#5BD18B"), 6)
    painter.end()
    return image


def _stick_figure(painter: QPainter, x: float, top: float, height: float, color: QColor, width: int) -> None:
    painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    head = height * 0.09
    neck, hip = top + head * 2, top + height * 0.55
    painter.drawEllipse(QPoint(round(x), round(top + head)), round(head), round(head))
    painter.drawLine(round(x), round(neck), round(x), round(hip))
    painter.drawLine(round(x - height * 0.2), round(neck + height * 0.15), round(x + height * 0.2), round(neck + height * 0.15))
    painter.drawLine(round(x), round(hip), round(x - height * 0.15), round(top + height))
    painter.drawLine(round(x), round(hip), round(x + height * 0.15), round(top + height))


# ---------------------------------------------------------------------- fake controllers
class FakeAuthController(QObject):
    """Accepts any password except "wrong"; registration always succeeds with MEDIUM risk."""

    def __init__(self, view: AuthView, on_success: Callable[[], None]):
        super().__init__(view)
        self.view = view
        self.on_success = on_success
        self.registrations: list[RegistrationData] = []
        view.login_requested.connect(self.login)
        view.register_requested.connect(self.register)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(1500)
        self._timer.timeout.connect(self.on_success)

    @Slot(str, str)
    def login(self, email: str, password: str) -> None:
        if password == "wrong":
            self.view.show_error("Invalid email or password. Please try again.")
            return
        self.view.show_success("Welcome back! Authentication successful.")
        self._timer.start()

    @Slot(object)
    def register(self, data: RegistrationData) -> None:
        self.registrations.append(data)
        print(f"[preview] registration: role={data.role!r}, {len(data.risk_answers)} answers")
        if data.email.startswith("taken"):
            self.view.show_error("Registration failed. This email is already in use.")
            return
        self.view.show_success("Account created! The patient's risk level is MEDIUM.")
        self._timer.start()


class FakeMonitorController(QObject):
    """Mirrors BaseMonitorController's call order. Camera 2 does not exist; files last 6 s."""

    def __init__(self, view: BaseMonitorView, *, auto_falls: bool = True):
        super().__init__(view)
        self.view = view
        self.auto_falls = auto_falls
        self.running = False
        self.waiting_first_frame = False
        self.t = 0.0
        self.frames = 0
        self.is_file = False
        view.start_requested.connect(self.start_camera)
        view.upload_requested.connect(self.start_file)
        view.stop_requested.connect(self.stop)

        self.frame_timer = self._timer(33, self.frame, single=False)
        self.connect_timer = self._timer(900, self.connected)
        self.fail_timer = self._timer(700, self.fail)
        self.stop_timer = self._timer(450, self.finish)
        self.end_timer = self._timer(6000, self.finish)
        self.mail_timer = self._timer(1200, self.mail_sent)
        self._pending_failure = ""

    def _timer(self, interval: int, slot, *, single: bool = True) -> QTimer:
        timer = QTimer(self)
        timer.setInterval(interval)
        timer.setSingleShot(single)
        timer.timeout.connect(slot)
        return timer

    @Slot(int)
    def start_camera(self, index: int) -> None:
        if self.running:
            return
        self._begin(f"Starting camera {index}...", is_file=False)
        if index == 2:
            self._pending_failure = f"Could not open camera {index}"
            self.fail_timer.start()
        else:
            self.connect_timer.start()

    @Slot(str)
    def start_file(self, path: str) -> None:
        if self.running:
            return
        self._begin(f"Processing video file: {os.path.basename(path)}", is_file=True)
        self.connect_timer.start()

    def _begin(self, message: str, *, is_file: bool) -> None:
        self.running, self.is_file, self.frames = True, is_file, 0
        self.waiting_first_frame = True
        self.view.set_monitoring_state(True)
        self.view.log_event("INFO", message)

    @Slot()
    def connected(self) -> None:
        self.frame_timer.start()
        if self.is_file:
            self.end_timer.start()

    @Slot()
    def frame(self) -> None:
        if self.waiting_first_frame:
            self.waiting_first_frame = False
            self.view.log_event("INFO", "Stream connected")
        self.t += 0.033
        self.frames += 1
        self.view.update_video_frame(synthetic_frame(self.t))
        if isinstance(self.view, AdminView):
            self.view.skeleton_panel.update_frame(synthetic_skeleton(self.t))
            self.view.skeleton_panel.update_telemetry({
                "inference_ms": 11 + 4 * abs(math.sin(self.t)),
                "confidence": 0.45 + 0.5 * abs(math.sin(self.t / 3)),
                "centroid_y": 0.52 + 0.1 * math.sin(self.t),
            })
        if self.auto_falls and self.frames in (120, 210):
            self.fall(0.87 if self.frames == 120 else 0.91)

    def fall(self, probability: float) -> None:
        self.view.trigger_fall_alert(f"Fall detected ({probability:.0%})")
        self.view.log_event("INFO", "Sending notification e-mail...")
        self.mail_timer.start()

    @Slot()
    def mail_sent(self) -> None:
        self.view.log_event("INFO", "Notification e-mail sent")

    @Slot()
    def stop(self) -> None:
        if not self.running:
            return
        self.view.set_stopping()
        self.stop_timer.start()

    @Slot()
    def fail(self) -> None:
        self.view.log_event("ERROR", self._pending_failure)
        self.finish()

    @Slot()
    def finish(self) -> None:
        for timer in (self.frame_timer, self.connect_timer, self.end_timer):
            timer.stop()
        if not self.running:
            return
        self.running = False
        self.view.set_monitoring_state(False)
        self.view.log_event("INFO", "Stream disconnected")
        self.view.clear_video()


# ---------------------------------------------------------------------- checks
def run_checks() -> list[str]:
    problems = [f"contrast: {failure}" for failure in check_contrast()]
    problems += [f"toast rule no longer in the controllers: {key!r}" for key in check_toast_rules()]
    return problems


def forbidden_modules() -> list[str]:
    loaded = {name.split(".")[1] for name in sys.modules if name.startswith("PySide6.Qt")}
    return sorted(loaded - ALLOWED_QT_MODULES)


# ---------------------------------------------------------------------- interactive mode
class PreviewWindow(QMainWindow):
    def __init__(self, admin: bool):
        super().__init__()
        from src.router.router import ViewRouter

        self.setWindowTitle(f"{APP_NAME} preview")
        self.setMinimumSize(1120, 720)
        self.admin = admin
        self.router = ViewRouter(self)
        self.auth_view = AuthView()
        self.auth_controller = FakeAuthController(self.auth_view, self.open_dashboard)
        self.router.add_view(self.auth_view)
        self.router.navigate_to(self.auth_view)
        self.monitor_view: BaseMonitorView | None = None

    @Slot()
    def open_dashboard(self) -> None:
        cls = AdminView if self.admin else MonitorView
        self.monitor_view = cls(user_name="Ana García", user_role="Administrator" if self.admin else "Medical Staff",
                                patient_name="José Martínez", risk_level="MEDIUM")
        FakeMonitorController(self.monitor_view)
        self.monitor_view.logout_requested.connect(self.logout)
        self.router.add_view(self.monitor_view)
        self.router.navigate_to(self.monitor_view)

    @Slot()
    def logout(self) -> None:
        view = self.monitor_view

        def cleanup() -> None:
            if view is not None:
                self.router.remove_view(view)
                view.deleteLater()

        self.monitor_view = None
        self.router.navigate_to(self.auth_view, on_finish_callback=cleanup)


# ---------------------------------------------------------------------- scripted runs
class Script(QObject):
    """Runs (delay_ms, action) steps one after another on the event loop."""

    def __init__(self, steps: list[tuple[int, Callable[[], None]]], app: QApplication):
        super().__init__(app)
        self.steps = steps
        self.index = 0
        self.failures: list[str] = []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.next)

    def start(self) -> None:
        self.timer.start(300)

    @Slot()
    def next(self) -> None:
        if self.index >= len(self.steps):
            QApplication.instance().exit(1 if self.failures else 0)
            return
        _, action = self.steps[self.index]
        try:
            action()
        except Exception as error:  # noqa: BLE001  (report and keep going: one broken step must not hide the rest)
            self.failures.append(f"step {self.index}: {error!r}")
            print(f"[preview] step {self.index} failed: {error!r}")
        self.index += 1
        delay = self.steps[self.index][0] if self.index < len(self.steps) else 0
        self.timer.start(delay)


def _window(view: QWidget, size: tuple[int, int]) -> QMainWindow:
    window = QMainWindow()
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
    window.setWindowTitle(APP_NAME)
    window.setCentralWidget(view)
    window.resize(*size)
    window.show()
    return window


def _clear_toasts(window: QWidget) -> None:
    for toast in ToastHost.for_widget(window).toasts():
        toast.dismiss()


def shot_steps(out: Path, size: tuple[int, int], keep: list) -> list[tuple[int, Callable[[], None]]]:
    width, height = size
    suffix = f"{width}x{height}"
    steps: list[tuple[int, Callable[[], None]]] = []

    def shot(window_ref: list, name: str, delay: int = 450) -> None:
        steps.append((delay, lambda: window_ref[0].grab().save(str(out / f"{name}_{suffix}.png"))))

    def do(action: Callable[[], None], delay: int = 50) -> None:
        steps.append((delay, action))

    # --- administration screen
    admin_ref: list = [None]
    view_ref: list = [None]
    controller_ref: list = [None]

    def build_admin() -> None:
        view = AdminView(user_name="Ana García", user_role="Administrator", patient_name="José Martínez",
                         risk_level="MEDIUM")
        controller_ref[0] = FakeMonitorController(view, auto_falls=False)
        view_ref[0] = view
        admin_ref[0] = _window(view, size)
        keep.append(admin_ref[0])

    do(build_admin)
    shot(admin_ref, "01_idle", 600)
    do(lambda: view_ref[0].video_panel.primary.click())
    shot(admin_ref, "02_starting", 300)
    do(lambda: controller_ref[0].connected(), 600)
    shot(admin_ref, "03_live", 1400)
    do(lambda: controller_ref[0].fall(0.87), 50)
    do(lambda: controller_ref[0].fall(0.91), 400)
    shot(admin_ref, "04_alert", 1500)
    do(lambda: view_ref[0].event_log.filter_combo.setCurrentIndex(1))
    shot(admin_ref, "05_log_filtered", 300)
    do(lambda: view_ref[0].event_log.filter_combo.setCurrentIndex(0))

    def open_dialog() -> None:
        dialog = ConfirmDialog(view_ref[0], Monitor.CONFIRM_SIGN_OUT_TITLE, Monitor.CONFIRM_SIGN_OUT_BODY,
                               Monitor.CONFIRM_SIGN_OUT_ACTION, destructive=True)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
        dialog.show()
        keep.append(dialog)

    def save_dialog() -> None:
        dialog = keep[-1]
        base = admin_ref[0].grab()
        painter = QPainter(base)
        card = dialog.grab()
        painter.drawPixmap((base.width() - card.width()) // 2, (base.height() - card.height()) // 2, card)
        painter.end()
        base.save(str(out / f"06_dialog_sign_out_{suffix}.png"))
        dialog.close()

    do(open_dialog, 50)
    do(save_dialog, 400)
    do(lambda: view_ref[0]._acknowledge_alert(), 100)
    do(lambda: view_ref[0].video_panel.primary.click(), 100)
    shot(admin_ref, "07_stopping", 150)
    shot(admin_ref, "08_stopped", 900)
    do(lambda: _clear_toasts(admin_ref[0]), 50)
    do(lambda: (view_ref[0].video_panel.source_combo.setCurrentIndex(2), view_ref[0].video_panel.primary.click()), 400)
    shot(admin_ref, "09_error", 1500)
    do(lambda: _clear_toasts(admin_ref[0]), 50)
    do(lambda: view_ref[0]._start_file("C:/videos/clip.mp4"), 400)
    do(lambda: controller_ref[0].connected(), 600)
    do(lambda: controller_ref[0].finish(), 1500)
    shot(admin_ref, "10_finished", 700)

    # --- monitoring screen of a user without a patient
    user_ref: list = [None]

    def build_user() -> None:
        view = MonitorView(user_name="Laura Pérez Gómez", user_role="Family / Caregiver")
        FakeMonitorController(view, auto_falls=False)
        user_ref[0] = _window(view, size)
        keep.append(user_ref[0])

    do(build_user, 100)
    shot(user_ref, "11_user_no_patient", 600)

    # --- sign-in and sign-up
    auth_ref: list = [None]
    auth_view_ref: list = [None]

    def build_auth() -> None:
        view = AuthView()
        FakeAuthController(view, lambda: None)
        auth_view_ref[0] = view
        auth_ref[0] = _window(view, size)
        keep.append(auth_ref[0])

    do(build_auth, 100)
    shot(auth_ref, "12_login", 600)

    def wrong_password() -> None:
        page = auth_view_ref[0].login_page
        page.email.setText("ana@example.com")
        page.password.setText("wrong")
        page._submit()

    do(wrong_password)
    shot(auth_ref, "13_login_error", 500)
    do(lambda: _clear_toasts(auth_ref[0]))
    do(lambda: auth_view_ref[0].login_page.create_link.click(), 400)

    def register() -> object:
        return auth_view_ref[0].register_page

    for step in range(5):
        do(lambda: register()._on_next(), 400)
        shot(auth_ref, f"{14 + step}_register_step{step + 1}_errors", 450)
        do(lambda: _clear_toasts(auth_ref[0]), 50)
        do(lambda step=step: _fill_register_step(register(), step), 300)
        if step < 4:
            do(lambda: register()._on_next(), 100)
    return steps


def _fill_register_step(page, step: int) -> None:
    if step == 0:
        page.name.setText("Ana García")
        page.phone.setText("+34 600 000 000")
        page.role.set_selected(0)
    elif step == 1:
        page.email.setText("ana@example.com")
        page.password.setText("Secret12!")
        page.confirm.setText("Secret12!")
    elif step == 2:
        page.patient.setText("José Martínez")
        for field in page.profile.fields:
            _answer(field)
    elif step == 3:
        for field in page.daily.fields:
            _answer(field)
    else:
        for field in page.health.fields:
            _answer(field)


def _answer(field) -> None:
    if field.options is not None:
        if hasattr(field.options, "set_selected"):
            field.options.set_selected(1)
        else:
            field.options.buttons[1].setChecked(True)
    elif field.edit is not None:
        value = 78 if field.question.maximum >= 50 else 4
        field.edit.setText(str(max(field.question.minimum, min(field.question.maximum, value))))


def perf_steps(size: tuple[int, int], keep: list, report: dict) -> list[tuple[int, Callable[[], None]]]:
    """Plays 5 s at 30 fps and counts Resize events of the side panels (must stay at 0)."""

    class Counter(QObject):
        def __init__(self):
            super().__init__()
            self.count = 0
            self.active = False

        def eventFilter(self, watched, event) -> bool:
            if self.active and event.type() == event.Type.Resize:
                self.count += 1
            return False

    counter = Counter()
    keep.append(counter)
    refs: dict = {}

    def build() -> None:
        view = AdminView(user_name="Ana García", user_role="Administrator", patient_name="José", risk_level="HIGH")
        refs["controller"] = FakeMonitorController(view, auto_falls=False)
        refs["view"] = view
        keep.append(_window(view, size))
        for panel in (view.skeleton_panel, view.session_panel):
            panel.installEventFilter(counter)

    def start() -> None:
        refs["view"].video_panel.primary.click()
        refs["controller"].connected()

    def arm() -> None:
        counter.active = True

    def measure() -> None:
        counter.active = False
        report["frames"] = refs["controller"].frames
        report["resizes"] = counter.count

    return [(0, build), (400, start), (1500, arm), (5000, measure), (100, lambda: refs["controller"].finish())]


# ---------------------------------------------------------------------- entry point
def main() -> int:
    app = QApplication(sys.argv[:1])
    app.setQuitOnLastWindowClosed(not (ARGS.shots or ARGS.perf))
    ThemeManager.setup_theme(app)
    settings = QSettings("FallSense", "FallSense")
    saved = {key: settings.value(key) for key in ("monitor/log_filter", "monitor/log_height")}

    problems = run_checks()
    for problem in problems:
        print(f"[preview] WARNING {problem}")
    sizes = SIZES
    if ARGS.size:
        width, height = (int(value) for value in ARGS.size.lower().split("x"))
        sizes = ((width, height),)

    keep: list = []
    exit_code = 0
    if ARGS.shots:
        out = Path(ARGS.shots)
        out.mkdir(parents=True, exist_ok=True)
        steps: list = []
        for size in sizes:
            steps += shot_steps(out, size, keep)
            steps.append((100, lambda: [w.close() for w in keep if isinstance(w, QMainWindow)]))
        script = Script(steps, app)
        script.start()
        exit_code = app.exec()
        print(f"[preview] screenshots saved in {out.resolve()}")
    elif ARGS.perf:
        report: dict = {}
        script = Script(perf_steps(sizes[0], keep, report), app)
        script.start()
        exit_code = app.exec()
        print(f"[preview] perf: {report.get('frames')} frames played, side-panel resizes while playing: "
              f"{report.get('resizes')}")
        if report.get("resizes"):
            exit_code = 1
    else:
        window = PreviewWindow(ARGS.admin)
        window.resize(*sizes[min(1, len(sizes) - 1)])
        window.show()
        exit_code = app.exec()

    for key, value in saved.items():     # the harness must not change the user's preferences
        if value is None:
            settings.remove(key)
        else:
            settings.setValue(key, value)

    extra = forbidden_modules()
    if extra:
        print(f"[preview] ERROR modules outside PySide6-Essentials were loaded: {', '.join(extra)}")
        exit_code = 1
    if problems:
        exit_code = exit_code or 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

