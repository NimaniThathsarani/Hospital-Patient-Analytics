"""
Reusable data-loading utilities for the Doctor Performance Dashboard.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLEANED_DATA_PATH = ROOT_DIR / "data" / "cleaned" / "cleaned_dataset.csv"
PROCESSED_DATA_PATH = ROOT_DIR / "data" / \
    "processed" / "doctor_performance_dataset.csv"

DASHBOARD_SOURCE_COLUMNS = [
    "encounter_id",
    "patient_nbr",
    "doctor_id",
    "department",
    "admission_date",
    "length_of_stay",
    "readmitted",
    "patient_satisfaction",
    "gender",
    "age",
    "diag_1",
    "bed_occupancy"
]
DATE_COLUMNS = ["admission_date"]
NUMERIC_COLUMNS = [
    "length_of_stay",
    "patient_satisfaction",
    "bed_occupancy"
]
ID_COLUMNS = [
    "encounter_id",
    "patient_nbr",
    "doctor_id"
]
READMISSION_POSITIVE_VALUE = "<30"


def _coerce_dashboard_dtypes(data: pd.DataFrame) -> pd.DataFrame:
    """
    Apply consistent dtypes to the columns the dashboard relies on.
    """
    working_data = data.copy()

    for date_column in DATE_COLUMNS:
        if date_column in working_data.columns:
            working_data[date_column] = pd.to_datetime(
                working_data[date_column],
                errors="coerce",
            )

    for numeric_column in NUMERIC_COLUMNS:
        if numeric_column in working_data.columns:
            working_data[numeric_column] = pd.to_numeric(
                working_data[numeric_column],
                errors="coerce",
            )

    for id_column in ID_COLUMNS:
        if id_column in working_data.columns:
            working_data[id_column] = working_data[id_column].astype(str)

    if "department" in working_data.columns:
        working_data["department"] = (
            working_data["department"].astype(str).str.strip()
        )

    return working_data


def load_cleaned_dataset(path: Path | str | None = None) -> pd.DataFrame:
    """
    Load the cleaned dataset for the dashboard.
    """
    selected_path = Path(path) if path is not None else CLEANED_DATA_PATH

    if not selected_path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at: {selected_path}"
        )

    data = pd.read_csv(selected_path, low_memory=False)

    return _coerce_dashboard_dtypes(data)


def load_processed_doctor_dataset(path: Path | str | None = None) -> pd.DataFrame:
    """
    Load the processed doctor-performance dataset for the dashboard.
    """
    selected_path = Path(path) if path is not None else PROCESSED_DATA_PATH

    if not selected_path.exists():
        raise FileNotFoundError(
            f"Processed doctor-performance dataset not found at: "
            f"{selected_path}\n"
            "Run scripts/prepare_doctor_dashboard_data.py to create it."
        )

    data = pd.read_csv(selected_path, low_memory=False)

    return _coerce_dashboard_dtypes(data)


def load_dashboard_dataset() -> tuple[pd.DataFrame, str]:
    """
    Load the best available dataset for the dashboard.
    """
    if PROCESSED_DATA_PATH.exists():
        return load_processed_doctor_dataset(), "processed"

    if CLEANED_DATA_PATH.exists():
        return load_cleaned_dataset(), "cleaned_fallback"

    raise FileNotFoundError(
        "No dashboard dataset was found. Expected either:\n"
        f"- {PROCESSED_DATA_PATH}\n"
        f"- {CLEANED_DATA_PATH}"
    )


def validate_required_columns(data: pd.DataFrame, required_columns: set[str]) -> list[str]:
    """
    Validate that all required columns are present in the DataFrame.
    """
    return sorted(required_columns.difference(data.columns))
