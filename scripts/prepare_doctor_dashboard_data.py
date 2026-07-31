"""
Prepare the doctor-performance dashboard dataset.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dashboard.data_loader import (
    DASHBOARD_SOURCE_COLUMNS,
    PROCESSED_DATA_PATH,
    load_cleaned_dataset,
    validate_required_columns
)


def build_doctor_department_mapping(data: pd.DataFrame) -> pd.Series:
    """
    Build a consistent one-to-one doctor-to-department mapping.
    """
    department_counts = (
        data.groupby(["doctor_id", "department"])
        .size()
        .rename("row_count")
        .reset_index()
    )

    department_counts = department_counts.sort_values(
        by=["doctor_id", "row_count", "department"],
        ascending=[True, False, True],
    )

    canonical_department = (
        department_counts.groupby("doctor_id")
        .first()["department"]
    )

    return canonical_department


def select_dashboard_columns(data: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the columns the doctor-performance dashboard needs.
    """
    available_columns = [
        column
        for column in DASHBOARD_SOURCE_COLUMNS
        if column in data.columns
    ]

    missing_columns = validate_required_columns(
        data, set(DASHBOARD_SOURCE_COLUMNS)
    )

    if missing_columns:
        print(
            "Warning: the following expected columns were not found "
            f"in the cleaned dataset and will be skipped: "
            f"{', '.join(missing_columns)}"
        )

    return data[available_columns].copy()


def apply_department_mapping(
    data: pd.DataFrame,
    mapping: pd.Series,
) -> pd.DataFrame:
    """
    Overwrite each row's department with the doctor's canonical value.
    """
    working_data = data.copy()

    working_data["department"] = (
        working_data["doctor_id"].map(mapping)
    )

    return working_data


def validate_prepared_dataset(
    data: pd.DataFrame,
    sample_size: int = 3,
) -> None:
    """
    Print a few manual-validation checks for doctors and departments.
    """
    print("\n--- Manual validation sample ---")

    print(
        f"Each doctor now maps to exactly "
        f"{data.groupby('doctor_id')['department'].nunique().max()} "
        "department (should be 1)."
    )

    sample_doctors = (
        data["doctor_id"].drop_duplicates().sort_values().head(sample_size)
    )

    for doctor_id in sample_doctors:
        doctor_rows = data[data["doctor_id"] == doctor_id]

        readmit_rate = (
            doctor_rows["readmitted"].astype(str).str.strip().eq("<30").mean()
            * 100
        )

        print(
            f"  {doctor_id}: department={doctor_rows['department'].iloc[0]}, "
            f"encounters={len(doctor_rows)}, "
            f"avg_length_of_stay={doctor_rows['length_of_stay'].mean():.2f}, "
            f"readmission_rate={readmit_rate:.2f}%"
        )

    print()

    sample_departments = (
        data["department"].drop_duplicates().sort_values().head(sample_size)
    )

    for department in sample_departments:
        department_rows = data[data["department"] == department]

        readmit_rate = (
            department_rows["readmitted"]
            .astype(str)
            .str.strip()
            .eq("<30")
            .mean()
            * 100
        )

        print(
            f"  {department}: "
            f"doctors={department_rows['doctor_id'].nunique()}, "
            f"patients={department_rows['patient_nbr'].nunique()}, "
            f"encounters={len(department_rows)}, "
            f"readmission_rate={readmit_rate:.2f}%"
        )

    print("--- End validation sample ---\n")


def main() -> None:
    """Build and save the processed doctor-performance dataset."""
    print("Loading cleaned dataset...")
    cleaned_data = load_cleaned_dataset()
    print(f"  Loaded {len(cleaned_data):,} rows.")

    print("Selecting dashboard columns...")
    dashboard_data = select_dashboard_columns(cleaned_data)

    print("Building consistent doctor-to-department mapping...")
    department_mapping = build_doctor_department_mapping(cleaned_data)
    print(f"  Mapped {department_mapping.nunique()} unique departments "
          f"across {len(department_mapping)} doctors.")

    dashboard_data = apply_department_mapping(
        dashboard_data, department_mapping
    )

    validate_prepared_dataset(dashboard_data)

    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    dashboard_data.to_csv(PROCESSED_DATA_PATH, index=False)

    print(
        f"Saved processed doctor-performance dataset "
        f"({len(dashboard_data):,} rows, "
        f"{dashboard_data['doctor_id'].nunique():,} doctors) to:\n"
        f"  {PROCESSED_DATA_PATH}"
    )


if __name__ == "__main__":
    main()
