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


def create_single_doctor_metrics(
    data: pd.DataFrame,
    doctor_id: str,
) -> dict[str, object]:
    """
    Calculate detailed KPIs for one selected doctor.

    Args:
        data: Filtered hospital dashboard dataset.
        doctor_id: Doctor identifier selected by the user.

    Returns:
        Dictionary containing the selected doctor's KPIs.
    """
    doctor_data = data[data["doctor_id"] == doctor_id].copy()

    if doctor_data.empty:
        return {}

    doctor_data["is_30_day_readmission"] = (
        doctor_data["readmitted"].astype(str).str.strip() == "<30"
    )

    department = doctor_data["department"].mode()

    return {
        "doctor_id": doctor_id,
        "department": (
            department.iloc[0]
            if not department.empty
            else "Unknown"
        ),
        "unique_patients": doctor_data["patient_nbr"].nunique(),
        "total_encounters": doctor_data["encounter_id"].nunique(),
        "average_length_of_stay": round(
            doctor_data["length_of_stay"].mean(),
            2,
        ),
        "readmission_rate": round(
            doctor_data["is_30_day_readmission"].mean() * 100,
            2,
        ),
        "average_satisfaction": round(
            doctor_data["patient_satisfaction"].mean(),
            2,
        ),
    }


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


def render_doctor_details(data: pd.DataFrame) -> None:
    """
    Render a detailed drill-down view for one selected doctor.

    Args:
        data: Filtered hospital dashboard dataset.
    """
    st.subheader("Doctor Details")

    missing_columns = validate_doctor_data(data)

    if missing_columns:
        st.error(
            "Doctor details cannot be displayed because these columns "
            f"are missing: {', '.join(missing_columns)}"
        )
        return

    available_doctors = sorted(
        data["doctor_id"].dropna().astype(str).unique().tolist()
    )

    if not available_doctors:
        st.warning("No doctors are available for the selected filters.")
        return

    selected_doctor = st.selectbox(
        "Select Doctor",
        available_doctors,
        key="doctor_details_selector",
    )

    metrics = create_single_doctor_metrics(
        data,
        selected_doctor,
    )

    if not metrics:
        st.warning("No records were found for the selected doctor.")
        return

    st.caption(
        f"Department: {metrics['department']}"
    )

    column_1, column_2, column_3, column_4, column_5 = st.columns(5)

    with column_1:
        st.metric(
            "Unique Patients",
            f"{metrics['unique_patients']:,}",
        )

    with column_2:
        st.metric(
            "Total Encounters",
            f"{metrics['total_encounters']:,}",
        )

    with column_3:
        st.metric(
            "Average Length of Stay",
            f"{metrics['average_length_of_stay']:.2f} days",
        )

    with column_4:
        st.metric(
            "30-Day Readmission Rate",
            f"{metrics['readmission_rate']:.2f}%",
        )

    with column_5:
        st.metric(
            "Average Satisfaction",
            f"{metrics['average_satisfaction']:.2f} / 5",
        )

    doctor_data = data[
        data["doctor_id"].astype(str) == selected_doctor
    ].copy()

    display_columns = [
        column
        for column in [
            "encounter_id",
            "patient_nbr",
            "department",
            "admission_date",
            "length_of_stay",
            "readmitted",
            "patient_satisfaction",
            "diag_1",
        ]
        if column in doctor_data.columns
    ]

    st.markdown("### Encounter Details")

    st.dataframe(
        doctor_data[display_columns],
        use_container_width=True,
        hide_index=True,
    )