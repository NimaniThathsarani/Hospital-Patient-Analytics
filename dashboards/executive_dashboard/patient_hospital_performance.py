"""
Patient & Hospital Performance dashboard for the Executive KPI Dashboard.

Sub-pages (st.tabs):
    1. Total Patients           — volume, age/gender breakdown, monthly trend
    2. Readmission Rate         — monthly trend, age/gender/dept breakdown
    3. Avg Length of Stay       — ALOS KPIs, by-dept bar, LOS distribution
    4. Bed Occupancy Rate       — gauge, monthly trend, by-dept bar
    5. Admission Forecasts      — ARIMA + Prophet ML charts, model comparison
    6. High-Risk Patients       — risk breakdown charts, ranked patient table
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
# Forecast file paths
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

    readmissions = int(wd["is_30_day_readmission"].sum())
    readmission_rate = (readmissions / total_encounters * 100) if total_encounters > 0 else 0.0

    alos = 0.0
    if "length_of_stay" in wd.columns:
        los_num = pd.to_numeric(wd["length_of_stay"], errors="coerce")
        alos = _safe_round(los_num.mean(), 1)

    bed_occupancy_rate = 0.0
    if "bed_occupancy" in wd.columns:
        bed_num = pd.to_numeric(wd["bed_occupancy"], errors="coerce")
        bed_occupancy_rate = _safe_round(bed_num.mean(), 1)

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
# Shared KPI Card Helper
# ---------------------------------------------------------------------------

def _kpi_card(
    title: str,
    value: str | int | float,
    icon: str,
    color: str,
    subtitle: str = "",
) -> str:
    """HTML snippet for a consistent KPI card with an optional subtitle."""
    subtitle_html = (
        f'<div style="font-size:0.75rem;color:#8fa0b0;margin-top:4px;">{subtitle}</div>'
        if subtitle
        else ""
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


def _section_header(title: str, subtitle: str) -> None:
    """Render a consistent section header."""
    st.markdown(
        f"""
        <div style="font-size:1.3rem; font-weight:700; color:#16324f;
             margin:0.6rem 0 0.2rem;">{title}</div>
        <div style="font-size:0.9rem; color:#5f6f7f; margin-bottom:1rem;">
            {subtitle}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Forecast Data Loaders (shared across tabs)
# ---------------------------------------------------------------------------

def _load_historical_monthly() -> pd.DataFrame | None:
    """Load the pre-aggregated monthly admissions CSV."""
    if not _MONTHLY_ADMISSIONS_PATH.exists():
        return None
    df = pd.read_csv(_MONTHLY_ADMISSIONS_PATH)
    df.columns = [c.strip() for c in df.columns]
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


def _load_model_comparison() -> pd.DataFrame | None:
    """Load the model performance comparison CSV."""
    if not _MODEL_COMPARISON_PATH.exists():
        return None
    return pd.read_csv(_MODEL_COMPARISON_PATH)


# ---------------------------------------------------------------------------
# Shared Chart Builders
# ---------------------------------------------------------------------------

def build_admission_forecast_chart(data: pd.DataFrame) -> go.Figure | None:
    """Build the admission trend + ARIMA & Prophet forecast chart."""
    historical = _load_historical_monthly()
    arima_fc = _load_arima_monthly_forecast()
    prophet_fc = _load_prophet_monthly_forecast()

    fig = go.Figure()

    if historical is not None and not historical.empty:
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
        height=420,
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
    monthly["readmission_rate"] = (
        monthly["readmissions"] / monthly["encounters"] * 100
    ).round(1)
    monthly["rolling_avg"] = (
        monthly["readmission_rate"].rolling(window=3, min_periods=1).mean().round(1)
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly["month"],
        y=monthly["readmission_rate"],
        name="Monthly Readmission Rate (%)",
        marker_color=WARNING_COLOR,
        opacity=0.65,
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
        title="30-Day Readmission Rate — Monthly Trend",
        xaxis_title="Month",
        yaxis_title="Readmission Rate (%)",
        height=360,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.25),
        margin={"l": 10, "r": 10, "t": 50, "b": 65},
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
        height=360,
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
    fig.update_layout(height=320, margin={"l": 20, "r": 20, "t": 40, "b": 20})
    return fig


def build_patient_by_age_group_chart(data: pd.DataFrame) -> go.Figure | None:
    """Donut chart — patient count by age group."""
    age_col = (
        "age_group"
        if "age_group" in data.columns
        else ("age" if "age" in data.columns else None)
    )
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
        height=360,
        showlegend=True,
        legend=dict(orientation="v", x=1.0, y=0.5),
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
    )
    return fig


