"""
Patient & Hospital Performance dashboard for the Executive KPI Dashboard.

Covers:
    - Total Patients, Readmission Rate, ALOS, Bed Occupancy Rate, Patient Satisfaction
    - Admission Forecasts (historical monthly trend + ARIMA & Prophet forecast overlay)
    - Readmission Rate Trend Over Time
    - High-Risk Patients table with download
    - Patient demographic breakdowns (age group, gender)
    - ALOS by Department
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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

# ---------------------------------------------------------------------------
# Paths to pre-trained forecast files
# ---------------------------------------------------------------------------
_DASHBOARD_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _DASHBOARD_DIR.parent.parent
_FORECAST_DIR = _PROJECT_ROOT / "models" / "admission_forecasting"
_MONTHLY_ADMISSIONS_PATH = _PROJECT_ROOT / "data" / "cleaned" / "monthly_admissions.csv"
_ARIMA_MONTHLY_PATH = _FORECAST_DIR / "arima_monthly_forecast.csv"
_PROPHET_DAILY_PATH = _FORECAST_DIR / "prophet_forecast_daily_future.csv"
_MODEL_COMPARISON_PATH = _FORECAST_DIR / "model_comparison.csv"


# ---------------------------------------------------------------------------
# KPI Computation
# ---------------------------------------------------------------------------

def compute_kpis(data: pd.DataFrame) -> dict:
    """Compute top-level KPIs for the Patient & Hospital Performance dashboard."""
    if data.empty:
        return {}

    wd = _with_readmission_flag(data)
    total_patients = int(wd["patient_nbr"].nunique())
    total_encounters = int(wd["encounter_id"].nunique())

    # Readmission Rate
    readmissions = int(wd["is_30_day_readmission"].sum())
    readmission_rate = (readmissions / total_encounters * 100) if total_encounters > 0 else 0.0

    # ALOS
    alos = 0.0
    if "length_of_stay" in wd.columns:
        los_num = pd.to_numeric(wd["length_of_stay"], errors="coerce")
        alos = _safe_round(los_num.mean(), 1)

    # Bed Occupancy — use real bed_occupancy column when available
    bed_occupancy_rate = 0.0
    if "bed_occupancy" in wd.columns:
        bed_num = pd.to_numeric(wd["bed_occupancy"], errors="coerce")
        bed_occupancy_rate = _safe_round(bed_num.mean(), 1)

    # Patient Satisfaction
    avg_satisfaction = 0.0
    if "patient_satisfaction" in wd.columns:
        sat_num = pd.to_numeric(wd["patient_satisfaction"], errors="coerce")
        avg_satisfaction = _safe_round(sat_num.mean(), 1)

    return {
        "total_patients": total_patients,
        "total_encounters": total_encounters,
        "readmission_rate": _safe_round(readmission_rate, 1),
        "readmissions": readmissions,
        "alos": alos,
        "bed_occupancy": bed_occupancy_rate,
        "high_risk_count": readmissions,
        "avg_satisfaction": avg_satisfaction,
    }


# ---------------------------------------------------------------------------
# KPI Card HTML helper
# ---------------------------------------------------------------------------

def _kpi_card(title: str, value: str | int | float, icon: str, color: str,
              subtitle: str = "") -> str:
    """HTML snippet for a consistent KPI card with an optional subtitle."""
    subtitle_html = (
        f'<div style="font-size:0.75rem;color:#8fa0b0;margin-top:4px;">{subtitle}</div>'
        if subtitle else ""
    )
    return f"""
    <div class="kpi-card" style="border-top:4px solid {color}; margin-bottom:12px;">
        <div style="font-size:1.5rem; color:{color};">{icon}</div>
        <div style="font-size:0.8rem; font-weight:600; color:#667788;
             margin:5px 0 3px;">{title}</div>
        <div style="font-size:1.65rem; font-weight:700; color:#16324f;">{value}</div>
        {subtitle_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Chart Builders
# ---------------------------------------------------------------------------

def _load_historical_monthly() -> pd.DataFrame | None:
    """Load the pre-aggregated monthly admissions CSV."""
    if not _MONTHLY_ADMISSIONS_PATH.exists():
        return None
    df = pd.read_csv(_MONTHLY_ADMISSIONS_PATH)
    df.columns = [c.strip() for c in df.columns]
    # Normalise column names
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    adm_col = next((c for c in df.columns if "admi" in c.lower()), None)
    if date_col is None or adm_col is None:
        return None
    df = df.rename(columns={date_col: "Date", adm_col: "Admissions"})
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date")
    return df


def _load_arima_monthly_forecast() -> pd.DataFrame | None:
    """Load ARIMA monthly forecast (future periods only)."""
    if not _ARIMA_MONTHLY_PATH.exists():
        return None
    df = pd.read_csv(_ARIMA_MONTHLY_PATH)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    # Keep only future months (date > last historical month)
    historical = _load_historical_monthly()
    if historical is not None:
        last_hist = historical["Date"].max()
        df = df[df["date"] > last_hist]
    return df if not df.empty else None


def _load_prophet_monthly_forecast() -> pd.DataFrame | None:
    """Aggregate the Prophet daily future forecast to monthly."""
    if not _PROPHET_DAILY_PATH.exists():
        return None
    df = pd.read_csv(_PROPHET_DAILY_PATH)
    df["ds"] = pd.to_datetime(df["ds"], errors="coerce")
    df = df.dropna(subset=["ds"])
    if df.empty:
        return None
    # Aggregate daily → monthly
    df["month"] = df["ds"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("month", as_index=False).agg(
        yhat=("yhat", "sum"),
        yhat_lower=("yhat_lower", "sum"),
        yhat_upper=("yhat_upper", "sum"),
    )
    historical = _load_historical_monthly()
    if historical is not None:
        last_hist = historical["Date"].max()
        monthly = monthly[monthly["month"] > last_hist]
    return monthly if not monthly.empty else None


def build_admission_forecast_chart(data: pd.DataFrame) -> go.Figure | None:
    """
    Build the admission trend + ARIMA & Prophet forecast chart.
    Uses the pre-trained forecast CSVs when available; falls back to linear
    regression over the filtered dataset if not.
    """
    historical = _load_historical_monthly()
    arima_fc = _load_arima_monthly_forecast()
    prophet_fc = _load_prophet_monthly_forecast()

    fig = go.Figure()

    if historical is not None and not historical.empty:
        # Full historical series from the cleaned CSV
        fig.add_trace(go.Scatter(
            x=historical["Date"],
            y=historical["Admissions"],
            mode="lines+markers",
            name="Historical Admissions",
            line=dict(color=PRIMARY_COLOR, width=2.5),
            marker=dict(size=4),
        ))

        if arima_fc is not None:
            fig.add_trace(go.Scatter(
                x=arima_fc["date"],
                y=arima_fc["arima_forecast"].round(0),
                mode="lines+markers",
                name="ARIMA Forecast",
                line=dict(color=ACCENT_COLOR, width=2.5, dash="dash"),
                marker=dict(symbol="diamond", size=8),
            ))

        if prophet_fc is not None:
            fig.add_trace(go.Scatter(
                x=prophet_fc["month"],
                y=prophet_fc["yhat"].round(0),
                mode="lines+markers",
                name="Prophet Forecast",
                line=dict(color=SUCCESS_COLOR, width=2.5, dash="dot"),
                marker=dict(symbol="square", size=7),
            ))
            # Confidence band
            fig.add_trace(go.Scatter(
                x=pd.concat([prophet_fc["month"], prophet_fc["month"][::-1]]),
                y=pd.concat([prophet_fc["yhat_upper"], prophet_fc["yhat_lower"][::-1]]),
                fill="toself",
                fillcolor="rgba(46,204,113,0.12)",
                line=dict(color="rgba(0,0,0,0)"),
                name="Prophet 95% CI",
                showlegend=True,
            ))

        title = "Monthly Admission History & ML Forecast (ARIMA + Prophet)"

    else:
        # Fallback: compute trend from filtered data using linear regression
        if "admission_date" not in data.columns:
            return None
        wd = data.copy()
        wd["admission_date"] = pd.to_datetime(wd["admission_date"], errors="coerce")
        wd = wd.dropna(subset=["admission_date"])
        if wd.empty:
            return None

        wd["month"] = wd["admission_date"].dt.to_period("M").dt.to_timestamp()
        monthly = wd.groupby("month").size().reset_index(name="admissions")

        from sklearn.linear_model import LinearRegression
        months_num = np.arange(len(monthly)).reshape(-1, 1)
        reg = LinearRegression().fit(months_num, monthly["admissions"].values)
        future_steps = 3
        future_num = np.arange(len(monthly) + future_steps).reshape(-1, 1)
        forecast_vals = reg.predict(future_num)

        last_date = monthly["month"].max()
        future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, future_steps + 1)]
        all_dates = list(monthly["month"]) + future_dates

        fig.add_trace(go.Scatter(
            x=monthly["month"], y=monthly["admissions"],
            mode="lines+markers", name="Admissions (Filtered)",
            line=dict(color=PRIMARY_COLOR, width=3),
        ))
        fig.add_trace(go.Scatter(
            x=all_dates, y=forecast_vals.round(0),
            mode="lines", name="Linear Regression Forecast",
            line=dict(color=ACCENT_COLOR, width=2, dash="dash"),
        ))
        title = "Admissions Trend & Forecast (Filtered Data — 3-Month Projection)"

    fig.update_layout(
        template=CHART_TEMPLATE,
        title=title,
        xaxis_title="Month",
        yaxis_title="Total Admissions",
        height=400,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.2),
        margin={"l": 10, "r": 10, "t": 55, "b": 60},
    )
    return fig


