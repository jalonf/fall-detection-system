"""Builds the risk-assessment dataset from the ESdE 2025 health survey (INE).

It keeps the respondents aged 65+, computes the predictors the application asks in its
questionnaire and the targets (accidents at home or during leisure time), and writes the CSV
with its dictionary to `data/risk_assessment/processed/`.

    python -m training.risk_assessment.build_risk_dataset_esde
"""

import io
import logging
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.paths import ESDE_ZIP, RISK_PROCESSED_DIR

# Configure clean logging format
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

TAB_FILE = "ESdEadulto_2025.tab"   # microdata file inside the INE zip
MIN_AGE = 65
NO_ANSWER = 9                      # INE code for "No contesta" in the single-digit variables


# --------------------------------------------------------------------------------------------------
# Recoding helpers. The INE codes are 1 = yes / 2 = no, or 1..4 for "how much difficulty".
# Each helper returns NaN for "no answer", which is handled later (see `fill_missing`).
# --------------------------------------------------------------------------------------------------
def yes_no(answers: pd.Series) -> pd.Series:
    """1 = yes, 2 = no -> 1 / 0."""
    return answers.map({1: 1.0, 2: 0.0})


def difficulty(answers: pd.Series) -> pd.Series:
    """1 none, 2 some, 3 a lot, 4 cannot do it at all -> 0 / 1 / 2 / 3."""
    return answers.map({1: 0.0, 2: 1.0, 3: 2.0, 4: 3.0})


def condition(df: pd.DataFrame, number: int) -> pd.Series:
    """Whether the person suffered disease `number` of block C5 in the last 12 months (1 / 0).

    C5b ("last 12 months") is only asked when C5a ("ever") is yes, so a "no" in C5a means 0.
    """
    last_year, ever = df[f"C5b_{number}"], df[f"C5a_{number}"]
    result = yes_no(last_year)
    result[(ever == 2) & result.isna()] = 0.0
    return result


def any_of(*answers: pd.Series) -> pd.Series:
    """1 if any of the answers is 1, 0 if all are 0, otherwise unknown (NaN)."""
    table = pd.concat(answers, axis=1)
    result = pd.Series(np.nan, index=table.index)
    result[(table == 0).all(axis=1)] = 0.0
    result[(table == 1).any(axis=1)] = 1.0
    return result


def takes_medicine(answers: pd.Series) -> pd.Series:
    """Medicines of the last two weeks (K3_*a). The question is left blank when the person took none -> 0."""
    return yes_no(answers).where(answers.notna(), 0.0)


def prescribed_medicine_types(df: pd.DataFrame) -> pd.Series:
    """Number of the 23 medicine types (K3_1b..K3_23b) that a doctor prescribed in the last two weeks."""
    prescribed = pd.concat([df[f"K3_{i}b"] == 1 for i in range(1, 24)], axis=1)
    return prescribed.sum(axis=1).astype(float)


# --------------------------------------------------------------------------------------------------
# The predictors: one row per question of the application's questionnaire.
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Feature:
    """One column of the dataset and how it is computed from the survey.

    Attributes:
        name: Column of the CSV.
        source: ESdE variable(s) it is computed from.
        description: What is asked.
        coding: Meaning of the values.
    """
    name: str                              # column of the CSV
    source: str                            # ESdE variable(s) it is computed from
    description: str                       # what is asked
    coding: str                            # meaning of the values
    fall_relation: str                     # why it is related to falls
    build: Callable[[pd.DataFrame], pd.Series]   # computes the column from the raw ESdE table


