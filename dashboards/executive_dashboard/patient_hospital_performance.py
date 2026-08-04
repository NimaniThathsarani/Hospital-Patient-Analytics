"""
Patient & Hospital Performance dashboard for the Executive Analysis page.

Covers:
    - Total Patients, Readmission Rate, ALOS, Bed Occupancy Rate
    - Admission Forecasts (monthly trend + linear regression projection)
    - High-Risk Patients (30-day readmission flag)
    - Interactive filters: date range, department, age group, gender
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression
import numpy as np

# ---------------------------------------------------------------------------
# 1. Imports from shared dashboard utilities
# ---------------------------------------------------------------------------
from styles import (
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    ACCENT_COLOR,
    WARNING_COLOR,
    SUCCESS_COLOR,
    NEUTRAL_COLOR,
    CHART_TEMPLATE,
)
from kpi_calculations import (
    READMISSION_POSITIVE_VALUE,
    _with_readmission_flag,
    _safe_round,
)


def compute_kpis(data: pd.DataFrame) -> dict:
    """Compute top-level KPIs for the Patient & Hospital Performance dashboard."""
    if data.empty:
        return {}

    wd = _with_readmission_flag(data)
    total_patients = wd["patient_nbr"].nunique()
    total_encounters = wd["encounter_id"].nunique()

    # Readmission Rate
    readmissions = wd["is_30_day_readmission"].sum()
    readmission_rate = (readmissions / total_encounters * 100) if total_encounters > 0 else 0.0

    # ALOS (Average Length of Stay)
    alos = wd["length_of_stay"].mean() if "length_of_stay" in wd.columns else 0.0

    # Bed Occupancy (Mock estimation based on encounters and fixed beds)
    TOTAL_BEDS = 500
    avg_daily_census = total_encounters / 30.0  # assuming 30 days for mock
    bed_occupancy_rate = (avg_daily_census / TOTAL_BEDS * 100)

    # High-Risk Patients
    high_risk_count = readmissions  # simplifying high-risk as 30-day readmissions

    return {
        "total_patients": total_patients,
        "total_encounters": total_encounters,
        "readmission_rate": _safe_round(readmission_rate, 1),
        "alos": _safe_round(alos, 1),
        "bed_occupancy": _safe_round(bed_occupancy_rate, 1),
        "high_risk_count": int(high_risk_count),
    }


def _kpi_card(title: str, value: str | int | float, icon: str, color: str) -> str:
    """HTML string for a consistent KPI card."""
    return f"""
    <div class="kpi-card" style="border-top: 4px solid {color};">
        <div class="kpi-icon" style="color: {color};">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """


# ---------------------------------------------------------------------------
# 2. Chart Builders
# ---------------------------------------------------------------------------

def build_monthly_admissions_chart(data: pd.DataFrame) -> go.Figure | None:
    """Line chart showing admissions over time with a simple forecast."""
    if "admission_date" not in data.columns:
        return None
    wd = data.copy()
    wd["admission_date"] = pd.to_datetime(wd["admission_date"], errors="coerce")
    wd = wd.dropna(subset=["admission_date"])
    if wd.empty:
        return None

    wd["month"] = wd["admission_date"].dt.to_period("M").dt.to_timestamp()
    monthly = wd.groupby("month").size().reset_index(name="admissions")

    months_numeric = np.arange(len(monthly)).reshape(-1, 1)
    reg = LinearRegression().fit(months_numeric, monthly["admissions"].values)
    forecast_steps = 3
    future_numeric = np.arange(len(monthly) + forecast_steps).reshape(-1, 1)
    forecast_values = reg.predict(future_numeric)

    last_date = monthly["month"].max()
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, forecast_steps + 1)]
    all_dates = list(monthly["month"]) + future_dates

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["admissions"],
        mode="lines+markers", name="Actual Admissions",
        line=dict(color=PRIMARY_COLOR, width=3)
    ))
    fig.add_trace(go.Scatter(
        x=all_dates, y=forecast_values,
        mode="lines", name="Forecast Trend",
        line=dict(color=ACCENT_COLOR, width=2, dash="dash")
    ))
    fig.update_layout(
        template=CHART_TEMPLATE, title="Admissions Trend & Forecast (Next 3 Months)",
        xaxis_title="Month", yaxis_title="Total Admissions", height=380
    )
    return fig


def build_alos_by_department_chart(data: pd.DataFrame) -> go.Figure | None:
    """Bar chart for ALOS by department."""
    if "department" not in data.columns or "length_of_stay" not in data.columns:
        return None
    dept = data.groupby("department", as_index=False)["length_of_stay"].mean()
    dept = dept.sort_values("length_of_stay", ascending=False)
    fig = px.bar(
        dept, x="department", y="length_of_stay", color="department",
        title="Average Length of Stay (Days) by Department",
        labels={"department": "Department", "length_of_stay": "ALOS (Days)"}
    )
    fig.update_layout(template=CHART_TEMPLATE, height=350, showlegend=False)
    fig.update_traces(texttemplate="%{y:.1f}", textposition="outside")
    return fig


def build_bed_occupancy_gauge(rate: float) -> go.Figure:
    """Gauge chart for Bed Occupancy Rate."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=rate,
        title={"text": "Bed Occupancy Rate"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": PRIMARY_COLOR},
            "steps": [
                {"range": [0, 60], "color": SUCCESS_COLOR},
                {"range": [60, 85], "color": WARNING_COLOR},
                {"range": [85, 100], "color": ACCENT_COLOR},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75, "value": 90
            }
        }
    ))
    fig.update_layout(height=350)
    return fig


