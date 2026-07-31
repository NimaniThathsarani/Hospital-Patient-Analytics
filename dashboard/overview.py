"""
Executive overview components for the Doctor Performance Dashboard.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


REQUIRED_OVERVIEW_COLUMNS = {
    "doctor_id",
    "department",
    "patient_nbr",
    "encounter_id",
    "length_of_stay",
    "readmitted",
    "patient_satisfaction",
}


def validate_overview_data(data: pd.DataFrame) -> list[str]:
    """
    Return required overview columns missing from the dataset.

    Args:
        data: Filtered hospital dashboard dataset.

    Returns:
        Sorted list of missing column names.
    """
    return sorted(
        REQUIRED_OVERVIEW_COLUMNS.difference(data.columns)
    )


def create_overview_metrics(
    data: pd.DataFrame,
) -> dict[str, float | int]:
    """
    Calculate hospital-level dashboard KPIs.

    Args:
        data: Filtered hospital dashboard dataset.

    Returns:
        Dictionary containing executive overview KPIs.
    """
    if data.empty:
        return {}

    working_data = data.copy()

    working_data["is_30_day_readmission"] = (
        working_data["readmitted"]
        .astype(str)
        .str.strip()
        .eq("<30")
    )

    average_length_of_stay = pd.to_numeric(
        working_data["length_of_stay"],
        errors="coerce",
    ).mean()

    average_satisfaction = pd.to_numeric(
        working_data["patient_satisfaction"],
        errors="coerce",
    ).mean()

    return {
        "total_doctors": int(
            working_data["doctor_id"].nunique()
        ),
        "unique_patients": int(
            working_data["patient_nbr"].nunique()
        ),
        "total_encounters": int(
            working_data["encounter_id"].nunique()
        ),
        "average_length_of_stay": (
            round(float(average_length_of_stay), 2)
            if pd.notna(average_length_of_stay)
            else 0.0
        ),
        "readmission_rate": round(
            float(
                working_data[
                    "is_30_day_readmission"
                ].mean()
                * 100
            ),
            2,
        ),
        "average_satisfaction": (
            round(float(average_satisfaction), 2)
            if pd.notna(average_satisfaction)
            else 0.0
        ),
    }


def create_department_overview(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create department-level performance summary.

    Args:
        data: Filtered hospital dashboard dataset.

    Returns:
        Department-level KPI summary.
    """
    if data.empty:
        return pd.DataFrame()

    working_data = data.copy()

    working_data["is_30_day_readmission"] = (
        working_data["readmitted"]
        .astype(str)
        .str.strip()
        .eq("<30")
    )

    department_summary = (
        working_data.groupby(
            "department",
            as_index=False,
        )
        .agg(
            total_doctors=("doctor_id", "nunique"),
            unique_patients=("patient_nbr", "nunique"),
            total_encounters=("encounter_id", "nunique"),
            average_length_of_stay=(
                "length_of_stay",
                "mean",
            ),
            readmission_rate=(
                "is_30_day_readmission",
                "mean",
            ),
            average_satisfaction=(
                "patient_satisfaction",
                "mean",
            ),
        )
    )

    department_summary["readmission_rate"] *= 100

    department_summary[
        "average_length_of_stay"
    ] = department_summary[
        "average_length_of_stay"
    ].round(2)

    department_summary[
        "readmission_rate"
    ] = department_summary[
        "readmission_rate"
    ].round(2)

    department_summary[
        "average_satisfaction"
    ] = department_summary[
        "average_satisfaction"
    ].round(2)

    return department_summary.sort_values(
        "total_encounters",
        ascending=False,
    ).reset_index(drop=True)


