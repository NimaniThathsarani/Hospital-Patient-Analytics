"""
Doctor-level analysis components for the Doctor Performance Dashboard.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


REQUIRED_DOCTOR_COLUMNS = {
    "doctor_id",
    "department",
    "patient_nbr",
    "encounter_id",
    "length_of_stay",
    "readmitted",
    "patient_satisfaction",
}


def validate_doctor_data(data: pd.DataFrame) -> list[str]:
    """
    Return a list of required doctor-analysis columns missing from the dataset.

    Args:
        data: Filtered hospital dashboard dataset.

    Returns:
        A sorted list of missing column names.
    """
    return sorted(REQUIRED_DOCTOR_COLUMNS.difference(data.columns))


def create_doctor_summary(data: pd.DataFrame) -> pd.DataFrame:
    """
    Create one performance-summary row for each doctor.

    Args:
        data: Filtered hospital dashboard dataset.

    Returns:
        Doctor-level summary containing workload and performance KPIs.
    """
    if data.empty:
        return pd.DataFrame()

    working_data = data.copy()

    working_data["is_30_day_readmission"] = (
        working_data["readmitted"].astype(str).str.strip() == "<30"
    )

    doctor_summary = (
        working_data.groupby(["doctor_id", "department"], as_index=False)
        .agg(
            unique_patients=("patient_nbr", "nunique"),
            total_encounters=("encounter_id", "nunique"),
            average_length_of_stay=("length_of_stay", "mean"),
            readmission_rate=("is_30_day_readmission", "mean"),
            average_satisfaction=("patient_satisfaction", "mean"),
        )
    )

    doctor_summary["readmission_rate"] *= 100

    doctor_summary["average_length_of_stay"] = doctor_summary[
        "average_length_of_stay"
    ].round(2)

    doctor_summary["readmission_rate"] = doctor_summary[
        "readmission_rate"
    ].round(2)

    doctor_summary["average_satisfaction"] = doctor_summary[
        "average_satisfaction"
    ].round(2)

    return doctor_summary.sort_values(
        by=["unique_patients", "total_encounters"],
        ascending=[False, False],
    ).reset_index(drop=True)


def render_doctor_comparison(data: pd.DataFrame) -> None:
    """
    Render the doctor comparison section in Streamlit.

    Args:
        data: Filtered hospital dashboard dataset.
    """
    st.subheader("Doctor Comparison")

    missing_columns = validate_doctor_data(data)

    if missing_columns:
        st.error(
            "Doctor comparison cannot be displayed because these columns "
            f"are missing: {', '.join(missing_columns)}"
        )
        return

    doctor_summary = create_doctor_summary(data)

    if doctor_summary.empty:
        st.warning("No doctor records are available for the selected filters.")
        return

    st.caption(
        "Compare doctors using patient volume, length of stay, "
        "30-day readmission rate, and patient satisfaction."
    )

    display_summary = doctor_summary.rename(
        columns={
            "doctor_id": "Doctor ID",
            "department": "Department",
            "unique_patients": "Unique Patients",
            "total_encounters": "Total Encounters",
            "average_length_of_stay": "Average Length of Stay",
            "readmission_rate": "30-Day Readmission Rate (%)",
            "average_satisfaction": "Average Satisfaction",
        }
    )

    st.dataframe(
        display_summary,
        use_container_width=True,
        hide_index=True,
    )