def build_readmission_trend_chart(data: pd.DataFrame) -> go.Figure | None:
    """Monthly readmission rate trend with a 3-month rolling average."""
    if "admission_date" not in data.columns or "readmitted" not in data.columns:
        return None
    wd = _with_readmission_flag(data).copy()
    wd["admission_date"] = pd.to_datetime(wd["admission_date"], errors="coerce")
    wd = wd.dropna(subset=["admission_date"])
    if wd.empty:
        return None

    wd["month"] = wd["admission_date"].dt.to_period("M").dt.to_timestamp()
    monthly = wd.groupby("month").agg(
        encounters=("encounter_id", "nunique"),
        readmissions=("is_30_day_readmission", "sum"),
    ).reset_index()
    monthly["readmission_rate"] = (monthly["readmissions"] / monthly["encounters"] * 100).round(1)
    monthly["rolling_avg"] = monthly["readmission_rate"].rolling(window=3, min_periods=1).mean().round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly["month"],
        y=monthly["readmission_rate"],
        name="Monthly Readmission Rate (%)",
        marker_color=WARNING_COLOR,
        opacity=0.6,
    ))
    fig.add_trace(go.Scatter(
        x=monthly["month"],
        y=monthly["rolling_avg"],
        mode="lines+markers",
        name="3-Month Rolling Avg",
        line=dict(color=PRIMARY_COLOR, width=2.5),
        marker=dict(size=5),
    ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="30-Day Readmission Rate Trend",
        xaxis_title="Month",
        yaxis_title="Readmission Rate (%)",
        height=320,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.25),
        margin={"l": 10, "r": 10, "t": 50, "b": 60},
    )
    return fig


