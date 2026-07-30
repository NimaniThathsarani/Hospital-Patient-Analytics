"""
Main application for the Doctor Performance Dashboard.
"""

import streamlit as st

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

st.info(f"Current page: {selected_page}")

st.markdown(
    """
    <div class="data-note">
        Dashboard data and KPI calculations will be connected in the next steps.
    </div>
    """,
    unsafe_allow_html=True,
)