FEATURES = [
    # --- Profile ---
    Feature("age", "EDADa", "Edad en años", "65-102",
            "El riesgo de caída aumenta con la edad (fragilidad, pérdida de masa muscular y de equilibrio)",
            lambda df: df["EDADa"].astype(float)),
    Feature("sex_female", "SEXOa", "Sexo", "0 hombre, 1 mujer",
            "Las mujeres caen más y se fracturan más (osteoporosis)",
            lambda df: (df["SEXOa"] == 2).astype(float)),
    Feature("lives_with_partner", "A4", "Convive en pareja (cónyuge o pareja de hecho)", "0 no, 1 sí",
            "Vivir solo se asocia a más caídas y a peor respuesta tras caer",
            lambda df: df["A4"].map({1: 1.0, 2: 1.0, 3: 0.0})),

    # --- General health and pain ---
    Feature("self_rated_health", "C1", "Salud percibida en los últimos 12 meses", "0 muy buena .. 4 muy mala",
            "La mala salud percibida resume fragilidad y comorbilidad",
            lambda df: (df["C1"] - 1).astype(float)),
    Feature("activity_limitation", "C3a1", "Limitación por un problema de salud", "0 nada, 1 limitado, 2 gravemente",
            "Las limitaciones por problemas de salud reducen la movilidad y la reserva funcional",
            lambda df: df["C3a1"].map({3: 0.0, 2: 1.0, 1: 2.0})),
    Feature("pain_level", "G9", "Dolor padecido en las últimas 4 semanas", "0 ninguno .. 5 extremo",
            "El dolor crónico altera la marcha y el equilibrio",
            lambda df: df["G9"].where(df["G9"] != NO_ANSWER) - 1),

    # --- Mobility and strength (difficulty doing it without help) ---
    Feature("walk_500m_difficulty", "F6", "Dificultad para caminar 500 m sin ayuda", "0 ninguna .. 3 no puede",
            "La dificultad para caminar es uno de los predictores más fuertes de caída",
            lambda df: difficulty(df["F6"])),
    Feature("stairs_difficulty", "F7", "Dificultad para subir o bajar 12 escalones", "0 ninguna .. 3 no puede",
            "Las escaleras son una causa frecuente de caída y reflejan la fuerza de las piernas",
            lambda df: difficulty(df["F7"])),
    Feature("sit_stand_difficulty", "G1_2", "Dificultad para sentarse o levantarse de una silla o cama",
            "0 ninguna .. 3 no puede",
            "Levantarse de una silla mide la fuerza de las piernas (prueba clásica de riesgo)",
            lambda df: difficulty(df["G1_2"])),
    Feature("bathing_difficulty", "G1_5", "Dificultad para ducharse o bañarse sin ayuda", "0 ninguna .. 3 no puede",
            "El baño es un lugar de alto riesgo y esta limitación indica fragilidad",
            lambda df: difficulty(df["G1_5"])),
    Feature("heavy_chores_difficulty", "G4_6", "Dificultad para las tareas domésticas de mucho esfuerzo",
            "0 ninguna .. 3 no puede",
            "Las tareas de esfuerzo miden la reserva física y la fragilidad",
            lambda df: difficulty(df["G4_6"])),

    # --- Cognition and senses ---
    Feature("concentration_difficulty", "F8", "Dificultad para concentrarse", "0 ninguna .. 3 no puede",
            "El deterioro cognitivo y de la atención aumenta las caídas",
            lambda df: difficulty(df["F8"])),
    Feature("vision_difficulty", "F2", "Dificultad para ver (con gafas si las usa)", "0 ninguna .. 3 no ve",
            "La mala visión impide detectar obstáculos",
            lambda df: difficulty(df["F2"])),
    Feature("hearing_difficulty", "F4", "Dificultad para oír en un sitio tranquilo", "0 ninguna .. 3 no oye",
            "La pérdida auditiva se asocia a más caídas (equilibrio y atención al entorno)",
            lambda df: difficulty(df["F4"])),

    # --- Medication (last two weeks) ---
    Feature("n_prescribed_med_types", "K3_1b .. K3_23b", "Número de tipos de medicamento recetados", "0-23",
            "La polifarmacia es un factor de riesgo reconocido",
            prescribed_medicine_types),
    Feature("takes_sedatives", "K3_7a", "Toma tranquilizantes, relajantes o pastillas para dormir", "0 no, 1 sí",
            "Los sedantes e hipnóticos aumentan el riesgo (somnolencia, equilibrio)",
            lambda df: takes_medicine(df["K3_7a"])),
    Feature("takes_antidepressants", "K3_14a", "Toma antidepresivos o estimulantes", "0 no, 1 sí",
            "Los antidepresivos se asocian a más caídas",
            lambda df: takes_medicine(df["K3_14a"])),
    Feature("takes_bp_medication", "K3_12a", "Toma medicinas para la tensión arterial", "0 no, 1 sí",
            "Los antihipertensivos pueden causar hipotensión y mareo",
            lambda df: takes_medicine(df["K3_12a"])),

    # --- Diseases suffered in the last 12 months (stroke: ever) ---
    Feature("osteoporosis", "C5b_28", "Osteoporosis", "0 no, 1 sí",
            "Aumenta la probabilidad de fractura al caer",
            lambda df: condition(df, 28)),
    Feature("arthrosis", "C5b_6", "Artrosis", "0 no, 1 sí",
            "Afecta a las articulaciones de carga, a la marcha y a la fuerza",
            lambda df: condition(df, 6)),
    Feature("chronic_back_pain", "C5b_7, C5b_8", "Dolor de espalda crónico (cervical o lumbar)", "0 no, 1 sí",
            "El dolor de espalda limita la movilidad y la postura",
            lambda df: any_of(condition(df, 7), condition(df, 8))),
    Feature("urinary_incontinence", "C5b_14", "Incontinencia urinaria", "0 no, 1 sí",
            "La urgencia miccional provoca prisas y caídas, sobre todo de noche",
            lambda df: condition(df, 14)),
    Feature("stroke_ever", "C5a_24", "Ictus alguna vez (embolia, infarto o hemorragia cerebral)", "0 no, 1 sí",
            "Las secuelas de un ictus alteran el equilibrio y la fuerza",
            lambda df: yes_no(df["C5a_24"])),
    Feature("diabetes", "C5b_12", "Diabetes", "0 no, 1 sí",
            "Neuropatía, problemas visuales e hipoglucemias",
            lambda df: condition(df, 12)),
    Feature("anxiety", "C5b_22", "Ansiedad crónica", "0 no, 1 sí",
            "La ansiedad y el miedo a caer se asocian a más caídas y se tratan con psicofármacos",
            lambda df: condition(df, 22)),
    Feature("depression", "C5b_21", "Depresión", "0 no, 1 sí",
            "Se asocia a más caídas, directamente y por la medicación",
            lambda df: condition(df, 21)),
    Feature("heart_disease", "C5b_2, C5b_3, C5b_4", "Infarto, angina u otra enfermedad del corazón", "0 no, 1 sí",
            "Arritmias, síncope y baja tolerancia al esfuerzo",
            lambda df: any_of(condition(df, 2), condition(df, 3), condition(df, 4))),

    # --- Lifestyle ---
    Feature("physical_activity", "O2", "Frecuencia de actividad física en el tiempo libre",
            "0 sedentario .. 3 entrena varias veces por semana",
            "El sedentarismo debilita músculos y equilibrio; el ejercicio es preventivo",
            lambda df: df["O2"].map({1: 0.0, 2: 1.0, 3: 2.0, 4: 3.0})),
]

