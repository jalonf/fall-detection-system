"""Texts the application shows (Spanish): interface, messages, alert e-mail and video labels.

The health questionnaire is the exception: its texts stay in `src/domain/questionnaire.py`, next to the
values the risk model reads for each answer.

Overline texts are already written in upper case here; the stylesheet never transforms text.
"""

from __future__ import annotations

from typing import ClassVar

from src.domain.roles import ADMINISTRATOR, CAREGIVER, MEDICAL_STAFF

EM_DASH = "—"

# What the interface shows for values that are stored or used by the code in English.
RISK_LEVEL_LABELS = {"LOW": "bajo", "MEDIUM": "medio", "HIGH": "alto"}
ROLE_LABELS = {CAREGIVER: "Familiar / Cuidador", MEDICAL_STAFF: "Personal sanitario", ADMINISTRATOR: "Administrador"}


def risk_level_label(level: str) -> str:
    """Returns the Spanish name of a risk level ("alto" for "HIGH"); an unknown value is returned as it is."""
    return RISK_LEVEL_LABELS.get(level, level)


def role_label(role: str) -> str:
    """Returns the Spanish name of a stored user role; an unknown value is returned as it is."""
    return ROLE_LABELS.get(role, role)


class Common:
    """Texts shared by several screens."""
    CANCEL = "Cancelar"
    OPTIONAL = "Opcional"
    SHOW_PASSWORD = "Mostrar contraseña"
    HIDE_PASSWORD = "Ocultar contraseña"
    CLEAR_TEXT = "Borrar texto"
    UNEXPECTED_ERROR = "Algo ha fallado. Inténtalo de nuevo."


class Brand:
    """Brand panel of the sign-in screens."""
    HEADLINE = "Detección de caídas continua y privada"
    PARAGRAPH = "Para personas mayores, en casa o en una residencia."
    FEATURES = (
        ("activity", "Detección de caídas en tiempo real",
         "Una red neuronal recurrente analiza cada segundo de movimiento."),
        ("eye-off", "Privacidad desde el diseño", "La cara se difumina antes de mostrar, guardar o enviar imágenes."),
        ("bell", "Aviso inmediato al cuidador", "Al detectar una caída se envía un correo con la captura."),
    )
    FOOTER = "Trabajo de Fin de Grado · Universidad de León · 2026"


class Login:
    """Sign-in page."""
    TITLE = "Iniciar sesión"
    SUBTITLE = "Introduce los datos de tu cuenta para continuar."
    EMAIL = "Correo electrónico"
    EMAIL_PLACEHOLDER = "nombre@ejemplo.com"
    PASSWORD = "Contraseña"
    SUBMIT = "Iniciar sesión"
    SUBMITTING = "Iniciando sesión…"
    NEW_HERE = "¿Es tu primera vez en Vigía?"
    CREATE_ACCOUNT = "Crear una cuenta"
    EMAIL_REQUIRED = "Introduce tu correo electrónico."
    EMAIL_INVALID = "Introduce un correo electrónico válido."
    PASSWORD_REQUIRED = "Introduce tu contraseña."


class Form:
    """Questions of the health questionnaire."""
    CHOICE_REQUIRED = "Elige una respuesta."
    NUMBER_RANGE = "Introduce un número entero entre {minimum} y {maximum}."
    NUMBER_PLACEHOLDER = "{minimum}–{maximum}"