def build_high_risk_table(data: pd.DataFrame) -> pd.DataFrame:
    """Returns a filtered dataframe of high-risk patients."""
    wd = _with_readmission_flag(data)
    hr = wd[wd["is_30_day_readmission"] == True].copy()
    if hr.empty:
        return hr
    hr = hr.sort_values(by="length_of_stay", ascending=False)
    columns_to_show = ["patient_nbr", "encounter_id", "department", "age_group", "length_of_stay"]
    available_cols = [c for c in columns_to_show if c in hr.columns]
    return hr[available_cols]


# ---------------------------------------------------------------------------
# 3. Main Dashboard Rendering
# ---------------------------------------------------------------------------

def render_patient_hospital_performance(data: pd.DataFrame) -> None:
    """
    Render the Patient & Hospital Performance executive dashboard.

    Args:
        data: Filtered hospital dashboard dataset.
    """
    st.markdown(
        """
        <div style="margin-bottom:0.3rem;">
            <span style="font-size:2rem;font-weight:700;color:#16324f;">
                🏥 Patient &amp; Hospital Performance
            </span>
        </div>
        <div style="font-size:0.98rem;color:#5f6f7f;margin-bottom:1.2rem;">
            Executive KPI Dashboard · Patient care, admissions &amp; hospital operations
        </div>
        """,
        unsafe_allow_html=True,
    )

    if data.empty:
        st.warning("No records match the selected filters.")
        return

    kpis = compute_kpis(data)
    if not kpis:
        st.warning("Unable to compute KPIs for the selected data.")
        return

    # --- KPI Cards Row ---
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(_kpi_card("Total Patients", f"{kpis['total_patients']:,}", "👥", PRIMARY_COLOR), unsafe_allow_html=True)
        st.markdown(_kpi_card("Total Encounters", f"{kpis['total_encounters']:,}", "🏥", SECONDARY_COLOR), unsafe_allow_html=True)
    with k2:
        st.markdown(_kpi_card("Readmission Rate", f"{kpis['readmission_rate']}%", "🔄", WARNING_COLOR), unsafe_allow_html=True)
        st.markdown(_kpi_card("Average Length of Stay", f"{kpis['alos']} Days", "🛏️", PRIMARY_COLOR), unsafe_allow_html=True)
    with k3:
        st.markdown(_kpi_card("Bed Occupancy Rate", f"{kpis['bed_occupancy']}%", "📊", ACCENT_COLOR), unsafe_allow_html=True)
        st.markdown(_kpi_card("High-Risk Patients", f"{kpis['high_risk_count']:,}", "⚠️", ACCENT_COLOR), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Charts Row 1 ---
    c1, c2 = st.columns([3, 2])
    with c1:
        fig_forecast = build_monthly_admissions_chart(data)
        if fig_forecast:
            st.plotly_chart(fig_forecast, width='stretch')
        else:
            st.info("Admission data unavailable for forecasting.")
    with c2:
        fig_gauge = build_bed_occupancy_gauge(kpis["bed_occupancy"])
        if fig_gauge:
            st.plotly_chart(fig_gauge, width='stretch')

    # --- Charts Row 2 ---
    st.markdown("#### Operational Metrics")
    fig_alos = build_alos_by_department_chart(data)
    if fig_alos:
        st.plotly_chart(fig_alos, width='stretch')

    # --- High-Risk Patient Table ---
    st.markdown("#### 🚨 High-Risk Patient Records")
    hr_table = build_high_risk_table(data)
    if not hr_table.empty:
        st.caption(f"Showing {len(hr_table):,} high-risk patient records (30-day readmission flag). Sorted by Length of Stay (descending).")
        st.dataframe(hr_table, width='stretch', hide_index=True)
        csv_bytes = hr_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download High-Risk Patient Report (CSV)",
            data=csv_bytes,
            file_name="high_risk_patients.csv",
            mime="text/csv",
        )
    else:
        st.info("No high-risk patient records found for the selected filters.")
