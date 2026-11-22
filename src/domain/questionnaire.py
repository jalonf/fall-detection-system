"""The health questionnaire that is answered about the patient when signing up.

Every question is one input of the risk model (`src/ai/risk_assessor.py`): `key` is the name of the
model's feature and every answer carries the number the model was trained with (see
`training/risk_assessment/build_risk_dataset_esde.py`, where each feature is documented). The sign-up
form is built from `QUESTIONS`, so adding or changing a question only means editing this list.
"""

from dataclasses import dataclass

# Steps of the sign-up form that show questions.
PROFILE, DAILY_LIFE, HEALTH = "profile", "daily_life", "health"

CHOICE, CHECK, NUMBER = "choice", "check", "number"

_DIFFICULTY = (("No difficulty", 0), ("Some difficulty", 1), ("A lot of difficulty", 2), ("Cannot do it", 3))
_SEEING = (("No difficulty", 0), ("Some difficulty", 1), ("A lot of difficulty", 2), ("Cannot see at all", 3))
_HEARING = (("No difficulty", 0), ("Some difficulty", 1), ("A lot of difficulty", 2), ("Cannot hear at all", 3))


@dataclass(frozen=True)
class Question:
    """One question of the health questionnaire, and one input of the risk model.

    Attributes:
        key: Name of the model feature.
        text: What the caregiver reads.
        step: Step of the sign-up form where it is shown.
        kind: CHOICE (one of the options), CHECK (yes / no box) or NUMBER.
        options: CHOICE only: (label, value the model uses) pairs.
        minimum: NUMBER only: smallest accepted value.
        maximum: NUMBER only: largest accepted value.
        section: Heading shown above the first question of a group.
    """
    key: str                                      # name of the model feature
    text: str                                     # what the caregiver reads
    step: str                                     # step of the form where it is shown
    kind: str                                     # CHOICE (one of the options), CHECK (yes / no box) or NUMBER
    options: tuple[tuple[str, float], ...] = ()   # CHOICE: (label, value the model uses)
    minimum: int = 0                              # NUMBER: smallest accepted value
    maximum: int = 0                              # NUMBER: largest accepted value
    section: str = ""                             # heading shown above the first question of a group


def _choice(key, text, step, options, section=""):
    return Question(key, text, step, CHOICE, options=tuple(options), section=section)


def _check(key, text, step, section=""):
    return Question(key, text, step, CHECK, section=section)


def _number(key, text, step, minimum, maximum, section=""):
    return Question(key, text, step, NUMBER, minimum=minimum, maximum=maximum, section=section)


QUESTIONS = (
    # --- The patient ---
    _number("age", "Age (years)", PROFILE, 18, 110),
    _choice("sex_female", "Sex", PROFILE, (("Male", 0), ("Female", 1))),
    _check("lives_with_partner", "Lives with a spouse or partner", PROFILE),

    # --- Daily life ---
    _choice("self_rated_health", "General health", DAILY_LIFE,
            (("Very good", 0), ("Good", 1), ("Fair", 2), ("Bad", 3), ("Very bad", 4)),
            section="General condition"),
    _choice("activity_limitation", "Limited by a health problem (at least 6 months)", DAILY_LIFE,
            (("Not limited", 0), ("Limited, but not severely", 1), ("Severely limited", 2))),
    _choice("pain_level", "Pain in the last 4 weeks", DAILY_LIFE,
            (("None", 0), ("Very mild", 1), ("Mild", 2), ("Moderate", 3), ("Severe", 4), ("Extreme", 5))),
    _choice("physical_activity", "Physical activity in free time", DAILY_LIFE,
            (("Almost none (sedentary)", 0), ("Occasional", 1), ("Several times a month", 2),
             ("Several times a week", 3))),
    _choice("walk_500m_difficulty", "Walking 500 metres without help", DAILY_LIFE, _DIFFICULTY,
            section="Difficulty with everyday activities"),
    _choice("stairs_difficulty", "Going up or down 12 steps", DAILY_LIFE, _DIFFICULTY),
    _choice("sit_stand_difficulty", "Sitting down or getting up from a chair or bed", DAILY_LIFE, _DIFFICULTY),
    _choice("bathing_difficulty", "Showering or bathing without help", DAILY_LIFE, _DIFFICULTY),
    _choice("heavy_chores_difficulty", "Heavy housework (washing windows, scrubbing floors)", DAILY_LIFE,
            _DIFFICULTY),
    _choice("concentration_difficulty", "Concentrating", DAILY_LIFE, _DIFFICULTY),
    _choice("vision_difficulty", "Seeing (with glasses if used)", DAILY_LIFE, _SEEING),
    _choice("hearing_difficulty", "Hearing in a quiet place", DAILY_LIFE, _HEARING),

    # --- Health ---
    _check("osteoporosis", "Osteoporosis", HEALTH, section="Conditions in the last 12 months"),
    _check("arthrosis", "Arthrosis", HEALTH),
    _check("chronic_back_pain", "Chronic back or neck pain", HEALTH),
    _check("urinary_incontinence", "Urinary incontinence", HEALTH),
    _check("diabetes", "Diabetes", HEALTH),
    _check("heart_disease", "Heart disease (heart attack, angina...)", HEALTH),
    _check("anxiety", "Chronic anxiety", HEALTH),
    _check("depression", "Depression", HEALTH),
    _check("stroke_ever", "Has ever had a stroke", HEALTH),
    _number("n_prescribed_med_types", "Different medicines prescribed by a doctor", HEALTH, 0, 23,
            section="Medication in the last 2 weeks"),
    _check("takes_sedatives", "Takes tranquillisers, relaxants or sleeping pills", HEALTH),
    _check("takes_antidepressants", "Takes antidepressants", HEALTH),
    _check("takes_bp_medication", "Takes medicines for blood pressure", HEALTH),
)