def build_alos_by_department_chart(data: pd.DataFrame) -> go.Figure | None:
    """Horizontal bar chart for ALOS by department."""
    if "department" not in data.columns or "length_of_stay" not in data.columns:
        return None
    dept = (
        data.groupby("department", as_index=False)["length_of_stay"]
        .mean()
        .round(1)
        .sort_values("length_of_stay", ascending=True)
    )
    fig = px.bar(
        dept,
        y="department",
        x="length_of_stay",
        orientation="h",
        color="length_of_stay",
        color_continuous_scale="Blues",
        title="Average Length of Stay (Days) by Department",
        labels={"department": "Department", "length_of_stay": "ALOS (Days)"},
        text_auto=".1f",
    )
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=320,
        showlegend=False,
        coloraxis_showscale=False,
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
    )
    return fig


def build_bed_occupancy_gauge(rate: float) -> go.Figure:
    """Gauge chart for Bed Occupancy Rate."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=rate,
        title={"text": "Avg Bed Occupancy Rate (%)"},
        delta={"reference": 85, "suffix": "% vs 85% target"},
        gauge={
            "axis": {"range": [0, 100], "ticksuffix": "%"},
            "bar": {"color": PRIMARY_COLOR},
            "steps": [
                {"range": [0, 60], "color": SUCCESS_COLOR},
                {"range": [60, 85], "color": "#f39c12"},
                {"range": [85, 100], "color": WARNING_COLOR},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 90,
            },
        },
    ))
    fig.update_layout(height=300, margin={"l": 20, "r": 20, "t": 40, "b": 20})
    return fig


def build_patient_by_age_group_chart(data: pd.DataFrame) -> go.Figure | None:
    """Donut chart — patient count by age group."""
    age_col = "age_group" if "age_group" in data.columns else ("age" if "age" in data.columns else None)
    if age_col is None:
        return None
    wd = _with_readmission_flag(data)
    age_grp = (
        wd.groupby(age_col, as_index=False)
        .agg(patients=("patient_nbr", "nunique"))
        .sort_values(age_col)
    )
    fig = px.pie(
        age_grp,
        names=age_col,
        values="patients",
        title="Patient Distribution by Age Group",
        hole=0.42,
        color_discrete_sequence=px.colors.sequential.Blues[::-1],
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=320,
        showlegend=True,
        legend=dict(orientation="v", x=1.0, y=0.5),
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
    )
    return fig


def build_readmission_by_age_gender_chart(data: pd.DataFrame) -> go.Figure | None:
    """Grouped bar — readmission rate by age group and gender."""
    age_col = "age_group" if "age_group" in data.columns else ("age" if "age" in data.columns else None)
    if age_col is None or "gender" not in data.columns:
        return None

    wd = _with_readmission_flag(data)
    grp = (
        wd.groupby([age_col, "gender"], as_index=False)
        .agg(
            encounters=("encounter_id", "nunique"),
            readmissions=("is_30_day_readmission", "sum"),
        )
    )
    grp["readmission_rate"] = (grp["readmissions"] / grp["encounters"] * 100).round(1)
    grp = grp.sort_values(age_col)

    fig = px.bar(
        grp,
        x=age_col,
        y="readmission_rate",
        color="gender",
        barmode="group",
        title="30-Day Readmission Rate by Age Group & Gender",
        labels={
            age_col: "Age Group",
            "readmission_rate": "Readmission Rate (%)",
            "gender": "Gender",
        },
        color_discrete_sequence=[PRIMARY_COLOR, ACCENT_COLOR],
    )
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=320,
        xaxis_tickangle=-30,
        legend=dict(orientation="h", y=-0.3),
        margin={"l": 10, "r": 10, "t": 50, "b": 70},
    )
    return fig


def build_high_risk_table(data: pd.DataFrame) -> pd.DataFrame:
    """Return a filtered dataframe of high-risk (30-day readmission) patients."""
    wd = _with_readmission_flag(data)
    hr = wd[wd["is_30_day_readmission"]].copy()
    if hr.empty:
        return hr
    hr = hr.sort_values(by="length_of_stay", ascending=False)
    # Include age/age_group, gender, satisfaction if available
    preferred_cols = [
        "patient_nbr", "encounter_id", "department",
        "age_group", "age", "gender",
        "length_of_stay", "patient_satisfaction",
    ]
    available_cols = [c for c in preferred_cols if c in hr.columns]
    return hr[available_cols].reset_index(drop=True)


def _load_model_comparison() -> pd.DataFrame | None:
    """Load the model performance comparison CSV."""
    if not _MODEL_COMPARISON_PATH.exists():
        return None
    df = pd.read_csv(_MODEL_COMPARISON_PATH)
    return df


# ---------------------------------------------------------------------------
# Main Dashboard Rendering
# ---------------------------------------------------------------------------

def render_patient_hospital_performance(data: pd.DataFrame) -> None:
    """
    Render the Patient & Hospital Performance executive dashboard.

    Args:
        data: Filtered hospital dashboard dataset (from app.py).
    """
    st.markdown(
        """
        <div style="margin-bottom:0.3rem;">
            <span style="font-size:2rem; font-weight:700; color:#16324f;">
                🏥 Patient &amp; Hospital Performance
            </span>
        </div>
        <div style="font-size:0.98rem; color:#5f6f7f; margin-bottom:0.4rem;">
            Executive KPI Dashboard · Patient care, admissions &amp; hospital operations
        </div>
        <hr style="border-color:#d6e0e9; margin-bottom:1.2rem;">
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

    # -----------------------------------------------------------------------
    # Section 1 — KPI Cards (2 rows × 4 columns)
    # -----------------------------------------------------------------------
    st.markdown("#### 📊 Key Performance Indicators")
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        st.markdown(
            _kpi_card("Total Patients", f"{kpis['total_patients']:,}", "👥", PRIMARY_COLOR,
                      "Unique patient count"),
            unsafe_allow_html=True,
        )
    with r1c2:
        st.markdown(
            _kpi_card("Total Encounters", f"{kpis['total_encounters']:,}", "🏥", SECONDARY_COLOR,
                      "All hospital visits"),
            unsafe_allow_html=True,
        )
    with r1c3:
        st.markdown(
            _kpi_card("30-Day Readmission Rate", f"{kpis['readmission_rate']}%", "🔄",
                      WARNING_COLOR, f"{kpis['readmissions']:,} readmissions"),
            unsafe_allow_html=True,
        )
    with r1c4:
        st.markdown(
            _kpi_card("High-Risk Patients", f"{kpis['high_risk_count']:,}", "⚠️",
                      "#e74c3c", "30-day readmission flag"),
            unsafe_allow_html=True,
        )

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        st.markdown(
            _kpi_card("Avg Length of Stay", f"{kpis['alos']} Days", "🛏️", PRIMARY_COLOR,
                      "Per encounter"),
            unsafe_allow_html=True,
        )
    with r2c2:
        st.markdown(
            _kpi_card("Avg Bed Occupancy", f"{kpis['bed_occupancy']}%", "📊", ACCENT_COLOR,
                      "Based on bed_occupancy column"),
            unsafe_allow_html=True,
        )
    with r2c3:
        st.markdown(
            _kpi_card("Patient Satisfaction", f"{kpis['avg_satisfaction']} / 5", "⭐",
                      SUCCESS_COLOR, "Average score"),
            unsafe_allow_html=True,
        )
    with r2c4:
        enc_per_pt = _safe_round(kpis["total_encounters"] / max(kpis["total_patients"], 1), 2)
        st.markdown(
            _kpi_card("Encounters / Patient", str(enc_per_pt), "🔢", NEUTRAL_COLOR,
                      "Visit frequency"),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Section 2 — Admission Forecast + Bed Occupancy Gauge
    # -----------------------------------------------------------------------
    st.markdown("#### 📈 Admission Trends & Forecast")
    chart_col, gauge_col = st.columns([3, 2])
    with chart_col:
        fig_forecast = build_admission_forecast_chart(data)
        if fig_forecast:
            st.plotly_chart(fig_forecast, width="stretch")
        else:
            st.info("Admission data unavailable for forecasting.")

        # Show model performance info if available
        model_df = _load_model_comparison()
        if model_df is not None:
            with st.expander("📋 Forecast Model Performance Metrics"):
                st.dataframe(model_df, hide_index=True, width="stretch")
                st.caption(
                    "ARIMA and Prophet models were trained on daily historical admissions. "
                    "Monthly forecasts are aggregated from the daily outputs."
                )

    with gauge_col:
        fig_gauge = build_bed_occupancy_gauge(kpis["bed_occupancy"])
        st.plotly_chart(fig_gauge, width="stretch")

        # Readmission trend below the gauge
        fig_readm_trend = build_readmission_trend_chart(data)
        if fig_readm_trend:
            st.plotly_chart(fig_readm_trend, width="stretch")

    # -----------------------------------------------------------------------
    # Section 3 — Operational Metrics
    # -----------------------------------------------------------------------
    st.markdown("#### 🏢 Operational Metrics")
    op_col1, op_col2 = st.columns(2)

    with op_col1:
        fig_alos = build_alos_by_department_chart(data)
        if fig_alos:
            st.plotly_chart(fig_alos, width="stretch")

    with op_col2:
        fig_age = build_patient_by_age_group_chart(data)
        if fig_age:
            st.plotly_chart(fig_age, width="stretch")

    # Readmission by age group & gender
    fig_readm_demo = build_readmission_by_age_gender_chart(data)
    if fig_readm_demo:
        st.plotly_chart(fig_readm_demo, width="stretch")

    # -----------------------------------------------------------------------
    # Section 4 — High-Risk Patient Records
    # -----------------------------------------------------------------------
    st.markdown("#### 🚨 High-Risk Patient Records")
    hr_table = build_high_risk_table(data)
    if not hr_table.empty:
        st.caption(
            f"Showing **{len(hr_table):,}** high-risk patient records "
            f"(30-day readmission flag). Sorted by Length of Stay ↓."
        )
        st.dataframe(hr_table, width="stretch", hide_index=True)
        csv_bytes = hr_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download High-Risk Patient Report (CSV)",
            data=csv_bytes,
            file_name="high_risk_patients.csv",
            mime="text/csv",
            key="phd_high_risk_download",
        )
    else:
        st.info("No high-risk patient records found for the selected filters.")
