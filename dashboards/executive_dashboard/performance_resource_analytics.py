"""
Performance & Resource Analytics dashboard for the Executive Analysis page.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd


def render_performance_resource_analytics(data: pd.DataFrame) -> None:
    """Render the Performance & Resource Analytics dashboard."""
    st.markdown(
        """
        <div style="margin-bottom:0.3rem;">
            <span style="font-size:2rem;font-weight:700;color:#16324f;">
                📊 Performance &amp; Resource Analytics
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "This dashboard is under construction. "
        "Performance & Resource Analytics will appear here."
    )
