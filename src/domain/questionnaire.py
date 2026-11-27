"""The health questionnaire that is answered about each patient when they are added.

Every question is one input of the risk model (`src/ai/risk_assessor.py`): `key` is the name of the
model's feature and every answer carries the number the model was trained with (see
`training/risk_assessment/build_risk_dataset_esde.py`, where each feature is documented). The questions
are grouped in `SECTIONS`, in the order the new patient form shows them; the form is built from
`QUESTIONS`, so adding or changing a question only means editing this module.
"""

from dataclasses import dataclass

CHOICE, CHECK, NUMBER = "choice", "check", "number"


@dataclass(frozen=True)
class Section:
    """A group of related questions, shown together as one card of the new patient form.

    Attributes:
        key: Identifier of the section.
        title: Its heading.
        description: One line that tells the caregiver what the questions are about.
    """
    key: str
    title: str
    description: str


PATIENT = Section("patient", "Paciente", "Quién es el paciente y con quién vive.")
CONDITION = Section("condition", "Estado general", "Cómo ha estado de salud el paciente últimamente.")
ACTIVITIES = Section("activities", "Actividades diarias", "Cuánto le cuesta al paciente cada actividad.")
CONDITIONS = Section("conditions", "Problemas de salud", "Diagnosticados por un médico en los últimos 12 meses.")
MEDICATION = Section("medication", "Medicación", "Medicamentos tomados en las últimas 2 semanas.")
SECTIONS = (PATIENT, CONDITION, ACTIVITIES, CONDITIONS, MEDICATION)


@dataclass(frozen=True)
class Question:
    """One question of the health questionnaire, and one input of the risk model.

    Attributes:
        key: Name of the model feature.
        text: What the caregiver reads.
        section: Section of the form where it is shown.
        kind: CHOICE (one of the options), CHECK (yes / no box) or NUMBER.
        options: CHOICE only: (label, value the model uses) pairs.
        minimum: NUMBER only: smallest accepted value.
        maximum: NUMBER only: largest accepted value.
    """
    key: str
    text: str
    section: Section
    kind: str
    options: tuple[tuple[str, float], ...] = ()
    minimum: int = 0
    maximum: int = 0

    @property
    def required(self) -> bool:
        """True when it must be answered: a CHECK left empty is already an answer ("no")."""
        return self.kind != CHECK


def _choice(key, text, section, options):
    return Question(key, text, section, CHOICE, options=tuple(options))


def _check(key, text, section):
    return Question(key, text, section, CHECK)


def _number(key, text, section, minimum, maximum):
    return Question(key, text, section, NUMBER, minimum=minimum, maximum=maximum)


_DIFFICULTY = (("Ninguna dificultad", 0), ("Alguna dificultad", 1), ("Mucha dificultad", 2), ("No puede hacerlo", 3))

QUESTIONS = (
    # --- The patient ---
    _number("age", "Edad (años)", PATIENT, 18, 110),
    _choice("sex_female", "Sexo", PATIENT, (("Hombre", 0), ("Mujer", 1))),
    _check("lives_with_partner", "Vive con su cónyuge o pareja", PATIENT),

    # --- General condition ---
    _choice("self_rated_health", "Estado de salud general", CONDITION,
            (("Muy bueno", 0), ("Bueno", 1), ("Regular", 2), ("Malo", 3), ("Muy malo", 4))),
    _choice("activity_limitation", "Limitado por un problema de salud (al menos 6 meses)", CONDITION,
            (("Nada limitado", 0), ("Limitado, pero no gravemente", 1), ("Gravemente limitado", 2))),
    _choice("pain_level", "Dolor en las últimas 4 semanas", CONDITION,
            (("Ninguno", 0), ("Muy leve", 1), ("Leve", 2), ("Moderado", 3), ("Severo", 4), ("Extremo", 5))),
    _choice("physical_activity", "Actividad física en el tiempo libre", CONDITION,
            (("Casi ninguna (sedentario)", 0), ("Ocasional", 1), ("Varias veces al mes", 2),
             ("Varias veces a la semana", 3))),

    # --- Everyday activities: all answered on the same difficulty scale ---
    _choice("walk_500m_difficulty", "Caminar 500 metros en llano sin ayuda", ACTIVITIES, _DIFFICULTY),
    _choice("stairs_difficulty", "Subir o bajar 12 escalones", ACTIVITIES, _DIFFICULTY),
    _choice("sit_stand_difficulty", "Sentarse o levantarse de una silla o cama", ACTIVITIES, _DIFFICULTY),
    _choice("bathing_difficulty", "Ducharse o bañarse sin ayuda", ACTIVITIES, _DIFFICULTY),
    _choice("heavy_chores_difficulty", "Tareas domésticas pesadas (cristales, fregar suelos)", ACTIVITIES,
            _DIFFICULTY),
    _choice("concentration_difficulty", "Recordar o concentrarse", ACTIVITIES, _DIFFICULTY),
    _choice("vision_difficulty", "Ver (con gafas si las usa)", ACTIVITIES, _DIFFICULTY),
    _choice("hearing_difficulty", "Oír una conversación en un sitio tranquilo", ACTIVITIES, _DIFFICULTY),

    # --- Health conditions ---
    _check("osteoporosis", "Osteoporosis", CONDITIONS),
    _check("arthrosis", "Artrosis", CONDITIONS),
    _check("chronic_back_pain", "Dolor crónico de espalda o cuello", CONDITIONS),
    _check("urinary_incontinence", "Incontinencia urinaria", CONDITIONS),
    _check("diabetes", "Diabetes", CONDITIONS),
    _check("heart_disease", "Enfermedad del corazón (infarto, angina...)", CONDITIONS),
    _check("anxiety", "Ansiedad crónica", CONDITIONS),
    _check("depression", "Depresión", CONDITIONS),
    _check("stroke_ever", "Ha sufrido alguna vez un ictus", CONDITIONS),

    # --- Medication ---
    _number("n_prescribed_med_types", "Medicamentos distintos recetados por un médico", MEDICATION, 0, 23),
    _check("takes_sedatives", "Tranquilizantes, relajantes o pastillas para dormir", MEDICATION),
    _check("takes_antidepressants", "Antidepresivos", MEDICATION),
    _check("takes_bp_medication", "Medicinas para la tensión arterial", MEDICATION),
)


def questions_in(section: Section) -> tuple[Question, ...]:
    """Returns the questions of a section, in order.

    Args:
        section: One of `SECTIONS`.

    Returns:
        Its questions.
    """
    return tuple(question for question in QUESTIONS if question.section == section)
