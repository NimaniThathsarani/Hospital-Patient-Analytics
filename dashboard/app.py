"""
Main application for the Doctor Performance Dashboard.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from doctor_analysis import (
    render_doctor_comparison,
    render_doctor_details,
)
from overview import render_executive_overview
from styles import apply_dashboard_styles


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLEANED_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "cleaned"
    / "cleaned_dataset.csv"
)


@st.cache_data
def load_temporary_dashboard_data() -> pd.DataFrame:
    """
    Load the cleaned hospital dataset for dashboard development.

    Pasindu's processed doctor-performance dataset and data loader
    will replace this function during final integration.

    Returns:
        Cleaned hospital data prepared for dashboard filtering.

    Raises:
        FileNotFoundError: If cleaned_dataset.csv does not exist.
    """
    if not CLEANED_DATA_PATH.exists():
        raise FileNotFoundError(
            "The cleaned dataset was not found at: "
            f"{CLEANED_DATA_PATH}"
        )

    data = pd.read_csv(
        CLEANED_DATA_PATH,
        low_memory=False,
    )

    if "admission_date" in data.columns:
        data["admission_date"] = pd.to_datetime(
            data["admission_date"],
            errors="coerce",
        )

    for numeric_column in [
        "length_of_stay",
        "patient_satisfaction",
    ]:
        if numeric_column in data.columns:
            data[numeric_column] = pd.to_numeric(
                data[numeric_column],
                errors="coerce",
            )

    return data


def apply_sidebar_filters(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Display dashboard filters and return the filtered dataset.

    Args:
        data: Complete temporary dashboard dataset.

    Returns:
        Filtered dashboard dataset.
    """
    filtered_data = data.copy()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Dashboard Filters")

    if (
        "admission_date" in filtered_data.columns
        and filtered_data["admission_date"].notna().any()
    ):
        minimum_date = (
            filtered_data["admission_date"]
            .min()
            .date()
        )

        maximum_date = (
            filtered_data["admission_date"]
            .max()
            .date()
        )

        selected_dates = st.sidebar.date_input(
            "Admission Date Range",
            value=(minimum_date, maximum_date),
            min_value=minimum_date,
            max_value=maximum_date,
        )

        if len(selected_dates) == 2:
            start_date, end_date = selected_dates

            filtered_data = filtered_data[
                filtered_data[
                    "admission_date"
                ].dt.date.between(
                    start_date,
                    end_date,
                )
            ]

    if "department" in filtered_data.columns:
        departments = sorted(
            filtered_data["department"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_departments = st.sidebar.multiselect(
            "Department",
            options=departments,
            default=departments,
        )

        if selected_departments:
            filtered_data = filtered_data[
                filtered_data["department"]
                .astype(str)
                .isin(selected_departments)
            ]
        else:
            filtered_data = filtered_data.iloc[0:0]

    if "doctor_id" in filtered_data.columns:
        doctors = sorted(
            filtered_data["doctor_id"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_doctors = st.sidebar.multiselect(
            "Doctor",
            options=doctors,
            placeholder="Leave empty to include all doctors",
        )

        if selected_doctors:
            filtered_data = filtered_data[
                filtered_data["doctor_id"]
                .astype(str)
                .isin(selected_doctors)
            ]

    if "gender" in filtered_data.columns:
        genders = sorted(
            filtered_data["gender"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_genders = st.sidebar.multiselect(
            "Gender",
            options=genders,
            default=genders,
        )

        if selected_genders:
            filtered_data = filtered_data[
                filtered_data["gender"]
                .astype(str)
                .isin(selected_genders)
            ]
        else:
            filtered_data = filtered_data.iloc[0:0]

    if "readmitted" in filtered_data.columns:
        readmission_values = sorted(
            filtered_data["readmitted"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_readmission_values = st.sidebar.multiselect(
            "Readmission Status",
            options=readmission_values,
            default=readmission_values,
        )

        if selected_readmission_values:
            filtered_data = filtered_data[
                filtered_data["readmitted"]
                .astype(str)
                .isin(selected_readmission_values)
            ]
        else:
            filtered_data = filtered_data.iloc[0:0]

    st.sidebar.caption(
        f"Filtered records: {len(filtered_data):,}"
    )

    return filtered_data


st.set_page_config(
    page_title="Doctor Performance Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    apply_dashboard_styles(),
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="dashboard-title">
        Doctor Performance Dashboard
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="dashboard-subtitle">
        Interactive hospital analytics for doctor and department performance.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Dashboard Navigation")

    selected_page = st.radio(
        "Select Page",
        [
            "Executive Overview",
            "Doctor Comparison",
            "Department Performance",
            "Doctor Details",
        ],
    )

try:
    dashboard_data = load_temporary_dashboard_data()

except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

filtered_data = apply_sidebar_filters(
    dashboard_data
)

st.warning(
    "Development mode: this dashboard is temporarily using "
    "data/cleaned/cleaned_dataset.csv. Pasindu's processed "
    "doctor-performance dataset will replace it during integration."
)

if filtered_data.empty:
    st.warning(
        "No records match the selected filters. "
        "Change the sidebar selections."
    )
    st.stop()

if selected_page == "Executive Overview":
    render_executive_overview(
        filtered_data
    )

elif selected_page == "Doctor Comparison":
    render_doctor_comparison(
        filtered_data
    )

elif selected_page == "Department Performance":
    st.info(
        "The Department Performance page will be connected after "
        "Pasindu's department analysis module is merged."
    )

elif selected_page == "Doctor Details":
    render_doctor_details(
        filtered_data
    )