PREDICTOR_COLUMNS = [feature.name for feature in FEATURES]


# --------------------------------------------------------------------------------------------------
# The targets: what the model has to predict.
# --------------------------------------------------------------------------------------------------
TARGETS = [
    ("y_accident", "D1_2, D1_3",
     "Accidente en casa o en tiempo libre en los últimos 12 meses (proxy de caída)", "0 no, 1 sí"),
    ("y_accident_home", "D1_2",
     "TARGET USADO: accidente en casa en los últimos 12 meses (el proxy más cercano a una caída en el hogar)",
     "0 no, 1 sí"),
    ("y_injurious_accident", "D1_2, D1_3, D2",
     "Accidente en casa o tiempo libre que requirió hospital o urgencias", "0 no, 1 sí"),
    ("y_injury_sequelae", "C5b_33", "Lesión o defecto permanente causado por un accidente", "0 no, 1 sí"),
    ("y_risk_score", "y_accident + y_injurious_accident + y_injury_sequelae",
     "Puntuación compuesta: suma de las tres señales anteriores", "0-3"),
    ("y_risk_level", "y_risk_score", "Nivel de riesgo: 0 bajo (puntuación 0), 1 medio (1), 2 alto (2 o más)",
     "0 bajo, 1 medio, 2 alto"),
    ("y_any_event", "y_risk_score", "Ha tenido algún evento (puntuación 1 o más)", "0 no, 1 sí"),
]
TARGET_COLUMNS = [name for name, *_ in TARGETS]

WEIGHT_COLUMN = "sample_weight"   # FACTORADULTO: how many people of the population each respondent represents


def build_targets(df: pd.DataFrame) -> pd.DataFrame:
    """The fall-related outcomes that the ESdE does contain (it has no direct fall question)."""
    home, leisure = yes_no(df["D1_2"]), yes_no(df["D1_3"])
    needed_care = df["D2"].isin([1, 2]).astype(float)   # D2: the accident needed hospital or emergency care

    targets = pd.DataFrame(index=df.index)
    targets["y_accident"] = any_of(home, leisure)
    targets["y_accident_home"] = home
    targets["y_injurious_accident"] = (targets["y_accident"] * needed_care).where(targets["y_accident"].notna())
    targets["y_injury_sequelae"] = condition(df, 33)
    targets["y_risk_score"] = targets["y_accident"] + targets["y_injurious_accident"] + targets["y_injury_sequelae"]
    targets["y_risk_level"] = targets["y_risk_score"].map({0.0: 0.0, 1.0: 1.0, 2.0: 2.0, 3.0: 2.0})
    targets["y_any_event"] = (targets["y_risk_score"] >= 1).astype(float).where(targets["y_risk_score"].notna())
    return targets


# --------------------------------------------------------------------------------------------------
# Dataset construction
# --------------------------------------------------------------------------------------------------
def load_adults(path: Path) -> pd.DataFrame:
    """Reads the INE microdata (the zip or the extracted .tab) and keeps the people aged `MIN_AGE`+."""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            member = next(name for name in archive.namelist() if name.endswith(TAB_FILE))
            source = io.BytesIO(archive.read(member))
    else:
        source = path
    everyone = pd.read_csv(source, sep="\t", encoding="latin-1", low_memory=False)
    adults = everyone[everyone["EDADa"] >= MIN_AGE].reset_index(drop=True)
    logger.info("Respondents: %d, aged %d or more: %d", len(everyone), MIN_AGE, len(adults))
    return adults


