"""
Main application for the Executive KPI Dashboard.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from data_loader import load_dashboard_dataset
from styles import apply_dashboard_styles
from patient_hospital_performance import render_patient_hospital_performance
from performance_resource_analytics import render_performance_resource_analytics


@st.cache_data(show_spinner="Loading dashboard data…")
def load_dashboard_data() -> tuple[pd.DataFrame, str]:
    """Load data with caching to avoid reloading on every interaction."""
    data, source = load_dashboard_dataset()
    if "admission_date" in data.columns:
        data["admission_date"] = pd.to_datetime(data["admission_date"], errors="coerce")
    # Derive age_group from 'age' column if not present (dataset uses 'age' brackets)
    if "age_group" not in data.columns and "age" in data.columns:
        data["age_group"] = data["age"].astype(str).str.strip()
    return data, source


def apply_sidebar_filters(data: pd.DataFrame) -> pd.DataFrame:
    """Display dashboard filters and return the filtered dataset."""
    filtered_data = data.copy()

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Global Filters")

    # 1. Date Range Filter
    if "admission_date" in filtered_data.columns and filtered_data["admission_date"].notna().any():
        min_date = filtered_data["admission_date"].min().date()
        max_date = filtered_data["admission_date"].max().date()
        date_range = st.sidebar.date_input(
            "📅 Admission Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
            start_date, end_date = date_range
            filtered_data = filtered_data[
                (filtered_data["admission_date"].dt.date >= start_date)
                & (filtered_data["admission_date"].dt.date <= end_date)
            ]

    # 2. Department Filter
    if "department" in filtered_data.columns:
        departments = sorted(filtered_data["department"].dropna().unique().tolist())
        selected_depts = st.sidebar.multiselect(
            "🏢 Department",
            options=departments,
            default=departments,
        )
        if selected_depts:
            filtered_data = filtered_data[filtered_data["department"].isin(selected_depts)]
        else:
            filtered_data = filtered_data.iloc[0:0]

    # 3. Patient Category / Age Group Filter (uses 'age_group' derived from 'age')
    if "age_group" in filtered_data.columns:
        age_groups = sorted(
            filtered_data["age_group"].dropna().astype(str).unique().tolist()
        )
        selected_ages = st.sidebar.multiselect(
            "👤 Patient Age Group",
            options=age_groups,
            default=age_groups,
        )
        if selected_ages:
            filtered_data = filtered_data[
                filtered_data["age_group"].astype(str).isin(selected_ages)
            ]
        else:
            filtered_data = filtered_data.iloc[0:0]

    # 4. Gender Filter
    if "gender" in filtered_data.columns:
        genders = sorted(filtered_data["gender"].dropna().astype(str).unique().tolist())
        selected_genders = st.sidebar.multiselect(
            "⚧ Gender",
            options=genders,
            default=genders,
        )
        if selected_genders:
            filtered_data = filtered_data[
                filtered_data["gender"].astype(str).isin(selected_genders)
            ]
        else:
            filtered_data = filtered_data.iloc[0:0]

    st.sidebar.markdown("---")
    st.sidebar.caption(f"📊 Filtered records: **{len(filtered_data):,}**")
    return filtered_data


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Executive KPI Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(apply_dashboard_styles(), unsafe_allow_html=True)

with st.sidebar:
    st.header("📈 Executive Navigation")
    selected_dashboard = st.radio(
        "Select Dashboard Module",
        [
            "Patient & Hospital Performance",
            "Performance & Resource Analytics",
        ],
    )

st.markdown(
    """
    <div class="dashboard-title">
        📈 Executive KPI Dashboard
    </div>
    <div class="dashboard-subtitle">
        Management insights into hospital operations, efficiency, and patient care.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data loading & filtering
# ---------------------------------------------------------------------------
try:
    dashboard_data, _ = load_dashboard_data()
    if dashboard_data.empty:
        st.error("Dashboard dataset is empty.")
        st.stop()
except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
    st.stop()

filtered_data = apply_sidebar_filters(dashboard_data)

if filtered_data.empty:
    st.warning("No records match the selected filters. Please adjust your selections.")
    st.stop()

# ---------------------------------------------------------------------------
# Module routing
# ---------------------------------------------------------------------------
if selected_dashboard == "Patient & Hospital Performance":
    render_patient_hospital_performance(filtered_data)
elif selected_dashboard == "Performance & Resource Analytics":
    render_performance_resource_analytics(filtered_data)