def create_monthly_hospital_workload(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create monthly hospital workload totals.

    Args:
        data: Filtered hospital dashboard dataset.

    Returns:
        Monthly encounter and patient summary.
    """
    if data.empty or "admission_date" not in data.columns:
        return pd.DataFrame()

    working_data = data.copy()

    working_data["admission_date"] = pd.to_datetime(
        working_data["admission_date"],
        errors="coerce",
    )

    working_data = working_data.dropna(
        subset=["admission_date"]
    )

    if working_data.empty:
        return pd.DataFrame()

    working_data["month"] = (
        working_data["admission_date"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    monthly_workload = (
        working_data.groupby(
            "month",
            as_index=False,
        )
        .agg(
            total_encounters=("encounter_id", "nunique"),
            unique_patients=("patient_nbr", "nunique"),
        )
        .sort_values("month")
    )

    return monthly_workload


def render_executive_overview(
    data: pd.DataFrame,
) -> None:
    """
    Render the executive overview dashboard page.

    Args:
        data: Filtered hospital dashboard dataset.
    """
    st.subheader("Executive Overview")

    missing_columns = validate_overview_data(data)

    if missing_columns:
        st.error(
            "The Executive Overview cannot be displayed because "
            f"these columns are missing: {', '.join(missing_columns)}"
        )
        return

    metrics = create_overview_metrics(data)

    if not metrics:
        st.warning(
            "No records are available for the selected filters."
        )
        return

    first_row = st.columns(3)

    with first_row[0]:
        st.metric(
            "Total Doctors",
            f"{metrics['total_doctors']:,}",
        )

    with first_row[1]:
        st.metric(
            "Unique Patients",
            f"{metrics['unique_patients']:,}",
        )

    with first_row[2]:
        st.metric(
            "Total Encounters",
            f"{metrics['total_encounters']:,}",
        )

    second_row = st.columns(3)

    with second_row[0]:
        st.metric(
            "Average Length of Stay",
            f"{metrics['average_length_of_stay']:.2f} days",
        )

    with second_row[1]:
        st.metric(
            "30-Day Readmission Rate",
            f"{metrics['readmission_rate']:.2f}%",
        )

    with second_row[2]:
        st.metric(
            "Average Satisfaction",
            f"{metrics['average_satisfaction']:.2f} / 5",
        )

    st.markdown("### Department Performance Snapshot")

    department_summary = create_department_overview(data)

    if department_summary.empty:
        st.info(
            "Department performance data is unavailable."
        )
    else:
        chart_column_1, chart_column_2 = st.columns(2)

        with chart_column_1:
            encounter_chart = px.bar(
                department_summary,
                x="department",
                y="total_encounters",
                color="department",
                title="Total Encounters by Department",
                labels={
                    "department": "Department",
                    "total_encounters": "Total Encounters",
                },
            )

            encounter_chart.update_layout(
                showlegend=False,
                height=420,
                margin={
                    "l": 20,
                    "r": 20,
                    "t": 60,
                    "b": 20,
                },
            )

            st.plotly_chart(
                encounter_chart,
                width='stretch',
            )

        with chart_column_2:
            readmission_chart = px.bar(
                department_summary,
                x="department",
                y="readmission_rate",
                color="department",
                title="30-Day Readmission Rate by Department",
                labels={
                    "department": "Department",
                    "readmission_rate": "Readmission Rate (%)",
                },
            )

            readmission_chart.update_layout(
                showlegend=False,
                height=420,
                margin={
                    "l": 20,
                    "r": 20,
                    "t": 60,
                    "b": 20,
                },
            )

            st.plotly_chart(
                readmission_chart,
                width='stretch',
            )

        display_summary = department_summary.rename(
            columns={
                "department": "Department",
                "total_doctors": "Doctors",
                "unique_patients": "Unique Patients",
                "total_encounters": "Total Encounters",
                "average_length_of_stay": (
                    "Average Length of Stay"
                ),
                "readmission_rate": (
                    "30-Day Readmission Rate (%)"
                ),
                "average_satisfaction": (
                    "Average Satisfaction"
                ),
            }
        )

        st.dataframe(
            display_summary,
            width='stretch',
            hide_index=True,
        )

    st.markdown("### Monthly Hospital Workload")

    monthly_workload = create_monthly_hospital_workload(
        data
    )

    if monthly_workload.empty:
        st.info(
            "Monthly workload cannot be displayed because "
            "valid admission dates are unavailable."
        )
    else:
        workload_chart = px.line(
            monthly_workload,
            x="month",
            y="total_encounters",
            markers=True,
            title="Monthly Encounter Trend",
            labels={
                "month": "Month",
                "total_encounters": "Total Encounters",
            },
            hover_data={
                "unique_patients": True,
            },
        )

        workload_chart.update_layout(
            height=450,
            margin={
                "l": 20,
                "r": 20,
                "t": 60,
                "b": 20,
            },
        )

        st.plotly_chart(
            workload_chart,
            width='stretch',
        )