def build_readmission_by_age_gender_chart(data: pd.DataFrame) -> go.Figure | None:
    """Grouped bar — readmission rate by age group and gender."""
    age_col = (
        "age_group"
        if "age_group" in data.columns
        else ("age" if "age" in data.columns else None)
    )
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
        height=360,
        xaxis_tickangle=-30,
        legend=dict(orientation="h", y=-0.3),
        margin={"l": 10, "r": 10, "t": 50, "b": 75},
    )
    return fig


def build_high_risk_table(data: pd.DataFrame) -> pd.DataFrame:
    """Return a filtered dataframe of high-risk (30-day readmission) patients."""
    wd = _with_readmission_flag(data)
    hr = wd[wd["is_30_day_readmission"]].copy()
    if hr.empty:
        return hr
    hr = hr.sort_values(by="length_of_stay", ascending=False)
    preferred_cols = [
        "patient_nbr", "encounter_id", "department",
        "age_group", "age", "gender",
        "length_of_stay", "patient_satisfaction",
    ]
    available_cols = [c for c in preferred_cols if c in hr.columns]
    return hr[available_cols].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Tab 1 — Total Patients
# ---------------------------------------------------------------------------

def _render_total_patients(data: pd.DataFrame, kpis: dict) -> None:
    """Render the Total Patients sub-page."""
    _section_header(
        "👥 Total Patients",
        "Patient volume, demographics, and monthly admission trends.",
    )

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            _kpi_card(
                "Total Unique Patients", f"{kpis['total_patients']:,}",
                "👥", PRIMARY_COLOR, "Unique patient count",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            _kpi_card(
                "Total Encounters", f"{kpis['total_encounters']:,}",
                "🏥", SECONDARY_COLOR, "All hospital visits",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        enc_per_pt = _safe_round(
            kpis["total_encounters"] / max(kpis["total_patients"], 1), 2
        )
        st.markdown(
            _kpi_card(
                "Encounters / Patient", str(enc_per_pt),
                "🔢", NEUTRAL_COLOR, "Visit frequency",
            ),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            _kpi_card(
                "Patient Satisfaction", f"{kpis['avg_satisfaction']} / 5",
                "⭐", SUCCESS_COLOR, "Average score",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Age group & gender breakdown
    col_age, col_gender = st.columns(2)

    with col_age:
        fig_age = build_patient_by_age_group_chart(data)
        if fig_age:
            st.plotly_chart(fig_age, use_container_width=True)
        else:
            st.info("Age group data not available.")

    with col_gender:
        if "gender" in data.columns:
            gender_counts = (
                data.groupby("gender", as_index=False)
                .agg(patients=("patient_nbr", "nunique"))
            )
            fig_gender = px.bar(
                gender_counts,
                x="gender",
                y="patients",
                color="gender",
                title="Unique Patients by Gender",
                labels={"gender": "Gender", "patients": "Unique Patients"},
                color_discrete_sequence=[PRIMARY_COLOR, ACCENT_COLOR],
                text_auto=True,
            )
            fig_gender.update_layout(
                template=CHART_TEMPLATE,
                height=360,
                showlegend=False,
                margin={"l": 10, "r": 10, "t": 50, "b": 10},
            )
            st.plotly_chart(fig_gender, use_container_width=True)
        else:
            st.info("Gender data not available.")

    # Monthly admission trend
    if "admission_date" in data.columns:
        st.markdown("##### Monthly Patient Admission Trend")
        wd = data.copy()
        wd["admission_date"] = pd.to_datetime(wd["admission_date"], errors="coerce")
        wd = wd.dropna(subset=["admission_date"])
        if not wd.empty:
            wd["month"] = wd["admission_date"].dt.to_period("M").dt.to_timestamp()
            monthly = (
                wd.groupby("month", as_index=False)
                .agg(
                    unique_patients=("patient_nbr", "nunique"),
                    total_encounters=("encounter_id", "nunique"),
                )
            )
            fig_monthly = go.Figure()
            fig_monthly.add_trace(go.Bar(
                x=monthly["month"],
                y=monthly["unique_patients"],
                name="Unique Patients",
                marker_color=PRIMARY_COLOR,
                opacity=0.8,
            ))
            fig_monthly.add_trace(go.Scatter(
                x=monthly["month"],
                y=monthly["total_encounters"],
                mode="lines+markers",
                name="Total Encounters",
                line=dict(color=ACCENT_COLOR, width=2.5),
                yaxis="y2",
            ))
            fig_monthly.update_layout(
                template=CHART_TEMPLATE,
                title="Monthly Unique Patients & Encounters",
                xaxis_title="Month",
                yaxis=dict(title="Unique Patients"),
                yaxis2=dict(
                    title="Total Encounters",
                    overlaying="y",
                    side="right",
                    showgrid=False,
                ),
                legend=dict(orientation="h", y=-0.2),
                height=400,
                hovermode="x unified",
                margin={"l": 10, "r": 60, "t": 50, "b": 60},
            )
            st.plotly_chart(fig_monthly, use_container_width=True)

    # Top departments by patient volume
    if "department" in data.columns:
        st.markdown("##### Patient Volume by Department")
        dept_vol = (
            data.groupby("department", as_index=False)
            .agg(
                unique_patients=("patient_nbr", "nunique"),
                total_encounters=("encounter_id", "nunique"),
            )
            .sort_values("unique_patients", ascending=False)
        )
        fig_dept = px.bar(
            dept_vol,
            x="department",
            y="unique_patients",
            color="total_encounters",
            color_continuous_scale="Blues",
            title="Unique Patients per Department (colour = encounters)",
            labels={
                "department": "Department",
                "unique_patients": "Unique Patients",
                "total_encounters": "Total Encounters",
            },
            text_auto=True,
        )
        fig_dept.update_layout(
            template=CHART_TEMPLATE,
            height=380,
            xaxis_tickangle=-30,
            coloraxis_showscale=True,
            margin={"l": 10, "r": 10, "t": 50, "b": 70},
        )
        st.plotly_chart(fig_dept, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 2 — Readmission Rate
# ---------------------------------------------------------------------------

def _render_readmission_rate(data: pd.DataFrame, kpis: dict) -> None:
    """Render the Readmission Rate sub-page."""
    _section_header(
        "🔄 Readmission Rate",
        "30-day readmission analytics broken down by time, demographics, and department.",
    )

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            _kpi_card(
                "30-Day Readmission Rate", f"{kpis['readmission_rate']}%",
                "🔄", WARNING_COLOR, "Of all encounters",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            _kpi_card(
                "Total Readmissions", f"{kpis['readmissions']:,}",
                "📋", SECONDARY_COLOR, "Flagged encounters",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        non_readm = kpis["total_encounters"] - kpis["readmissions"]
        st.markdown(
            _kpi_card(
                "Non-Readmitted", f"{non_readm:,}",
                "✅", SUCCESS_COLOR, "Encounters",
            ),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            _kpi_card(
                "Total Encounters", f"{kpis['total_encounters']:,}",
                "🏥", NEUTRAL_COLOR, "Basis for rate",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Monthly trend chart
    fig_trend = build_readmission_trend_chart(data)
    if fig_trend:
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Readmission trend data is not available for the selected filters.")

    # Age/gender & department breakdown side by side
    col_demo, col_dept = st.columns(2)

    with col_demo:
        fig_demo = build_readmission_by_age_gender_chart(data)
        if fig_demo:
            st.plotly_chart(fig_demo, use_container_width=True)
        else:
            st.info("Age / gender data not available.")

    with col_dept:
        if "department" in data.columns and "readmitted" in data.columns:
            wd = _with_readmission_flag(data)
            dept_readm = (
                wd.groupby("department", as_index=False)
                .agg(
                    encounters=("encounter_id", "nunique"),
                    readmissions=("is_30_day_readmission", "sum"),
                )
            )
            dept_readm["readmission_rate"] = (
                dept_readm["readmissions"] / dept_readm["encounters"] * 100
            ).round(1)
            dept_readm = dept_readm.sort_values("readmission_rate", ascending=True)

            fig_dept_readm = px.bar(
                dept_readm,
                y="department",
                x="readmission_rate",
                orientation="h",
                color="readmission_rate",
                color_continuous_scale="RdYlGn_r",
                title="30-Day Readmission Rate by Department",
                labels={
                    "department": "Department",
                    "readmission_rate": "Readmission Rate (%)",
                },
                text_auto=".1f",
            )
            fig_dept_readm.update_layout(
                template=CHART_TEMPLATE,
                height=360,
                coloraxis_showscale=False,
                margin={"l": 10, "r": 10, "t": 50, "b": 10},
            )
            st.plotly_chart(fig_dept_readm, use_container_width=True)
        else:
            st.info("Department data not available.")

    # Readmission distribution pie
    st.markdown("##### Readmission Status Breakdown")
    if "readmitted" in data.columns:
        # Build a clean DataFrame directly to avoid narwhals DuplicateError
        # caused by pandas value_counts() producing a "count" column that
        # conflicts with rename operations across different pandas versions.
        _status_series = data["readmitted"].astype(str)
        _counts = _status_series.groupby(_status_series).count()
        readm_counts = pd.DataFrame({
            "status": _counts.index.tolist(),
            "count": _counts.values.tolist(),
        })

        fig_pie = px.pie(
            readm_counts,
            names="status",
            values="count",
            title="Readmission Status Distribution",
            hole=0.4,
            color_discrete_sequence=[WARNING_COLOR, SUCCESS_COLOR, SECONDARY_COLOR],
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(
            template=CHART_TEMPLATE,
            height=360,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Download
    if "readmitted" in data.columns:
        wd = _with_readmission_flag(data)
        readm_df = wd[wd["is_30_day_readmission"]].copy()
        if not readm_df.empty:
            st.download_button(
                label="📥 Download Readmission Records (CSV)",
                data=readm_df.to_csv(index=False).encode("utf-8"),
                file_name="readmission_records.csv",
                mime="text/csv",
                key="readm_rate_download",
            )


# ---------------------------------------------------------------------------
# Tab 3 — Average Length of Stay
# ---------------------------------------------------------------------------

def _render_alos(data: pd.DataFrame, kpis: dict) -> None:
    """Render the Average Length of Stay sub-page."""
    _section_header(
        "🛏️ Average Length of Stay (ALOS)",
        "Length-of-stay KPIs, department comparison, and distribution analysis.",
    )

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            _kpi_card(
                "Overall ALOS", f"{kpis['alos']} Days",
                "🛏️", PRIMARY_COLOR, "Average across all encounters",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        if "length_of_stay" in data.columns:
            los_num = pd.to_numeric(data["length_of_stay"], errors="coerce").dropna()
            median_los = _safe_round(los_num.median(), 1)
        else:
            median_los = 0.0
        st.markdown(
            _kpi_card(
                "Median LOS", f"{median_los} Days",
                "📊", SECONDARY_COLOR, "50th percentile",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        if "length_of_stay" in data.columns:
            max_los = _safe_round(los_num.max(), 1) if "los_num" in dir() else 0.0
        else:
            max_los = 0.0
        st.markdown(
            _kpi_card(
                "Max LOS", f"{max_los} Days",
                "⬆️", WARNING_COLOR, "Longest stay",
            ),
            unsafe_allow_html=True,
        )
    with c4:
        if "length_of_stay" in data.columns:
            p90_los = _safe_round(
                pd.to_numeric(data["length_of_stay"], errors="coerce").quantile(0.9), 1
            )
        else:
            p90_los = 0.0
        st.markdown(
            _kpi_card(
                "90th Percentile LOS", f"{p90_los} Days",
                "📈", ACCENT_COLOR, "Upper tail",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Department ALOS bar + LOS distribution side by side
    col_dept, col_hist = st.columns(2)

    with col_dept:
        fig_alos = build_alos_by_department_chart(data)
        if fig_alos:
            st.plotly_chart(fig_alos, use_container_width=True)
        else:
            st.info("Department / LOS data not available.")

    with col_hist:
        if "length_of_stay" in data.columns:
            los_vals = pd.to_numeric(data["length_of_stay"], errors="coerce").dropna()
            fig_hist = px.histogram(
                x=los_vals,
                nbins=25,
                color_discrete_sequence=[SECONDARY_COLOR],
                title="LOS Frequency Distribution",
                labels={"x": "Length of Stay (Days)", "y": "Encounters"},
            )
            fig_hist.update_layout(
                template=CHART_TEMPLATE,
                height=360,
                bargap=0.05,
                margin={"l": 10, "r": 10, "t": 50, "b": 10},
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Length of stay data not available.")

    # Box plot by department
    if "department" in data.columns and "length_of_stay" in data.columns:
        st.markdown("##### LOS Distribution by Department")
        fig_box = px.box(
            data.dropna(subset=["length_of_stay"]),
            x="department",
            y="length_of_stay",
            color="department",
            title="Length of Stay Distribution per Department",
            labels={"department": "Department", "length_of_stay": "LOS (Days)"},
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_box.update_layout(
            template=CHART_TEMPLATE,
            height=380,
            showlegend=False,
            xaxis_tickangle=-30,
            margin={"l": 10, "r": 10, "t": 50, "b": 70},
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # LOS vs Patient Satisfaction scatter
    if "length_of_stay" in data.columns and "patient_satisfaction" in data.columns:
        st.markdown("##### LOS vs Patient Satisfaction")
        scatter_df = data[["length_of_stay", "patient_satisfaction"]].copy()
        scatter_df["length_of_stay"] = pd.to_numeric(
            scatter_df["length_of_stay"], errors="coerce"
        )
        scatter_df["patient_satisfaction"] = pd.to_numeric(
            scatter_df["patient_satisfaction"], errors="coerce"
        )
        scatter_df = scatter_df.dropna()

        color_col = None
        color_label = None
        if "department" in data.columns:
            scatter_df["department"] = data.loc[scatter_df.index, "department"]
            color_col = "department"
            color_label = "Department"

        fig_scatter = px.scatter(
            scatter_df,
            x="length_of_stay",
            y="patient_satisfaction",
            color=color_col,
            opacity=0.55,
            title="Length of Stay vs Patient Satisfaction",
            labels={
                "length_of_stay": "LOS (Days)",
                "patient_satisfaction": "Patient Satisfaction",
                **({color_col: color_label} if color_col else {}),
            },
        )
        # Add a manual linear trend line using numpy (no statsmodels required)
        _x = scatter_df["length_of_stay"].values
        _y = scatter_df["patient_satisfaction"].values
        _mask = np.isfinite(_x) & np.isfinite(_y)
        if _mask.sum() > 1:
            _m, _b = np.polyfit(_x[_mask], _y[_mask], 1)
            _x_line = np.linspace(_x[_mask].min(), _x[_mask].max(), 100)
            fig_scatter.add_trace(go.Scatter(
                x=_x_line,
                y=_m * _x_line + _b,
                mode="lines",
                name="Trend",
                line=dict(color=WARNING_COLOR, width=2, dash="dash"),
                showlegend=True,
            ))
        fig_scatter.update_layout(
            template=CHART_TEMPLATE,
            height=380,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
        )
        st.plotly_chart(fig_scatter, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 4 — Bed Occupancy Rate
# ---------------------------------------------------------------------------

def _render_bed_occupancy(data: pd.DataFrame, kpis: dict) -> None:
    """Render the Bed Occupancy Rate sub-page."""
    _section_header(
        "🏥 Bed Occupancy Rate",
        "Current occupancy levels, monthly trends, and department-level breakdown.",
    )

    # KPI row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            _kpi_card(
                "Avg Bed Occupancy", f"{kpis['bed_occupancy']}%",
                "🏥", PRIMARY_COLOR, "Across all encounters",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        status_color = (
            WARNING_COLOR if kpis["bed_occupancy"] >= 85
            else (SUCCESS_COLOR if kpis["bed_occupancy"] < 60 else ACCENT_COLOR)
        )
        status_text = (
            "⚠️ High" if kpis["bed_occupancy"] >= 85
            else ("✅ Normal" if kpis["bed_occupancy"] < 60 else "🟡 Moderate")
        )
        st.markdown(
            _kpi_card(
                "Occupancy Status", status_text,
                "📊", status_color, "85% is alert threshold",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            _kpi_card(
                "Total Encounters", f"{kpis['total_encounters']:,}",
                "📋", SECONDARY_COLOR, "Volume driver",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Gauge + monthly trend side by side
    col_gauge, col_trend = st.columns([2, 3])

    with col_gauge:
        fig_gauge = build_bed_occupancy_gauge(kpis["bed_occupancy"])
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Threshold legend
        st.markdown(
            """
            <div style="font-size:0.82rem; margin-top:0.5rem; line-height:1.8;">
                <span style="color:#2ecc71;">■</span> <b>0–60%</b> — Low utilisation<br>
                <span style="color:#f39c12;">■</span> <b>60–85%</b> — Normal range<br>
                <span style="color:#e74c3c;">■</span> <b>85–100%</b> — High / Critical<br>
                <span style="color:red;">|</span> <b>90%</b> — Alert threshold
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_trend:
        if "bed_occupancy" in data.columns and "admission_date" in data.columns:
            wd = data.copy()
            wd["admission_date"] = pd.to_datetime(wd["admission_date"], errors="coerce")
            wd["bed_occupancy"] = pd.to_numeric(wd["bed_occupancy"], errors="coerce")
            dated = wd.dropna(subset=["admission_date", "bed_occupancy"])
            if not dated.empty:
                dated["month"] = (
                    dated["admission_date"].dt.to_period("M").dt.to_timestamp()
                )
                monthly_occ = (
                    dated.groupby("month", as_index=False)["bed_occupancy"]
                    .mean()
                    .round(1)
                )
                monthly_occ.rename(
                    columns={"bed_occupancy": "avg_bed_occupancy"}, inplace=True
                )

                fig_occ = go.Figure()
                fig_occ.add_trace(go.Scatter(
                    x=monthly_occ["month"],
                    y=monthly_occ["avg_bed_occupancy"],
                    mode="lines+markers",
                    name="Avg Bed Occupancy (%)",
                    line=dict(color=PRIMARY_COLOR, width=3),
                    fill="tozeroy",
                    fillcolor="rgba(22,50,79,0.10)",
                ))
                fig_occ.add_hline(
                    y=85,
                    line_dash="dash",
                    line_color=WARNING_COLOR,
                    annotation_text="85% Alert Threshold",
                    annotation_position="top right",
                )
                fig_occ.add_hline(
                    y=90,
                    line_dash="dot",
                    line_color="red",
                    annotation_text="90% Critical",
                    annotation_position="top left",
                )
                fig_occ.update_layout(
                    template=CHART_TEMPLATE,
                    title="Monthly Average Bed Occupancy (%)",
                    xaxis_title="Month",
                    yaxis_title="Avg Bed Occupancy (%)",
                    height=360,
                    hovermode="x unified",
                    margin={"l": 10, "r": 10, "t": 50, "b": 10},
                )
                st.plotly_chart(fig_occ, use_container_width=True)
            else:
                st.info("Insufficient data for monthly occupancy trend.")
        else:
            st.info("Bed occupancy or admission date data is not available.")

    # Department-level occupancy
    if "bed_occupancy" in data.columns and "department" in data.columns:
        st.markdown("##### Average Bed Occupancy by Department")
        bed_dept = (
            data.groupby("department", as_index=False)["bed_occupancy"]
            .mean()
            .round(1)
            .sort_values("bed_occupancy", ascending=False)
        )
        fig_bed_dept = px.bar(
            bed_dept,
            x="department",
            y="bed_occupancy",
            color="bed_occupancy",
            color_continuous_scale="RdYlGn_r",
            title="Avg Bed Occupancy (%) by Department",
            labels={
                "department": "Department",
                "bed_occupancy": "Avg Bed Occupancy (%)",
            },
            text_auto=".1f",
        )
        fig_bed_dept.add_hline(
            y=85,
            line_dash="dash",
            line_color=WARNING_COLOR,
            annotation_text="85% Alert",
        )
        fig_bed_dept.update_layout(
            template=CHART_TEMPLATE,
            height=360,
            coloraxis_showscale=False,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
        )
        st.plotly_chart(fig_bed_dept, use_container_width=True)
    else:
        if "bed_occupancy" not in data.columns:
            st.info(
                "The `bed_occupancy` column is not present in the dataset. "
                "Gauge and trend charts show 0%."
            )


# ---------------------------------------------------------------------------
# Tab 5 — Admission Forecasts
# ---------------------------------------------------------------------------

def _render_admission_forecasts(data: pd.DataFrame) -> None:
    """Render the Admission Forecasts sub-page."""
    _section_header(
        "📈 Admission Forecasts",
        "ML-powered admission forecasting using ARIMA and Prophet models.",
    )

    # Forecast availability info
    has_arima = _ARIMA_MONTHLY_PATH.exists()
    has_prophet = _PROPHET_DAILY_PATH.exists()
    has_historical = _MONTHLY_ADMISSIONS_PATH.exists()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        state = "✅ Available" if has_historical else "❌ Not Found"
        color = SUCCESS_COLOR if has_historical else WARNING_COLOR
        st.markdown(
            _kpi_card("Historical Data", state, "📂", color, "monthly_admissions.csv"),
            unsafe_allow_html=True,
        )
    with col_b:
        state = "✅ Available" if has_arima else "❌ Not Found"
        color = SUCCESS_COLOR if has_arima else WARNING_COLOR
        st.markdown(
            _kpi_card("ARIMA Forecast", state, "📉", color, "arima_monthly_forecast.csv"),
            unsafe_allow_html=True,
        )
    with col_c:
        state = "✅ Available" if has_prophet else "❌ Not Found"
        color = SUCCESS_COLOR if has_prophet else WARNING_COLOR
        st.markdown(
            _kpi_card("Prophet Forecast", state, "🔮", color, "prophet_forecast_daily_future.csv"),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Main forecast chart
    fig_forecast = build_admission_forecast_chart(data)
    if fig_forecast:
        st.plotly_chart(fig_forecast, use_container_width=True)
    else:
        st.info("Admission date data is unavailable for forecasting.")

    # Model comparison table
    model_df = _load_model_comparison()
    if model_df is not None:
        st.markdown("##### Forecast Model Performance Metrics")
        with st.expander("📋 Show Model Comparison Table", expanded=True):
            st.dataframe(model_df, hide_index=True, use_container_width=True)
            st.caption(
                "ARIMA and Prophet models were trained on daily historical admissions. "
                "Monthly forecasts are aggregated from the daily outputs."
            )

    # ARIMA detailed chart if available
    arima_fc = _load_arima_monthly_forecast()
    prophet_fc = _load_prophet_monthly_forecast()

    if arima_fc is not None or prophet_fc is not None:
        st.markdown("##### Individual Model Forecasts")
        col_arima, col_prophet = st.columns(2)

        with col_arima:
            if arima_fc is not None:
                fig_a = px.line(
                    arima_fc,
                    x="date",
                    y="arima_forecast",
                    title="ARIMA Monthly Forecast",
                    labels={"date": "Month", "arima_forecast": "Predicted Admissions"},
                    markers=True,
                    color_discrete_sequence=[ACCENT_COLOR],
                )
                fig_a.update_layout(
                    template=CHART_TEMPLATE,
                    height=300,
                    margin={"l": 10, "r": 10, "t": 50, "b": 10},
                )
                st.plotly_chart(fig_a, use_container_width=True)
            else:
                st.info("ARIMA forecast file not found.")

        with col_prophet:
            if prophet_fc is not None:
                fig_p = go.Figure()
                fig_p.add_trace(go.Scatter(
                    x=pd.concat([prophet_fc["month"], prophet_fc["month"][::-1]]),
                    y=pd.concat([prophet_fc["yhat_upper"], prophet_fc["yhat_lower"][::-1]]),
                    fill="toself",
                    fillcolor="rgba(46,204,113,0.15)",
                    line=dict(color="rgba(0,0,0,0)"),
                    name="95% Confidence Interval",
                ))
                fig_p.add_trace(go.Scatter(
                    x=prophet_fc["month"],
                    y=prophet_fc["yhat"].round(0),
                    mode="lines+markers",
                    name="Prophet Forecast",
                    line=dict(color=SUCCESS_COLOR, width=2.5),
                    marker=dict(symbol="square", size=7),
                ))
                fig_p.update_layout(
                    template=CHART_TEMPLATE,
                    title="Prophet Monthly Forecast with CI",
                    xaxis_title="Month",
                    yaxis_title="Predicted Admissions",
                    height=300,
                    hovermode="x unified",
                    margin={"l": 10, "r": 10, "t": 50, "b": 10},
                )
                st.plotly_chart(fig_p, use_container_width=True)
            else:
                st.info("Prophet forecast file not found.")

    # Historical trend from dataset
    if "admission_date" in data.columns:
        st.markdown("##### Historical Monthly Admissions from Filtered Dataset")
        wd = data.copy()
        wd["admission_date"] = pd.to_datetime(wd["admission_date"], errors="coerce")
        wd = wd.dropna(subset=["admission_date"])
        if not wd.empty:
            wd["month"] = wd["admission_date"].dt.to_period("M").dt.to_timestamp()
            hist_monthly = wd.groupby("month").size().reset_index(name="admissions")
            fig_hist = px.area(
                hist_monthly,
                x="month",
                y="admissions",
                title="Filtered Data — Monthly Admissions",
                labels={"month": "Month", "admissions": "Admissions"},
                color_discrete_sequence=[PRIMARY_COLOR],
            )
            fig_hist.update_layout(
                template=CHART_TEMPLATE,
                height=300,
                margin={"l": 10, "r": 10, "t": 50, "b": 10},
            )
            st.plotly_chart(fig_hist, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 6 — High-Risk Patients
# ---------------------------------------------------------------------------

def _render_high_risk_patients(data: pd.DataFrame, kpis: dict) -> None:
    """Render the High-Risk Patients sub-page."""
    _section_header(
        "🚨 High-Risk Patients",
        "Patients flagged for 30-day readmission — risk breakdown and detailed records.",
    )

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            _kpi_card(
                "High-Risk Patients", f"{kpis['high_risk_count']:,}",
                "🚨", WARNING_COLOR, "30-day readmission flag",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        risk_pct = _safe_round(
            kpis["high_risk_count"] / max(kpis["total_encounters"], 1) * 100, 1
        )
        st.markdown(
            _kpi_card(
                "Risk Rate", f"{risk_pct}%",
                "⚠️", "#e74c3c", "Of total encounters",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        if "length_of_stay" in data.columns and "readmitted" in data.columns:
            wd_hr = _with_readmission_flag(data)
            hr_only = wd_hr[wd_hr["is_30_day_readmission"]]
            hr_avg_los = _safe_round(
                pd.to_numeric(hr_only["length_of_stay"], errors="coerce").mean(), 1
            )
        else:
            hr_avg_los = 0.0
        st.markdown(
            _kpi_card(
                "Avg LOS (High-Risk)", f"{hr_avg_los} Days",
                "🛏️", SECONDARY_COLOR, "High-risk encounters only",
            ),
            unsafe_allow_html=True,
        )
    with c4:
        if "patient_satisfaction" in data.columns and "readmitted" in data.columns:
            wd_hr2 = _with_readmission_flag(data)
            hr_only2 = wd_hr2[wd_hr2["is_30_day_readmission"]]
            hr_avg_sat = _safe_round(
                pd.to_numeric(hr_only2["patient_satisfaction"], errors="coerce").mean(), 1
            )
        else:
            hr_avg_sat = 0.0
        st.markdown(
            _kpi_card(
                "Avg Satisfaction (High-Risk)", f"{hr_avg_sat} / 5",
                "⭐", NEUTRAL_COLOR, "Satisfaction score",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    hr_table = build_high_risk_table(data)

    if hr_table.empty:
        st.info("No high-risk patient records found for the selected filters.")
        return

    # Risk breakdown charts
    col_age, col_dept = st.columns(2)

    with col_age:
        age_col = (
            "age_group"
            if "age_group" in hr_table.columns
            else ("age" if "age" in hr_table.columns else None)
        )
        if age_col:
            age_risk = (
                hr_table.groupby(age_col, as_index=False)
                .agg(high_risk_count=("patient_nbr", "nunique"))
                .sort_values(age_col)
            )
            fig_age_risk = px.bar(
                age_risk,
                x=age_col,
                y="high_risk_count",
                color="high_risk_count",
                color_continuous_scale="Reds",
                title="High-Risk Patients by Age Group",
                labels={
                    age_col: "Age Group",
                    "high_risk_count": "High-Risk Patients",
                },
                text_auto=True,
            )
            fig_age_risk.update_layout(
                template=CHART_TEMPLATE,
                height=340,
                coloraxis_showscale=False,
                xaxis_tickangle=-30,
                margin={"l": 10, "r": 10, "t": 50, "b": 70},
            )
            st.plotly_chart(fig_age_risk, use_container_width=True)
        else:
            st.info("Age data not available for breakdown.")

    with col_dept:
        if "department" in hr_table.columns:
            dept_risk = (
                hr_table.groupby("department", as_index=False)
                .agg(high_risk_count=("patient_nbr", "nunique"))
                .sort_values("high_risk_count", ascending=True)
            )
            fig_dept_risk = px.bar(
                dept_risk,
                y="department",
                x="high_risk_count",
                orientation="h",
                color="high_risk_count",
                color_continuous_scale="Reds",
                title="High-Risk Patients by Department",
                labels={
                    "department": "Department",
                    "high_risk_count": "High-Risk Patients",
                },
                text_auto=True,
            )
            fig_dept_risk.update_layout(
                template=CHART_TEMPLATE,
                height=340,
                coloraxis_showscale=False,
                margin={"l": 10, "r": 10, "t": 50, "b": 10},
            )
            st.plotly_chart(fig_dept_risk, use_container_width=True)
        else:
            st.info("Department data not available.")

    # Gender distribution of high-risk patients
    if "gender" in hr_table.columns:
        st.markdown("##### High-Risk Patients by Gender")
        gender_risk = (
            hr_table.groupby("gender", as_index=False)
            .agg(count=("patient_nbr", "nunique"))
        )
        fig_gender_risk = px.pie(
            gender_risk,
            names="gender",
            values="count",
            title="High-Risk Patient Gender Distribution",
            hole=0.4,
            color_discrete_sequence=[PRIMARY_COLOR, ACCENT_COLOR],
        )
        fig_gender_risk.update_traces(textposition="inside", textinfo="percent+label")
        fig_gender_risk.update_layout(
            template=CHART_TEMPLATE,
            height=320,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
        )
        st.plotly_chart(fig_gender_risk, use_container_width=True)

    # High-risk patient table
    st.markdown("##### High-Risk Patient Records")
    st.caption(
        f"Showing **{len(hr_table):,}** high-risk patient records "
        f"(30-day readmission flag). Sorted by Length of Stay ↓."
    )
    st.dataframe(hr_table, use_container_width=True, hide_index=True)

    # Download
    csv_bytes = hr_table.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download High-Risk Patient Report (CSV)",
        data=csv_bytes,
        file_name="high_risk_patients.csv",
        mime="text/csv",
        key="phd_high_risk_download",
    )


# ---------------------------------------------------------------------------
# Main Render Entry Point
# ---------------------------------------------------------------------------

def render_patient_hospital_performance(data: pd.DataFrame) -> None:
    """
    Render the Patient & Hospital Performance executive dashboard.

    Uses st.tabs() to provide 6 dedicated sub-pages:
        1. Total Patients
        2. Readmission Rate
        3. Avg Length of Stay
        4. Bed Occupancy Rate
        5. Admission Forecasts
        6. High-Risk Patients

    Args:
        data: Filtered hospital dashboard dataset passed from app.py.
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

    # 6 sub-page tabs — mirrors the pattern in performance_resource_analytics.py
    (
        tab_patients,
        tab_readmission,
        tab_alos,
        tab_bed,
        tab_forecast,
        tab_highrisk,
    ) = st.tabs([
        "👥 Total Patients",
        "🔄 Readmission Rate",
        "🛏️ Avg Length of Stay",
        "🏥 Bed Occupancy Rate",
        "📈 Admission Forecasts",
        "🚨 High-Risk Patients",
    ])

    with tab_patients:
        _render_total_patients(data, kpis)

    with tab_readmission:
        _render_readmission_rate(data, kpis)

    with tab_alos:
        _render_alos(data, kpis)

    with tab_bed:
        _render_bed_occupancy(data, kpis)

    with tab_forecast:
        _render_admission_forecasts(data)

    with tab_highrisk:
        _render_high_risk_patients(data, kpis)