class Register:
    """Sign-up page: the caregiver's account only (patients are added afterwards)."""
    TITLE = "Crear una cuenta"
    SUBTITLE = "Tu cuenta de cuidador. Después podrás añadir a las personas que cuidas."
    CREATE = "Crear cuenta"
    CREATING = "Creando cuenta…"
    HAVE_ACCOUNT = "¿Ya tienes una cuenta?"
    SIGN_IN = "Iniciar sesión"

    FULL_NAME = "Nombre completo"
    PHONE = "Teléfono"
    PHONE_PLACEHOLDER = "+34 600 000 000"
    ROLE = "Rol"
    EMAIL = "Correo electrónico"
    EMAIL_PLACEHOLDER = "nombre@ejemplo.com"
    EMAIL_HELP = "Para iniciar sesión y recibir los avisos de caídas."
    PASSWORD = "Contraseña"
    CONFIRM_PASSWORD = "Repetir contraseña"
    CHECKLIST = (
        ("length", "8 caracteres o más"),
        ("upper", "Una letra mayúscula"),
        ("number", "Un número"),
        ("symbol", "Un símbolo"),
    )

    NAME_REQUIRED = "Introduce tu nombre completo."
    PHONE_INVALID = "Introduce un teléfono con prefijo, p. ej. +34 600 000 000."
    ROLE_REQUIRED = "Elige un rol."
    EMAIL_INVALID = "Introduce un correo electrónico válido."
    EMAIL_IN_USE = "Este correo ya está registrado."
    PASSWORD_WEAK = "La contraseña no cumple todos los requisitos."
    PASSWORD_TOO_LONG = "Contraseña demasiado larga: máximo 72 caracteres (menos con tildes o emojis)."
    PASSWORD_MISMATCH = "Las contraseñas no coinciden."


class PatientForm:
    """New patient form: who they are and the health questionnaire that sets their risk level."""
    BACK_TO_PATIENTS = "Pacientes"
    TITLE = "Nuevo paciente"
    SUBTITLE = ("Responde a todas las preguntas sobre la persona que cuidas. Las respuestas fijan su nivel de riesgo, "
                "que determina con cuánto detalle la vigila la cámara.")
    CANCEL = "Cancelar"
    ADD = "Añadir paciente"
    ADDING = "Añadiendo paciente…"
    PATIENT_NAME = "Nombre completo"
    PATIENT_REQUIRED = "Introduce el nombre completo del paciente."
    MEDICAL_NOTES = "Notas médicas"
    MEDICAL_NOTES_PLACEHOLDER = "p. ej. vértigo, movilidad reducida"
    PROGRESS = "{answered} de {total} respondidas"
    MISSING_ONE = "Falta 1 respuesta"
    MISSING_MANY = "Faltan {n} respuestas"
    SECTION_PROGRESS = "{answered} de {total}"
    SECTION_MISSING = "Faltan {n}"
    SECTION_DONE = "Completo"
    SECTION_OPTIONAL = "Marca todas las que procedan"
    DISCARD_TITLE = "¿Descartar este paciente?"
    DISCARD_BODY = "Se perderán las respuestas introducidas."
    DISCARD_ACTION = "Descartar"


class Patients:
    """Patients page: the caregiver's patients, add and delete."""
    TITLE = "Pacientes"
    SUBTITLE = "Las personas que cuidas. El nivel de riesgo de cada una ajusta la monitorización."
    COUNT_ONE = "1 paciente"
    COUNT_MANY = "{n} pacientes"
    ADD = "Añadir paciente"
    COLUMNS = ("NOMBRE", "RIESGO", "CAÍDAS", "ÚLTIMA CAÍDA", "AÑADIDO")
    NO_FALLS = "Sin caídas"
    DATE_FORMAT = "d MMM yyyy"
    DATE_TIME_FORMAT = "d MMM yyyy · HH:mm"
    DELETE_TIP = "Eliminar a {name}"
    EMPTY_TITLE = "Añade a la persona que cuidas"
    EMPTY_TEXT = "Añade un paciente para monitorizar. Sus respuestas de salud ajustan la cámara."
    CONFIRM_DELETE_TITLE = "¿Eliminar a {name}?"
    CONFIRM_DELETE_BODY = "También se borrará su historial ({falls}). Esta acción no se puede deshacer."
    FALLS_NONE = "sin caídas guardadas"
    FALLS_ONE = "1 caída guardada"
    FALLS_MANY = "{n} caídas guardadas"
    CONFIRM_DELETE_ACTION = "Eliminar paciente"
    ADDED_TITLE = "Paciente añadido"
    ADDED = "{name} · nivel de riesgo {level}."
    DELETED_TITLE = "Paciente eliminado"
    DELETED = "Se han eliminado {name} y su historial de caídas."


