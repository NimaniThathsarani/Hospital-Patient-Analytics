"""
Department-performance components for the Doctor Performance Dashboard.
"""

from __future__ import annotations
import plotly.express as px
import streamlit as st
import pandas as pd

from kpi_calculations import (
    create_department_level_summary,
    create_monthly_workload_summary,
    total_doctors,
    total_encounters,
    unique_patients_treated
)

REQUIRED_DEPARTMENT_COLUMNS = {
    "doctor_id",
    "department",
    "patient_nbr",
    "encounter_id",
    "length_of_stay",
    "readmitted",
    "patient_satisfaction",
}

# Friendly labels shared by the comparison table and chart selector.
METRIC_LABELS = {
    "unique_patients": "Patients Treated",
    "total_encounters": "Total Encounters",
    "total_doctors": "Number of Doctors",
    "average_length_of_stay": "Average Length of Stay",
    "readmission_rate": "30-Day Readmission Rate (%)",
    "average_satisfaction": "Average Satisfaction",
    "patients_per_doctor": "Patients per Doctor",
}


def validate_department_data(data: pd.DataFrame) -> list[str]:
    """
    Return required department-analysis columns missing from the data.
    """
    return sorted(REQUIRED_DEPARTMENT_COLUMNS.difference(data.columns))


def prepare_department_summary_for_display(
    summary: pd.DataFrame,
) -> pd.DataFrame:
    """
    Rename department-summary columns for display and export.
    """
    display_summary = summary.rename(
        columns={
            "department": "Department",
            "total_doctors": METRIC_LABELS["total_doctors"],
            "unique_patients": METRIC_LABELS["unique_patients"],
            "total_encounters": METRIC_LABELS["total_encounters"],
            "average_length_of_stay": (
                METRIC_LABELS["average_length_of_stay"]
            ),
            "readmission_rate": METRIC_LABELS["readmission_rate"],
            "average_satisfaction": (
                METRIC_LABELS["average_satisfaction"]
            ),
            "patients_per_doctor": (
                METRIC_LABELS["patients_per_doctor"]
            ),
        }
    )

    expected_columns = [
        "Department",
        METRIC_LABELS["total_doctors"],
        METRIC_LABELS["unique_patients"],
        METRIC_LABELS["total_encounters"],
        METRIC_LABELS["average_length_of_stay"],
        METRIC_LABELS["readmission_rate"],
        METRIC_LABELS["average_satisfaction"],
        METRIC_LABELS["patients_per_doctor"],
    ]

    return display_summary[expected_columns]


def _render_department_bar_chart(
    department_summary: pd.DataFrame,
    metric_column: str,
    title: str,
) -> None:
    """Render a single department bar chart for one metric."""
    chart = px.bar(
        department_summary.sort_values(metric_column, ascending=False),
        x="department",
        y=metric_column,
        color="department",
        title=title,
        labels={
            "department": "Department",
            metric_column: METRIC_LABELS.get(metric_column, metric_column),
        },
    )

    chart.update_layout(
        showlegend=False,
        height=380,
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )

    st.plotly_chart(chart, width='stretch')


def render_department_performance(data: pd.DataFrame) -> None:
    """
    Render the Department Performance dashboard page.
    """
    st.subheader("Department Performance")

    missing_columns = validate_department_data(data)

    if missing_columns:
        st.error(
            "Department performance cannot be displayed because "
            f"these columns are missing: {', '.join(missing_columns)}"
        )
        return

    if data.empty:
        st.warning(
            "No records are available for the selected filters."
        )
        return

    st.caption(
        "Operational performance broken down by department: "
        "workload, length of stay, 30-day readmission rate, and "
        "patient satisfaction."
    )

    department_summary = create_department_level_summary(data)

    if department_summary.empty:
        st.info("Department performance data is unavailable.")
        return

    # Headline KPI row
    first_row = st.columns(4)

    with first_row[0]:
        st.metric(
            "Departments",
            f"{department_summary['department'].nunique():,}",
        )

    with first_row[1]:
        st.metric("Total Doctors", f"{total_doctors(data):,}")

    with first_row[2]:
        st.metric(
            "Unique Patients",
            f"{unique_patients_treated(data):,}",
        )

    with first_row[3]:
        st.metric("Total Encounters", f"{total_encounters(data):,}")

    # Department comparison charts
    st.markdown("### Department Comparison")

    chart_metric_options = {
        METRIC_LABELS["unique_patients"]: "unique_patients",
        METRIC_LABELS["total_encounters"]: "total_encounters",
        METRIC_LABELS["total_doctors"]: "total_doctors",
        METRIC_LABELS["average_length_of_stay"]: (
            "average_length_of_stay"
        ),
        METRIC_LABELS["readmission_rate"]: "readmission_rate",
        METRIC_LABELS["average_satisfaction"]: (
            "average_satisfaction"
        ),
        METRIC_LABELS["patients_per_doctor"]: "patients_per_doctor",
    }

    selected_metric_label = st.selectbox(
        "Select a metric to compare across departments",
        list(chart_metric_options.keys()),
        key="department_comparison_metric",
    )

    selected_metric_column = chart_metric_options[selected_metric_label]

    chart_column_1, chart_column_2 = st.columns(2)

    with chart_column_1:
        _render_department_bar_chart(
            department_summary,
            selected_metric_column,
            f"{selected_metric_label} by Department",
        )

    with chart_column_2:
        _render_department_bar_chart(
            department_summary,
            "readmission_rate",
            "30-Day Readmission Rate by Department",
        )

    st.markdown("### Department Comparison Table")

    display_summary = prepare_department_summary_for_display(
        department_summary
    )

    st.dataframe(
        display_summary,
        width='stretch',
        hide_index=True,
    )

    st.download_button(
        label="Download Department Comparison CSV",
        data=display_summary.to_csv(index=False).encode("utf-8"),
        file_name="department_performance_comparison.csv",
        mime="text/csv",
        key="download_department_comparison",
    )

    # Monthly workload trend
    st.markdown("### Monthly Workload Trend by Department")

    monthly_department_workload = create_monthly_workload_summary(
        data, group_by_department=True
    )

    if monthly_department_workload.empty:
        st.info(
            "Monthly workload cannot be displayed because valid "
            "admission dates are unavailable."
        )
        return

    available_departments = sorted(
        department_summary["department"].astype(str).unique().tolist()
    )

    selected_departments = st.multiselect(
        "Departments to include in the trend chart",
        options=available_departments,
        default=available_departments,
        key="department_trend_filter",
    )

    trend_data = monthly_department_workload[
        monthly_department_workload["department"]
        .astype(str)
        .isin(selected_departments)
    ]

    if trend_data.empty:
        st.info("Select at least one department to see the trend.")
        return

    trend_chart = px.line(
        trend_data,
        x="month",
        y="total_encounters",
        color="department",
        markers=True,
        title="Monthly Encounters by Department",
        labels={
            "month": "Month",
            "total_encounters": "Total Encounters",
            "department": "Department",
        },
        hover_data={"unique_patients": True},
    )

    trend_chart.update_layout(
        height=450,
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )

    st.plotly_chart(trend_chart, width='stretch')
