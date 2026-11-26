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


PATIENT = Section("patient", "Patient", "Who the patient is and who they live with.")
CONDITION = Section("condition", "General condition", "How the patient's health has been lately.")
ACTIVITIES = Section("activities", "Everyday activities", "How hard each activity is for the patient.")
CONDITIONS = Section("conditions", "Health conditions", "Conditions a doctor has diagnosed in the last 12 months.")
MEDICATION = Section("medication", "Medication", "Medicines taken in the last 2 weeks.")
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


_DIFFICULTY = (("No difficulty", 0), ("Some difficulty", 1), ("A lot of difficulty", 2), ("Cannot do it", 3))

QUESTIONS = (
    # --- The patient ---
    _number("age", "Age (years)", PATIENT, 18, 110),
    _choice("sex_female", "Sex", PATIENT, (("Male", 0), ("Female", 1))),
    _check("lives_with_partner", "Lives with a spouse or partner", PATIENT),

    # --- General condition ---
    _choice("self_rated_health", "General health", CONDITION,
            (("Very good", 0), ("Good", 1), ("Fair", 2), ("Bad", 3), ("Very bad", 4))),
    _choice("activity_limitation", "Limited by a health problem (at least 6 months)", CONDITION,
            (("Not limited", 0), ("Limited, but not severely", 1), ("Severely limited", 2))),
    _choice("pain_level", "Pain in the last 4 weeks", CONDITION,
            (("None", 0), ("Very mild", 1), ("Mild", 2), ("Moderate", 3), ("Severe", 4), ("Extreme", 5))),
    _choice("physical_activity", "Physical activity in free time", CONDITION,
            (("Almost none (sedentary)", 0), ("Occasional", 1), ("Several times a month", 2),
             ("Several times a week", 3))),

    # --- Everyday activities: all answered on the same difficulty scale ---
    _choice("walk_500m_difficulty", "Walking 500 metres without help", ACTIVITIES, _DIFFICULTY),
    _choice("stairs_difficulty", "Going up or down 12 steps", ACTIVITIES, _DIFFICULTY),
    _choice("sit_stand_difficulty", "Sitting down or getting up from a chair or bed", ACTIVITIES, _DIFFICULTY),
    _choice("bathing_difficulty", "Showering or bathing without help", ACTIVITIES, _DIFFICULTY),
    _choice("heavy_chores_difficulty", "Heavy housework (washing windows, scrubbing floors)", ACTIVITIES,
            _DIFFICULTY),
    _choice("concentration_difficulty", "Concentrating", ACTIVITIES, _DIFFICULTY),
    _choice("vision_difficulty", "Seeing (with glasses if used)", ACTIVITIES, _DIFFICULTY),
    _choice("hearing_difficulty", "Hearing in a quiet place", ACTIVITIES, _DIFFICULTY),

    # --- Health conditions ---
    _check("osteoporosis", "Osteoporosis", CONDITIONS),
    _check("arthrosis", "Arthrosis", CONDITIONS),
    _check("chronic_back_pain", "Chronic back or neck pain", CONDITIONS),
    _check("urinary_incontinence", "Urinary incontinence", CONDITIONS),
    _check("diabetes", "Diabetes", CONDITIONS),
    _check("heart_disease", "Heart disease (heart attack, angina...)", CONDITIONS),
    _check("anxiety", "Chronic anxiety", CONDITIONS),
    _check("depression", "Depression", CONDITIONS),
    _check("stroke_ever", "Has ever had a stroke", CONDITIONS),

    # --- Medication ---
    _number("n_prescribed_med_types", "Different medicines prescribed by a doctor", MEDICATION, 0, 23),
    _check("takes_sedatives", "Tranquillisers, relaxants or sleeping pills", MEDICATION),
    _check("takes_antidepressants", "Antidepressants", MEDICATION),
    _check("takes_bp_medication", "Medicines for blood pressure", MEDICATION),
)


def questions_in(section: Section) -> tuple[Question, ...]:
    """Returns the questions of a section, in order.

    Args:
        section: One of `SECTIONS`.

    Returns:
        Its questions.
    """
    return tuple(question for question in QUESTIONS if question.section == section)
