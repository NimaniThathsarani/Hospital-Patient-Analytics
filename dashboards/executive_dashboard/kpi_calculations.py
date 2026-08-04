"""
Reusable KPI and summary functions for the Doctor performance dashboard.
"""

from __future__ import annotations
import pandas as pd

READMISSION_POSITIVE_VALUE = "<30"

# Helper functions


def _with_readmission_flag(data: pd.DataFrame) -> pd.DataFrame:
    """
    Add a boolean ``is_30_day_readmission`` column to a copy of the data.
    """
    working_data = data.copy()

    working_data["is_30_day_readmission"] = (
        working_data["readmitted"]
        .astype(str)
        .str.strip()
        .eq(READMISSION_POSITIVE_VALUE)
    )

    return working_data


def _safe_round(value: float, decimals: int = 2) -> float:
    """Round a value, returning 0.0 for NaN/None instead of raising."""
    if value is None or pd.isna(value):
        return 0.0

    return round(float(value), decimals)


# Single-value KPI functions

def total_doctors(data: pd.DataFrame) -> int:
    """Return the number of unique doctors in the dataset."""
    if data.empty or "doctor_id" not in data.columns:
        return 0

    return int(data["doctor_id"].nunique())


def unique_patients_treated(data: pd.DataFrame) -> int:
    """Return the number of unique patients treated."""
    if data.empty or "patient_nbr" not in data.columns:
        return 0

    return int(data["patient_nbr"].nunique())


def total_encounters(data: pd.DataFrame) -> int:
    """Return the total number of unique encounters."""
    if data.empty or "encounter_id" not in data.columns:
        return 0

    return int(data["encounter_id"].nunique())


def average_length_of_stay(data: pd.DataFrame) -> float:
    """Return the average length of stay, in days."""
    if data.empty or "length_of_stay" not in data.columns:
        return 0.0

    length_of_stay = pd.to_numeric(
        data["length_of_stay"], errors="coerce"
    )

    return _safe_round(length_of_stay.mean())


def readmission_rate(data: pd.DataFrame) -> float:
    """Return the 30-day readmission rate, as a percentage (0-100)."""
    if data.empty or "readmitted" not in data.columns:
        return 0.0

    flagged_data = _with_readmission_flag(data)

    return _safe_round(
        flagged_data["is_30_day_readmission"].mean() * 100
    )


def average_patient_satisfaction(data: pd.DataFrame) -> float:
    """Return the average patient-satisfaction score."""
    if data.empty or "patient_satisfaction" not in data.columns:
        return 0.0

    satisfaction = pd.to_numeric(
        data["patient_satisfaction"], errors="coerce"
    )

    return _safe_round(satisfaction.mean())


def patients_per_doctor(data: pd.DataFrame) -> float:
    """Return the average number of unique patients per doctor."""
    doctor_count = total_doctors(data)

    if doctor_count == 0:
        return 0.0

    return _safe_round(unique_patients_treated(data) / doctor_count)


def calculate_overview_kpis(data: pd.DataFrame) -> dict[str, float | int]:
    """
    Calculate the full set of hospital-level KPIs in one call.
    """
    if data.empty:
        return {}

    return {
        "total_doctors": total_doctors(data),
        "unique_patients": unique_patients_treated(data),
        "total_encounters": total_encounters(data),
        "average_length_of_stay": average_length_of_stay(data),
        "readmission_rate": readmission_rate(data),
        "average_satisfaction": average_patient_satisfaction(data),
        "patients_per_doctor": patients_per_doctor(data),
    }


# Summary functions

def create_doctor_level_summary(data: pd.DataFrame) -> pd.DataFrame:
    """
    Create one performance-summary row for each doctor.
    """
    if data.empty:
        return pd.DataFrame()

    working_data = _with_readmission_flag(data)

    working_data["length_of_stay"] = pd.to_numeric(
        working_data["length_of_stay"], errors="coerce"
    )

    working_data["patient_satisfaction"] = pd.to_numeric(
        working_data["patient_satisfaction"], errors="coerce"
    )

    aggregation = {
        "unique_patients": ("patient_nbr", "nunique"),
        "total_encounters": ("encounter_id", "nunique"),
        "average_length_of_stay": ("length_of_stay", "mean"),
        "readmission_rate": ("is_30_day_readmission", "mean"),
        "average_satisfaction": ("patient_satisfaction", "mean"),
    }

    if "department" in working_data.columns:
        aggregation["department"] = ("department", "first")

    doctor_summary = working_data.groupby(
        "doctor_id", as_index=False
    ).agg(**aggregation)

    doctor_summary["readmission_rate"] *= 100

    numeric_columns = [
        "average_length_of_stay",
        "readmission_rate",
        "average_satisfaction",
    ]

    doctor_summary[numeric_columns] = (
        doctor_summary[numeric_columns].fillna(0).round(2)
    )

    return doctor_summary.sort_values(
        by=["unique_patients", "total_encounters"],
        ascending=[False, False],
    ).reset_index(drop=True)


def create_department_level_summary(data: pd.DataFrame) -> pd.DataFrame:
    """
    Create one performance-summary row for each department.
    """
    if data.empty or "department" not in data.columns:
        return pd.DataFrame()

    working_data = _with_readmission_flag(data)

    working_data["length_of_stay"] = pd.to_numeric(
        working_data["length_of_stay"], errors="coerce"
    )

    working_data["patient_satisfaction"] = pd.to_numeric(
        working_data["patient_satisfaction"], errors="coerce"
    )

    department_summary = working_data.groupby(
        "department", as_index=False
    ).agg(
        total_doctors=("doctor_id", "nunique"),
        unique_patients=("patient_nbr", "nunique"),
        total_encounters=("encounter_id", "nunique"),
        average_length_of_stay=("length_of_stay", "mean"),
        readmission_rate=("is_30_day_readmission", "mean"),
        average_satisfaction=("patient_satisfaction", "mean"),
    )

    department_summary["readmission_rate"] *= 100

    department_summary["patients_per_doctor"] = (
        department_summary["unique_patients"]
        / department_summary["total_doctors"].replace(0, pd.NA)
    )

    numeric_columns = [
        "average_length_of_stay",
        "readmission_rate",
        "average_satisfaction",
        "patients_per_doctor",
    ]

    department_summary[numeric_columns] = (
        department_summary[numeric_columns].fillna(0).round(2)
    )

    return department_summary.sort_values(
        "total_encounters", ascending=False
    ).reset_index(drop=True)


def create_monthly_workload_summary(
    data: pd.DataFrame,
    group_by_department: bool = False,
) -> pd.DataFrame:
    """
    Create a monthly workload summary (encounters and unique patients).
    """
    if data.empty or "admission_date" not in data.columns:
        return pd.DataFrame()

    working_data = data.copy()

    working_data["admission_date"] = pd.to_datetime(
        working_data["admission_date"], errors="coerce"
    )

    working_data = working_data.dropna(subset=["admission_date"])

    if working_data.empty:
        return pd.DataFrame()

    working_data["month"] = (
        working_data["admission_date"].dt.to_period("M").dt.to_timestamp()
    )

    group_columns = ["month"]

    if group_by_department and "department" in working_data.columns:
        group_columns.append("department")

    monthly_workload = (
        working_data.groupby(group_columns, as_index=False)
        .agg(
            total_encounters=("encounter_id", "nunique"),
            unique_patients=("patient_nbr", "nunique"),
        )
        .sort_values(group_columns)
        .reset_index(drop=True)
    )

    return monthly_workload