class Monitor:
    """Dashboards: top bar, session card, video panel and alerts."""
    TAB_MONITORING = "En directo"
    TAB_PATIENTS = "Pacientes"
    TAB_MONITORING_LOCKED = "Añade antes un paciente"
    TAB_PATIENTS_LOCKED = "Detén la monitorización para gestionar pacientes"
    ADMIN_TITLE = "Pruebas de detección"      # the administrators' single page
    SIGN_OUT = "Cerrar sesión"
    SIGN_OUT_SHORTCUT = "Ctrl+Shift+Q"
    ACCOUNT_TIP = "Cuenta"
    ACCOUNT_NAME = "{name}, {role}. Menú de la cuenta"
    ACCOUNT_MENU = "Menú de la cuenta"
    CLOCK_FORMAT = "ddd d MMM · HH:mm"

    CAMERA = "Cámara"
    STRIP_PATIENT = "PACIENTE"
    STRIP_CAMERA = "CÁMARA"
    STRIP_FILE = "ARCHIVO DE VÍDEO"
    STRIP_STATUS = "ESTADO"
    STRIP_DURATION = "DURACIÓN"
    RISK_BADGE = "RIESGO {level}"
    CAMERA_SPEC = "{width} × {height} · {fps} fps"
    CAMERA_SPEC_TIP = "Resolución y fotogramas según el nivel de riesgo {level} del paciente"
    CAMERA_SPEC_DEFAULT_TIP = "Sin paciente: la cámara usa el perfil de riesgo {level}"
    PATIENT_COMBO = "Paciente"
    PATIENT_COMBO_TIP = "Paciente monitorizado. Su nivel de riesgo fija la cámara y el modelo de caídas."
    CAMERA_SPEC_TEST_TIP = "Resolución y fotogramas del perfil de prueba de riesgo {level}"
    FILE_SPEC = "Se analiza a sus propios fps"

    # Administrators (testers): no patient, a test profile instead, and nothing is stored or e-mailed.
    STRIP_TEST_PROFILE = "PERFIL DE PRUEBA"
    TEST_PROFILES: ClassVar[dict[str, str]] = {"LOW": "Riesgo bajo", "MEDIUM": "Riesgo medio", "HIGH": "Riesgo alto"}
    TEST_PROFILE_COMBO = "Perfil de prueba"
    TEST_PROFILE_TIP = "Cámara y modelo de un nivel de riesgo. Se aplica la próxima vez que inicies la cámara."
    TEST_MODE_BADGE = "MODO PRUEBA"
    TEST_MODE_TIP = "Las caídas se muestran y registran aquí, pero no se guardan ni se envía correo."

    STATUS_TEXT: ClassVar[dict[str, str]] = {
        "idle": "Detenido",
        "starting": "Iniciando…",
        "live": "En directo",
        "stopping": "Deteniendo…",
        "error": "Error de la fuente",
        "finished": "Análisis finalizado",
        "alert": "Alerta de caída",
    }

    LIVE_VIDEO = "Vídeo en directo"
    SUBTITLE_IDLE = "Elige una fuente para empezar"
    SUBTITLE_RUNNING = "Analizando {label}"
    SUBTITLE_ERROR = "Fuente no disponible"
    SUBTITLE_FINISHED = "Finalizado · {label}"

    CAMERAS = ("Cámara 0", "Cámara 1", "Cámara 2")
    CAMERA_LABEL = "Cámara {index}"
    SOURCE_COMBO = "Fuente de vídeo"
    ANALYSE_VIDEO = "Analizar vídeo…"
    ANALYSE_VIDEO_TIP = "Analizar un archivo de vídeo (Ctrl+O)"
    FILE_DIALOG_TITLE = "Analizar un archivo de vídeo"
    FILE_DIALOG_FILTER = "Archivos de vídeo (*.mp4 *.avi *.mov *.mkv)"
    START = "Iniciar"
    START_TIP = "Iniciar monitorización (Ctrl+Intro)"
    STOP = "Detener"
    STOP_TIP = "Detener monitorización (Ctrl+Intro)"
    STOPPING = "Deteniendo…"


    PLACEHOLDER: ClassVar[dict[str, tuple[str, str]]] = {
        "idle": ("Monitorización detenida", "Elige una fuente y pulsa Iniciar."),
        "starting": ("Iniciando…", "Abriendo la fuente y cargando los modelos."),
        "error": ("Fuente no disponible", ""),
        "finished": ("Análisis finalizado", "{label} · {duration}"),
    }
    TRY_AGAIN = "Reintentar"
    CAMERA_LOST = "La cámara ha dejado de enviar imagen. Comprueba que está conectada y que no la usa otra aplicación."

    STATUS_ALERT_COUNT = "Alerta de caída ×{n}"
    ACKNOWLEDGE = "Enterado"
    ACKNOWLEDGE_TIP = "Marcar la alerta como atendida (Esc)"
    ALERT_ACKNOWLEDGED = "Alerta marcada como atendida"

    CONFIRM_SIGN_OUT_TITLE = "¿Detener y cerrar sesión?"
    CONFIRM_SIGN_OUT_BODY = "Hay una monitorización en curso. Al cerrar sesión se detienen la cámara y el análisis."
    CONFIRM_SIGN_OUT_ACTION = "Detener y cerrar sesión"


