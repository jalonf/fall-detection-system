"""Alert thread: stores every fall and e-mails the caregiver."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, Signal
from PySide6.QtGui import QImage, QImageWriter

from src.database.connection import db
from src.dtos.fall_alert import FallAlert
from src.notifications.email_notifier import EmailNotifier
from src.repositories.fall_repository import FallRepository
from src.strings import Messages

logger = logging.getLogger(__name__)

THREAD_NAME = "alert-thread"
EMAIL_COOLDOWN_S = 60      # at most one alert e-mail per minute; every fall is stored anyway
SNAPSHOT_QUALITY = 85      # JPEG quality of the capture attached to the e-mail


class AlertThread(QObject):
    """Alert thread: stores each fall and sends the alert e-mail, without blocking the video or the window.

    It is the third of the three threads of a monitoring session: the controller creates it when
    monitoring starts (together with the `VideoThread`), hands it each fall the `VideoThread`
    reports, and closes it when monitoring stops ("Stop", the end of a video file, signing out).

    The object is created and called in the GUI thread: `handle` returns at once and the work
    runs in the alert thread itself, a single thread named `alert-thread` (a one-thread
    `ThreadPoolExecutor`, which starts it with the first fall). There, in order, it:

    1. stores the `FallEvent` in the database (with its own connection, opened and closed there);
    2. encodes the capture as JPEG (only in memory) and sends the e-mail;
    3. marks the event as notified and emits `notification_sent`.

    Falls are handled one after another, so there is never more than one alert thread. Every
    fall is stored, but at most one e-mail goes out per `EMAIL_COOLDOWN_S`, so a person who
    struggles on the floor does not flood the caregiver's inbox.

    Signals:
        notification_sent(bool): Result of an alert e-mail. Emitted from the alert thread, so a
            receiver living in the GUI thread gets it as a queued call.

    Args:
        user: The signed-in caregiver; the e-mails go to their address.
        patient: Their patient (whose falls are stored), or None (nothing is stored).
    """

    notification_sent = Signal(bool)

    def __init__(self, user, patient=None):
        super().__init__()
        self.user = user
        self.patient = patient
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=THREAD_NAME)
        self._last_email_at = float("-inf")
        self._closed = False

    # ------------------------------------------------------------------ GUI thread
    def handle(self, probability: float, frame: QImage | None) -> bool:
        """A fall has just started: queues storing it and, unless one was sent recently, e-mailing it.

        Args:
            probability: The model's probability (0-1) for the fall.
            frame: The frame on screen when the fall was reported (face already blurred), or None.

        Returns:
            True when an e-mail will be sent; False when only the fall is stored (an e-mail went
            out less than `EMAIL_COOLDOWN_S` ago) or the service is closed. A failed e-mail does
            not count towards that minute, so the next fall tries again.
        """
        if self._closed:
            return False

        now = time.monotonic()
        send_email = now - self._last_email_at >= EMAIL_COOLDOWN_S
        if send_email:
            self._last_email_at = now
        timestamp = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M:%S")
        self._executor.submit(self._process, probability, frame, timestamp, send_email)
        return send_email

    def shutdown(self) -> None:
        """Takes no more falls. The ones already queued are still stored and e-mailed.

        It does not wait: stopping or signing out never blocks on the SMTP server. Python waits for the
        alert thread before the program exits, so no queued alert is lost.
        """
        self._closed = True
        self._executor.shutdown(wait=False)

    # ------------------------------------------------------------------ alert thread
    def _process(self, probability: float, frame: QImage | None, timestamp: str, send_email: bool) -> None:
        """Runs in the alert thread, one fall at a time: store it, e-mail it, mark it as notified."""
        try:
            # 1. Store the fall, with this thread's own connection (opened and closed here).
            fall_event = None
            if self.patient is not None:
                with db.connection_context():
                    fall_event = FallRepository().create_fall_event(self.patient, probability)
            if not send_email:
                return

            # 2. E-mail it, with the capture attached (encoded in memory, never written to disk).
            alert = FallAlert(
                patient_name=getattr(self.patient, "name", None) or self.user.name,
                medical_notes=getattr(self.patient, "medical_notes", None) or Messages.NO_NOTES,
                probability=probability,
                timestamp=timestamp,
                snapshot=encode_jpeg(frame),
            )
            ok = EmailNotifier(self.user.email).send(alert)
            if not ok:
                self._last_email_at = float("-inf")   # a failed e-mail does not count: the next fall tries again

            # 3. Mark it as notified and tell the interface (the signal is queued to the GUI thread).
            if ok and fall_event is not None:
                with db.connection_context():
                    FallRepository().mark_notification_sent(fall_event)
            self.notification_sent.emit(ok)
        except Exception:   # a failing alert must never kill the alert thread
            logger.exception("Unexpected error while handling a fall alert")
            if send_email:
                self._last_email_at = float("-inf")
                self.notification_sent.emit(False)


def encode_jpeg(image: QImage | None) -> bytes | None:
    """JPEG of the image, in memory (nothing is written to disk), or None.

    QImage is safe to use outside the GUI thread, so this runs in the alert thread.

    Args:
        image: The frame to encode, or None.

    Returns:
        The JPEG bytes, or None when there is no image or it could not be encoded.
    """
    if image is None or image.isNull():
        return None
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    writer = QImageWriter(buffer, b"jpg")
    writer.setQuality(SNAPSHOT_QUALITY)
    ok = writer.write(image)
    buffer.close()
    return bytes(data.data()) if ok else None