def build_predictors(df: pd.DataFrame) -> pd.DataFrame:
    """Computes every predictor column from the survey answers.

    Args:
        df: Survey rows (one per respondent).

    Returns:
        One column per feature of `FEATURES`.
    """
    return pd.DataFrame({feature.name: feature.build(df) for feature in FEATURES})


def fill_missing(data: pd.DataFrame, how: str) -> pd.DataFrame:
    """Handles the predictors that the person did not answer (NaN).

    impute: replace with the median of the column (keeps binary and ordinal columns on valid values);
    drop:   remove the rows that have any missing predictor;
    keep:   leave the NaN (for models that accept them).
    """
    incomplete = data[PREDICTOR_COLUMNS].isna().any(axis=1)
    logger.info("Rows with some missing predictor: %d (%.1f%%)", incomplete.sum(), 100 * incomplete.mean())
    for column, count in data[PREDICTOR_COLUMNS].isna().sum().sort_values(ascending=False).head(5).items():
        logger.info("  most missing: %-24s %d", column, count)

    if how == "drop":
        data = data[~incomplete].copy()
    elif how == "impute":
        data[PREDICTOR_COLUMNS] = data[PREDICTOR_COLUMNS].fillna(data[PREDICTOR_COLUMNS].median())
    return data


def build_dataset(adults: pd.DataFrame, missing: str) -> pd.DataFrame:
    """Builds the final dataset: id, predictors, targets and survey weight.

    Args:
        adults: Respondents aged 65+.
        missing: How missing answers are filled (see `fill_missing`).

    Returns:
        The dataset written to the CSV.
    """
    data = pd.concat([build_predictors(adults), build_targets(adults)], axis=1)
    data.insert(0, "person_id", np.arange(1, len(data) + 1))   # position among the respondents aged 65+
    data[WEIGHT_COLUMN] = adults["FACTORADULTO"].astype(float).round(3)

    data = data[data[TARGET_COLUMNS].notna().all(axis=1)]       # a row without a known target is useless
    data = fill_missing(data, missing)

    if missing != "keep":   # no NaN left: store the values as whole numbers
        values = PREDICTOR_COLUMNS + TARGET_COLUMNS
        data[values] = data[values].astype(int)
    return data


def build_dictionary() -> pd.DataFrame:
    """One row per column of the CSV: where it comes from, what it means and why it matters for falls."""
    rows = [("person_id", "id", "-", "Identificador de la persona (posición entre los mayores de 65)", "1..N", "")]
    rows += [(f.name, "predictor", f.source, f.description, f.coding, f.fall_relation) for f in FEATURES]
    rows += [(name, "target", source, description, coding, "") for name, source, description, coding in TARGETS]
    rows.append((WEIGHT_COLUMN, "weight", "FACTORADULTO",
                 "Factor de elevación de la encuesta (opcional como sample_weight al entrenar)", ">0", ""))
    return pd.DataFrame(rows, columns=["column", "role", "esde_variable", "description", "coding", "fall_relation"])


def process_dataset(dataset_root: str, output_dir: str, missing: str = "impute") -> None:
    """Reads the ESdE microdata and writes the risk dataset and its dictionary as CSV files."""
    dataset_path = Path(dataset_root)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if not dataset_path.exists():
        logger.error("Dataset path '%s' not found. Download ESdEadulto_2025.zip from the INE and place it there.", dataset_root)
        return

    dataset = build_dataset(load_adults(dataset_path), missing)

    data_path = out_path / "risk_dataset_esde2025.csv"
    dictionary_path = out_path / "risk_dataset_esde2025_dictionary.csv"
    dataset.to_csv(data_path, index=False)
    build_dictionary().to_csv(dictionary_path, index=False, encoding="utf-8-sig")   # BOM so Excel reads the accents

    logger.info("Saved %d samples to '%s'.", len(dataset), data_path)
    logger.info("Saved the column dictionary to '%s'.", dictionary_path)
    for target in TARGET_COLUMNS:
        logger.info("Target %-22s %s", target, dataset[target].value_counts().sort_index().to_dict())


if __name__ == "__main__":
    DATASET_ROOT = str(ESDE_ZIP)
    OUTPUT_DIR = str(RISK_PROCESSED_DIR)

    logger.info("Starting Risk Dataset Preprocessing")

    # Unanswered predictors: "impute" (median), "drop" (remove the rows) or "keep" (leave NaN)
    process_dataset(dataset_root=DATASET_ROOT, output_dir=OUTPUT_DIR, missing="impute")

    logger.info("Preprocessing Completed")