class Log:
    """Event log panel."""
    TITLE = "Registro de eventos"
    COUNT_ONE = "1 evento"
    COUNT_MANY = "{n} eventos"
    COUNT_FILTERED = "{shown} de {total} eventos"
    FILTERS = (("all", "Todos los eventos"), ("alerts", "Alertas"), ("errors", "Errores"), ("info", "Información"))
    FILTER_NAME = "Filtrar eventos"
    MORE = "Más acciones del registro"
    EXPORT = "Exportar CSV…"
    CLEAR = "Vaciar registro…"
    COLUMNS = ("Hora", "Tipo", "Descripción")
    CSV_HEADER = ("hora", "tipo", "descripción")
    EMPTY = "No hay eventos en esta sesión"
    EMPTY_FILTERED = "Ningún evento coincide con el filtro."
    EXPORT_DIALOG_TITLE = "Exportar el registro de eventos"
    EXPORT_FILTER = "Archivos CSV (*.csv)"
    EXPORT_FILE_NAME = "vigia-eventos-{stamp}.csv"
    EXPORT_FAILED = "No se pudo exportar el registro a {name}"
    CONFIRM_CLEAR_TITLE = "¿Vaciar el registro de eventos?"
    CONFIRM_CLEAR_BODY = (
        "Se quitarán {n} eventos de esta vista. Las caídas ya guardadas no se borran."
    )
    CONFIRM_CLEAR_BODY_ONE = (
        "Se quitará 1 evento de esta vista. Las caídas ya guardadas no se borran."
    )
    CONFIRM_CLEAR_ACTION = "Vaciar registro"
    TABLE_NAME = "Eventos"
    # The keys are the event types the code uses; the values are what the log shows.
    KIND_LABELS: ClassVar[dict[str, str]] = {"INFO": "INFO", "ERROR": "ERROR", "ALERT": "ALERTA"}


class Pose:
    """Pose analysis panel (administrators)."""
    TITLE = "Análisis de la pose"
    SUBTITLE = "33 puntos"
    SKELETON = "ESQUELETO"
    NO_SIGNAL = "Sin señal"
    INFERENCE = "Inferencia"
    CONFIDENCE = "Confianza"
    HIP_HEIGHT = "Cadera"
    HIP_HEIGHT_TIP = "Posición vertical normalizada del centro de la cadera (0 = arriba, 1 = abajo)"
    TREND_WINDOW = "Últimos 30 s"
    METRICS_EMPTY = "Inferencia, confianza y altura de la cadera aparecen aquí al monitorizar."


