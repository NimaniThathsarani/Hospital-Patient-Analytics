"""
Main application for the Doctor Performance Dashboard.
"""

import streamlit as st

from doctor_analysis import (
    render_doctor_comparison,
    render_doctor_details,
)
from styles import apply_dashboard_styles


st.set_page_config(
    page_title="Doctor Performance Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(apply_dashboard_styles(), unsafe_allow_html=True)

st.markdown(
    '<div class="dashboard-title">Doctor Performance Dashboard</div>',
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

if selected_page == "Executive Overview":
    st.info(
        "Executive Overview will be connected after the shared KPI module is ready."
    )

elif selected_page == "Doctor Comparison":
    st.warning(
        "Doctor comparison calculations are ready, but the page needs the "
        "processed dashboard dataset and shared data loader before results "
        "can be displayed."
    )

elif selected_page == "Department Performance":
    st.info(
        "Department Performance will be connected after the department "
        "analysis module is completed."
    )

elif selected_page == "Doctor Details":
    st.warning(
        "Doctor details functionality is ready, but it needs the processed "
        "dashboard dataset before the drill-down page can be displayed."
    )