class Toasts:
    """Toasts of the sign-in screen: signed in, account created and signed out."""

    SIGNED_IN_TITLE = "Sesión iniciada"
    SIGNED_IN = "Abriendo tu panel…"
    ACCOUNT_CREATED_TITLE = "Cuenta creada"
    ACCOUNT_CREATED = "Ahora añade a la persona que cuidas."
    SIGNED_OUT_TITLE = "Sesión cerrada"
    SIGNED_OUT = "Tu sesión ha terminado."
    KIND_TITLES: ClassVar[dict[str, str]] = {"success": "Hecho", "error": "Algo ha fallado", "warning": "Atención", "info": "Información"}


class Messages:
    """Errors and event log entries raised by controllers and threads."""
    REQUIRED_FIELDS = "Rellena todos los campos obligatorios."
    BAD_CREDENTIALS = "Correo o contraseña incorrectos. Inténtalo de nuevo."
    INVALID_ROLE = "Elige un rol válido."
    EMAIL_TAKEN = "No se pudo completar el registro: este correo ya está en uso."
    REGISTRATION_FAILED = "No se pudo completar el registro. Inténtalo de nuevo."
    PATIENT_NOT_SAVED = "No se pudo guardar el paciente. Inténtalo de nuevo."
    PATIENT_NOT_DELETED = "No se pudo eliminar el paciente. Inténtalo de nuevo."
    STARTING_CAMERA = "Iniciando la cámara {index}..."
    PROCESSING_FILE = "Procesando el vídeo: {name}"
    TEST_MODE = "Modo prueba · riesgo {level}: las caídas no se guardan ni se envían"
    STREAM_CONNECTED = "Vídeo conectado"
    STREAM_DISCONNECTED = "Vídeo desconectado"
    FALL_DETECTED = "Caída detectada ({probability:.0%})"
    SENDING_EMAIL = "Enviando el correo de aviso..."
    EMAIL_SKIPPED = "Caída guardada; sin correo (ya se envió uno hace menos de un minuto)"
    EMAIL_SENT = "Correo de aviso enviado"
    EMAIL_FAILED = "No se pudo enviar el correo de aviso"
    CAMERA_NOT_OPENED = "No se pudo abrir la cámara {index}"
    FILE_NOT_OPENED = "No se pudo abrir el vídeo {name}"
    MODEL_FAILED = "Detección de caídas no disponible: el modelo no se pudo usar. Monitorización detenida."
    UNEXPECTED_STOP = "La detección se ha detenido por un error inesperado"
    NO_NOTES = "Sin notas"


class Email:
    """Fall alert e-mail: sender, subject and both bodies (`src/notifications/`)."""
    SENDER = "Alertas {app}"
    SUBJECT = "{app}: alerta de caída - {patient}"
    ATTACHMENT_NAME = "caida.jpg"
    PAGE_TITLE = "{app}: caída detectada"
    PREVIEW = "Posible caída de {patient} ({timestamp})."
    BADGE = "Alerta"
    TITLE = "Caída detectada"
    ADVICE = "Se ha detectado una posible caída sin ayuda. Comprueba cómo está el paciente lo antes posible."
    PATIENT = "Paciente"
    DETECTED_AT = "Fecha y hora"
    CONFIDENCE = "Confianza"
    NOTES = "Notas clínicas"
    IMAGE = "Imagen"
    IMAGE_ATTACHED = "adjunta a este correo"
    IMAGE_MISSING = "no disponible"
    ATTACHMENT_TITLE = "Imagen adjunta."
    ATTACHMENT_BODY = "Este mensaje incluye la imagen capturada en el momento de la caída."
    FOOTER = "Mensaje automático de {app}. Solo para los contactos autorizados del paciente."


class Video:
    """Labels drawn on the video. Without accents: OpenCV's fonts cannot draw them."""
    PERSON = "PERSONA"
    FALL = "ALERTA"


def event_count(shown: int, total: int) -> str:
    """Returns the event log's counter text.

    Args:
        shown: Events that pass the filter.
        total: Events in the log.

    Returns:
        "3 eventos", or "2 de 3 eventos" while a filter hides some.
    """
    if shown != total:
        return Log.COUNT_FILTERED.format(shown=shown, total=total)
    return Log.COUNT_ONE if total == 1 else Log.COUNT_MANY.format(n=total)
