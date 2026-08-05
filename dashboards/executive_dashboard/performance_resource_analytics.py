"""
Performance & Resource Analytics dashboard for the Executive KPI Dashboard.

Covers:
    - Department Performance (encounters, ALOS, readmission rate, satisfaction)
    - Doctor Performance Summary (top doctors, scatter, ranked table)
    - Disease Distribution (top ICD-9 diagnosis codes, by department)
    - Resource Utilization (bed occupancy trend, LOS distribution, workload heatmap)
"""

from __future__ import annotations

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
    create_department_level_summary,
    create_doctor_level_summary,
    create_monthly_workload_summary,
    _with_readmission_flag,
    _safe_round,
)


# ICD-9 Disease Category Mapping

ICD9_CATEGORIES: dict[tuple[int, int], str] = {
    (1, 139): "Infectious & Parasitic Diseases",
    (140, 239): "Neoplasms",
    (240, 279): "Endocrine & Metabolic",
    (280, 289): "Blood Diseases",
    (290, 319): "Mental Disorders",
    (320, 389): "Nervous System",
    (390, 459): "Circulatory System",
    (460, 519): "Respiratory System",
    (520, 579): "Digestive System",
    (580, 629): "Genitourinary System",
    (630, 679): "Pregnancy & Childbirth",
    (680, 709): "Skin & Subcutaneous",
    (710, 739): "Musculoskeletal",
    (740, 759): "Congenital Anomalies",
    (760, 779): "Perinatal Conditions",
    (780, 799): "Symptoms & Ill-Defined",
    (800, 999): "Injury & Poisoning",
}


def _map_icd9_category(code) -> str:
    """
    Map an ICD-9 code to its disease category name.
    Accepts integers, floats, or strings (e.g. 250, 250.7, '250.7').
    Uses only the integer part for range matching.
    """
    try:
        # Convert string like '250.7' → 250 via float first
        code_int = int(float(str(code).strip()))
    except (TypeError, ValueError):
        return "Other / Unknown"
    for (lo, hi), label in ICD9_CATEGORIES.items():
        if lo <= code_int <= hi:
            return label
    return "Other / Unknown"


# ---------------------------------------------------------------------------
# KPI Helper Card
# ---------------------------------------------------------------------------

def _kpi_card(title: str, value: str, icon: str, color: str) -> str:
    """Return an HTML KPI card snippet."""
    return f"""
    <div class="kpi-card" style="border-top:4px solid {color}; margin-bottom:12px;">
        <div class="kpi-icon" style="color:{color}; font-size:1.6rem;">{icon}</div>
        <div class="kpi-title" style="font-size:0.82rem; font-weight:600;
             color:#667788; margin:6px 0 4px;">{title}</div>
        <div class="kpi-value" style="font-size:1.55rem; font-weight:700;
             color:#16324f;">{value}</div>
    </div>
    """


# ---------------------------------------------------------------------------
# 1. Department Performance
# ---------------------------------------------------------------------------

def _render_department_performance(data: pd.DataFrame) -> None:
    """Render the Department Performance section."""
    st.markdown(
        """
        <div style="font-size:1.3rem; font-weight:700; color:#16324f;
             margin:0.6rem 0 0.2rem;">🏢 Department Performance</div>
        <div style="font-size:0.9rem; color:#5f6f7f; margin-bottom:1rem;">
            Operational KPIs broken down by clinical department.
        </div>
        """,
        unsafe_allow_html=True,
    )

    dept_summary = create_department_level_summary(data)
    if dept_summary.empty:
        st.info("Department data is unavailable for the selected filters.")
        return

    # --- KPI headline row ---
    num_depts = dept_summary["department"].nunique()
    best_dept = dept_summary.loc[
        dept_summary["total_encounters"].idxmax(), "department"
    ]
    avg_readmission = _safe_round(dept_summary["readmission_rate"].mean(), 1)
    avg_satisfaction = _safe_round(dept_summary["average_satisfaction"].mean(), 1)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            _kpi_card("Active Departments", str(num_depts), "🏢", PRIMARY_COLOR),
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            _kpi_card("Busiest Department", best_dept, "📈", SECONDARY_COLOR),
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            _kpi_card("Avg Readmission Rate", f"{avg_readmission}%", "🔄", WARNING_COLOR),
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            _kpi_card("Avg Patient Satisfaction", f"{avg_satisfaction} / 5", "⭐", SUCCESS_COLOR),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Metric selector ---
    metric_options = {
        "Total Encounters": "total_encounters",
        "Unique Patients": "unique_patients",
        "Number of Doctors": "total_doctors",
        "Avg Length of Stay (Days)": "average_length_of_stay",
        "30-Day Readmission Rate (%)": "readmission_rate",
        "Average Patient Satisfaction": "average_satisfaction",
        "Patients per Doctor": "patients_per_doctor",
    }
    selected_label = st.selectbox(
        "Select metric to compare across departments",
        list(metric_options.keys()),
        key="exec_dept_metric_selector",
    )
    selected_col = metric_options[selected_label]

    col_chart, col_radar = st.columns([3, 2])

    with col_chart:
        sorted_dept = dept_summary.sort_values(selected_col, ascending=False)
        fig_bar = px.bar(
            sorted_dept,
            x="department",
            y=selected_col,
            color="department",
            title=f"{selected_label} by Department",
            labels={"department": "Department", selected_col: selected_label},
            text_auto=".2s",
        )
        fig_bar.update_layout(
            template=CHART_TEMPLATE,
            height=370,
            showlegend=False,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
        )
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, width="stretch")

    with col_radar:
        # Radar / spider chart for multi-metric dept comparison
        dept_names = dept_summary["department"].tolist()
        radar_metrics = [
            "total_encounters",
            "average_length_of_stay",
            "readmission_rate",
            "average_satisfaction",
            "patients_per_doctor",
        ]
        radar_labels = [
            "Encounters",
            "ALOS",
            "Readmission %",
            "Satisfaction",
            "Pts/Doctor",
        ]
        # Normalise 0-1 per metric for radar
        norm = dept_summary[radar_metrics].copy()
        for col in radar_metrics:
            rng = norm[col].max() - norm[col].min()
            norm[col] = (norm[col] - norm[col].min()) / rng if rng else 0

        colors = px.colors.qualitative.Bold
        fig_radar = go.Figure()
        for i, row in norm.iterrows():
            vals = [row[m] for m in radar_metrics]
            vals += [vals[0]]  # close polygon
            fig_radar.add_trace(
                go.Scatterpolar(
                    r=vals,
                    theta=radar_labels + [radar_labels[0]],
                    fill="toself",
                    name=dept_summary.loc[i, "department"],
                    line=dict(color=colors[i % len(colors)]),
                    opacity=0.7,
                )
            )
        fig_radar.update_layout(
            template=CHART_TEMPLATE,
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            title="Department Multi-Metric Radar",
            height=370,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
        )
        st.plotly_chart(fig_radar, width="stretch")

    # --- Monthly trend by department ---
    monthly_dept = create_monthly_workload_summary(data, group_by_department=True)
    if not monthly_dept.empty:
        st.markdown("##### Monthly Encounter Trend by Department")
        available_depts = sorted(dept_summary["department"].astype(str).unique().tolist())
        selected_depts = st.multiselect(
            "Filter departments",
            options=available_depts,
            default=available_depts,
            key="exec_dept_trend_filter",
        )
        trend_data = monthly_dept[
            monthly_dept["department"].astype(str).isin(selected_depts)
        ]
        if not trend_data.empty:
            fig_trend = px.line(
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
            fig_trend.update_layout(
                template=CHART_TEMPLATE,
                height=380,
                margin={"l": 10, "r": 10, "t": 50, "b": 10},
            )
            st.plotly_chart(fig_trend, width="stretch")

    # --- Department summary table ---
    st.markdown("##### Department Comparison Table")
    display_cols = {
        "department": "Department",
        "total_doctors": "Doctors",
        "unique_patients": "Unique Patients",
        "total_encounters": "Total Encounters",
        "average_length_of_stay": "Avg LOS (Days)",
        "readmission_rate": "Readmission Rate (%)",
        "average_satisfaction": "Avg Satisfaction",
        "patients_per_doctor": "Patients / Doctor",
    }
    display_df = dept_summary.rename(columns=display_cols)[list(display_cols.values())]
    st.dataframe(display_df, width="stretch", hide_index=True)
    st.download_button(
        label="📥 Download Department Report (CSV)",
        data=display_df.to_csv(index=False).encode("utf-8"),
        file_name="executive_department_performance.csv",
        mime="text/csv",
        key="exec_dept_download",
    )


# ---------------------------------------------------------------------------
# 2. Doctor Performance Summary
# ---------------------------------------------------------------------------

def _render_doctor_performance_summary(data: pd.DataFrame) -> None:
    """Render the Doctor Performance Summary section."""
    st.markdown(
        """
        <div style="font-size:1.3rem; font-weight:700; color:#16324f;
             margin:1.6rem 0 0.2rem;">👨‍⚕️ Doctor Performance Summary</div>
        <div style="font-size:0.9rem; color:#5f6f7f; margin-bottom:1rem;">
            Aggregated performance metrics for each doctor across all encounters.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "doctor_id" not in data.columns:
        st.info("Doctor data is not available in the selected dataset.")
        return

    doctor_summary = create_doctor_level_summary(data)
    if doctor_summary.empty:
        st.info("Doctor performance data is unavailable for the selected filters.")
        return

    total_docs = doctor_summary.shape[0]
    top_doc = doctor_summary.iloc[0]["doctor_id"]
    top_doc_patients = int(doctor_summary.iloc[0]["unique_patients"])
    global_avg_sat = _safe_round(doctor_summary["average_satisfaction"].mean(), 1)
    global_avg_readm = _safe_round(doctor_summary["readmission_rate"].mean(), 1)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            _kpi_card("Total Doctors", f"{total_docs:,}", "👨‍⚕️", PRIMARY_COLOR),
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            _kpi_card("Top Doctor (Patients)", f"{top_doc} · {top_doc_patients:,} pts", "🏆", ACCENT_COLOR),
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            _kpi_card("Avg Satisfaction", f"{global_avg_sat} / 5", "⭐", SUCCESS_COLOR),
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            _kpi_card("Avg Readmission Rate", f"{global_avg_readm}%", "🔄", WARNING_COLOR),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    top_n = st.slider(
        "Number of top doctors to display",
        min_value=5,
        max_value=min(50, total_docs),
        value=min(15, total_docs),
        step=5,
        key="exec_doctor_top_n",
    )

    top_doctors = doctor_summary.head(top_n)

    col_bar, col_scatter = st.columns([3, 2])

    with col_bar:
        fig_top = px.bar(
            top_doctors,
            x="doctor_id",
            y="unique_patients",
            color="average_satisfaction",
            color_continuous_scale="Blues",
            title=f"Top {top_n} Doctors by Patients Treated",
            labels={
                "doctor_id": "Doctor ID",
                "unique_patients": "Unique Patients",
                "average_satisfaction": "Avg Satisfaction",
            },
            text_auto=True,
        )
        fig_top.update_layout(
            template=CHART_TEMPLATE,
            height=380,
            xaxis_tickangle=-45,
            showlegend=False,
            margin={"l": 10, "r": 10, "t": 50, "b": 60},
        )
        st.plotly_chart(fig_top, width="stretch")

    with col_scatter:
        fig_scatter = px.scatter(
            doctor_summary,
            x="average_length_of_stay",
            y="readmission_rate",
            size="unique_patients",
            color="average_satisfaction",
            color_continuous_scale="RdYlGn",
            hover_name="doctor_id",
            title="ALOS vs Readmission Rate (bubble = patients)",
            labels={
                "average_length_of_stay": "Avg LOS (Days)",
                "readmission_rate": "Readmission Rate (%)",
                "average_satisfaction": "Satisfaction",
            },
        )
        fig_scatter.update_layout(
            template=CHART_TEMPLATE,
            height=380,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
        )
        st.plotly_chart(fig_scatter, width="stretch")

    # Readmission rate distribution for doctors
    st.markdown("##### Doctor Readmission Rate Distribution")
    fig_hist = px.histogram(
        doctor_summary,
        x="readmission_rate",
        nbins=20,
        color_discrete_sequence=[PRIMARY_COLOR],
        title="Distribution of Doctor 30-Day Readmission Rates",
        labels={"readmission_rate": "30-Day Readmission Rate (%)"},
    )
    fig_hist.update_layout(
        template=CHART_TEMPLATE,
        height=280,
        bargap=0.05,
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
    )
    st.plotly_chart(fig_hist, width="stretch")

    # Ranked table
    st.markdown("##### Full Doctor Performance Table")
    display_cols = {
        "doctor_id": "Doctor ID",
        "unique_patients": "Unique Patients",
        "total_encounters": "Total Encounters",
        "average_length_of_stay": "Avg LOS (Days)",
        "readmission_rate": "Readmission Rate (%)",
        "average_satisfaction": "Avg Satisfaction",
    }
    if "department" in doctor_summary.columns:
        display_cols["department"] = "Department"

    # Only keep columns that actually exist before renaming
    valid_orig_cols = [k for k in display_cols if k in doctor_summary.columns]
    display_df = doctor_summary[valid_orig_cols].rename(
        columns={k: display_cols[k] for k in valid_orig_cols}
    )
    st.dataframe(display_df, width="stretch", hide_index=True)
    st.download_button(
        label="📥 Download Doctor Performance Report (CSV)",
        data=display_df.to_csv(index=False).encode("utf-8"),
        file_name="executive_doctor_performance.csv",
        mime="text/csv",
        key="exec_doctor_download",
    )


# ---------------------------------------------------------------------------
# 3. Disease Distribution
# ---------------------------------------------------------------------------

def _render_disease_distribution(data: pd.DataFrame) -> None:
    """Render the Disease Distribution section."""
    st.markdown(
        """
        <div style="font-size:1.3rem; font-weight:700; color:#16324f;
             margin:1.6rem 0 0.2rem;">🦠 Disease Distribution</div>
        <div style="font-size:0.9rem; color:#5f6f7f; margin-bottom:1rem;">
            Primary diagnosis breakdown using ICD-9 codes (diag_1 column).
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "diag_1" not in data.columns:
        st.info("Diagnosis column (diag_1) is not available in the dataset.")
        return

    wd = data.copy()
    wd["diag_1_num"] = pd.to_numeric(wd["diag_1"], errors="coerce")
    wd = wd.dropna(subset=["diag_1_num"])

    if wd.empty:
        st.info("No valid diagnosis codes found for the selected filters.")
        return

    wd["disease_category"] = wd["diag_1_num"].apply(_map_icd9_category)

    # Category summary
    cat_summary = (
        wd.groupby("disease_category", as_index=False)
        .agg(
            encounter_count=("encounter_id", "nunique"),
            patient_count=("patient_nbr", "nunique"),
        )
        .sort_values("encounter_count", ascending=False)
        .reset_index(drop=True)
    )

    col_pie, col_bar = st.columns([2, 3])

    with col_pie:
        fig_pie = px.pie(
            cat_summary,
            names="disease_category",
            values="encounter_count",
            title="Disease Category Share of Encounters",
            hole=0.42,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(
            template=CHART_TEMPLATE,
            height=400,
            showlegend=False,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
        )
        st.plotly_chart(fig_pie, width="stretch")

    with col_bar:
        fig_cat_bar = px.bar(
            cat_summary,
            x="encounter_count",
            y="disease_category",
            orientation="h",
            color="encounter_count",
            color_continuous_scale="Blues",
            title="Encounters per Disease Category",
            labels={
                "encounter_count": "Encounters",
                "disease_category": "Disease Category",
            },
            text_auto=True,
        )
        fig_cat_bar.update_layout(
            template=CHART_TEMPLATE,
            height=400,
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
        )
        st.plotly_chart(fig_cat_bar, width="stretch")

    # Gender breakdown by category
    if "gender" in wd.columns:
        st.markdown("##### Disease Category by Gender")
        gender_disease = (
            wd.groupby(["disease_category", "gender"], as_index=False)
            .agg(encounters=("encounter_id", "nunique"))
            .sort_values("encounters", ascending=False)
        )
        fig_gender = px.bar(
            gender_disease,
            x="disease_category",
            y="encounters",
            color="gender",
            barmode="group",
            title="Disease Category Encounters by Gender",
            labels={
                "disease_category": "Disease Category",
                "encounters": "Encounters",
                "gender": "Gender",
            },
            color_discrete_sequence=[PRIMARY_COLOR, ACCENT_COLOR],
        )
        fig_gender.update_layout(
            template=CHART_TEMPLATE,
            height=350,
            xaxis_tickangle=-30,
            margin={"l": 10, "r": 10, "t": 50, "b": 80},
        )
        st.plotly_chart(fig_gender, width="stretch")

    # Age-group breakdown (if age_group column present, else use age)
    age_col = None
    if "age_group" in wd.columns:
        age_col = "age_group"
    elif "age" in wd.columns:
        age_col = "age"

    if age_col:
        st.markdown("##### Top Disease Categories by Age Group")
        age_disease = (
            wd.groupby(["disease_category", age_col], as_index=False)
            .agg(encounters=("encounter_id", "nunique"))
        )
        top_cats = cat_summary["disease_category"].head(6).tolist()
        age_disease_top = age_disease[
            age_disease["disease_category"].isin(top_cats)
        ]
        if not age_disease_top.empty:
            fig_age = px.bar(
                age_disease_top,
                x=age_col,
                y="encounters",
                color="disease_category",
                barmode="stack",
                title=f"Top 6 Disease Categories by {age_col.replace('_', ' ').title()}",
                labels={
                    age_col: age_col.replace("_", " ").title(),
                    "encounters": "Encounters",
                    "disease_category": "Category",
                },
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig_age.update_layout(
                template=CHART_TEMPLATE,
                height=360,
                xaxis_tickangle=-30,
                margin={"l": 10, "r": 10, "t": 50, "b": 80},
            )
            st.plotly_chart(fig_age, width="stretch")

    # Department heatmap
    if "department" in wd.columns:
        st.markdown("##### Disease Category Heatmap by Department")
        heat_data = (
            wd.groupby(["department", "disease_category"])
            .size()
            .reset_index(name="encounters")
        )
        heat_pivot = heat_data.pivot(
            index="department", columns="disease_category", values="encounters"
        ).fillna(0)
        fig_heat = px.imshow(
            heat_pivot,
            color_continuous_scale="Blues",
            title="Encounters: Department × Disease Category",
            labels={"color": "Encounters"},
            aspect="auto",
        )
        fig_heat.update_layout(
            template=CHART_TEMPLATE,
            height=400,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
            xaxis_tickangle=-40,
        )
        st.plotly_chart(fig_heat, width="stretch")


# ---------------------------------------------------------------------------
# 4. Resource Utilization
# ---------------------------------------------------------------------------

def _render_resource_utilization(data: pd.DataFrame) -> None:
    """Render the Resource Utilization section."""
    st.markdown(
        """
        <div style="font-size:1.3rem; font-weight:700; color:#16324f;
             margin:1.6rem 0 0.2rem;">🏗️ Resource Utilization</div>
        <div style="font-size:0.9rem; color:#5f6f7f; margin-bottom:1rem;">
            Bed occupancy, length of stay, and monthly workload utilization insights.
        </div>
        """,
        unsafe_allow_html=True,
    )

    wd = data.copy()

    # --- KPI headline ---
    avg_bed_occ = None
    avg_los = None
    total_enc = wd["encounter_id"].nunique() if "encounter_id" in wd.columns else 0

    if "bed_occupancy" in wd.columns:
        bed_num = pd.to_numeric(wd["bed_occupancy"], errors="coerce")
        avg_bed_occ = _safe_round(bed_num.mean(), 1)

    if "length_of_stay" in wd.columns:
        los_num = pd.to_numeric(wd["length_of_stay"], errors="coerce")
        avg_los = _safe_round(los_num.mean(), 1)

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(
            _kpi_card(
                "Total Encounters",
                f"{total_enc:,}",
                "📋",
                PRIMARY_COLOR,
            ),
            unsafe_allow_html=True,
        )
    with k2:
        val = f"{avg_los} Days" if avg_los is not None else "N/A"
        st.markdown(
            _kpi_card("Avg Length of Stay", val, "🛏️", SECONDARY_COLOR),
            unsafe_allow_html=True,
        )
    with k3:
        val = f"{avg_bed_occ}%" if avg_bed_occ is not None else "N/A"
        st.markdown(
            _kpi_card("Avg Bed Occupancy", val, "🏥", ACCENT_COLOR),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Bed Occupancy Trend Over Time ---
    if "bed_occupancy" in wd.columns and "admission_date" in wd.columns:
        st.markdown("##### Bed Occupancy Trend Over Time")
        wd["admission_date"] = pd.to_datetime(wd["admission_date"], errors="coerce")
        wd["bed_occupancy"] = pd.to_numeric(wd["bed_occupancy"], errors="coerce")
        dated = wd.dropna(subset=["admission_date", "bed_occupancy"])
        if not dated.empty:
            dated["month"] = dated["admission_date"].dt.to_period("M").dt.to_timestamp()
            monthly_occ = (
                dated.groupby("month", as_index=False)["bed_occupancy"]
                .mean()
                .round(1)
            )
            monthly_occ.rename(
                columns={"bed_occupancy": "avg_bed_occupancy"}, inplace=True
            )

            fig_occ = go.Figure()
            fig_occ.add_trace(
                go.Scatter(
                    x=monthly_occ["month"],
                    y=monthly_occ["avg_bed_occupancy"],
                    mode="lines+markers",
                    name="Avg Bed Occupancy (%)",
                    line=dict(color=PRIMARY_COLOR, width=3),
                    fill="tozeroy",
                    fillcolor=f"rgba(22,50,79,0.12)",
                )
            )
            fig_occ.add_hline(
                y=85,
                line_dash="dash",
                line_color=WARNING_COLOR,
                annotation_text="85% Alert Threshold",
                annotation_position="top right",
            )
            fig_occ.update_layout(
                template=CHART_TEMPLATE,
                title="Monthly Average Bed Occupancy (%)",
                xaxis_title="Month",
                yaxis_title="Avg Bed Occupancy (%)",
                height=340,
                margin={"l": 10, "r": 10, "t": 50, "b": 10},
            )
            st.plotly_chart(fig_occ, width="stretch")

    # --- LOS Distribution ---
    if "length_of_stay" in wd.columns:
        st.markdown("##### Length of Stay Distribution")
        col_hist, col_box = st.columns(2)
        los_data = pd.to_numeric(wd["length_of_stay"], errors="coerce").dropna()

        with col_hist:
            fig_los_hist = px.histogram(
                x=los_data,
                nbins=20,
                color_discrete_sequence=[SECONDARY_COLOR],
                title="Length of Stay — Frequency Distribution",
                labels={"x": "Length of Stay (Days)", "y": "Encounters"},
            )
            fig_los_hist.update_layout(
                template=CHART_TEMPLATE,
                height=300,
                bargap=0.05,
                margin={"l": 10, "r": 10, "t": 50, "b": 10},
            )
            st.plotly_chart(fig_los_hist, width="stretch")

        with col_box:
            if "department" in wd.columns:
                fig_los_box = px.box(
                    wd.dropna(subset=["length_of_stay"]),
                    x="department",
                    y="length_of_stay",
                    color="department",
                    title="Length of Stay by Department",
                    labels={
                        "department": "Department",
                        "length_of_stay": "LOS (Days)",
                    },
                )
                fig_los_box.update_layout(
                    template=CHART_TEMPLATE,
                    height=300,
                    showlegend=False,
                    margin={"l": 10, "r": 10, "t": 50, "b": 10},
                )
                st.plotly_chart(fig_los_box, width="stretch")

    # --- Monthly Workload ---
    monthly_wl = create_monthly_workload_summary(data)
    if not monthly_wl.empty:
        st.markdown("##### Monthly Hospital Workload")
        fig_wl = go.Figure()
        fig_wl.add_trace(
            go.Bar(
                x=monthly_wl["month"],
                y=monthly_wl["total_encounters"],
                name="Encounters",
                marker_color=PRIMARY_COLOR,
                opacity=0.85,
            )
        )
        fig_wl.add_trace(
            go.Scatter(
                x=monthly_wl["month"],
                y=monthly_wl["unique_patients"],
                mode="lines+markers",
                name="Unique Patients",
                line=dict(color=ACCENT_COLOR, width=2),
                yaxis="y2",
            )
        )
        fig_wl.update_layout(
            template=CHART_TEMPLATE,
            title="Monthly Encounters & Unique Patients",
            xaxis_title="Month",
            yaxis=dict(title="Total Encounters"),
            yaxis2=dict(
                title="Unique Patients",
                overlaying="y",
                side="right",
                showgrid=False,
            ),
            legend=dict(x=0.01, y=0.99),
            height=380,
            margin={"l": 10, "r": 60, "t": 50, "b": 10},
        )
        st.plotly_chart(fig_wl, width="stretch")

    # --- Bed Occupancy by Department ---
    if "bed_occupancy" in wd.columns and "department" in wd.columns:
        st.markdown("##### Average Bed Occupancy by Department")
        bed_dept = (
            wd.groupby("department", as_index=False)["bed_occupancy"]
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
        fig_bed_dept.update_layout(
            template=CHART_TEMPLATE,
            height=320,
            coloraxis_showscale=False,
            margin={"l": 10, "r": 10, "t": 50, "b": 10},
        )
        st.plotly_chart(fig_bed_dept, width="stretch")


# ---------------------------------------------------------------------------
# Main Render Entry Point
# ---------------------------------------------------------------------------

def render_performance_resource_analytics(data: pd.DataFrame) -> None:
    """
    Render the complete Performance & Resource Analytics executive dashboard.

    Args:
        data: Filtered hospital dashboard dataset passed from app.py.
    """
    st.markdown(
        """
        <div style="margin-bottom:0.3rem;">
            <span style="font-size:2rem; font-weight:700; color:#16324f;">
                📊 Performance &amp; Resource Analytics
            </span>
        </div>
        <div style="font-size:0.98rem; color:#5f6f7f; margin-bottom:0.5rem;">
            Executive KPI Dashboard · Department efficiency, doctor performance,
            disease distribution &amp; resource utilization.
        </div>
        <hr style="border-color:#d6e0e9; margin-bottom:1.2rem;">
        """,
        unsafe_allow_html=True,
    )

    if data.empty:
        st.warning("No records match the selected filters.")
        return

    # Section tabs for clean navigation
    tab_dept, tab_doctor, tab_disease, tab_resource = st.tabs([
        "🏢 Department Performance",
        "👨‍⚕️ Doctor Performance",
        "🦠 Disease Distribution",
        "🏗️ Resource Utilization",
    ])

    with tab_dept:
        _render_department_performance(data)

    with tab_doctor:
        _render_doctor_performance_summary(data)

    with tab_disease:
        _render_disease_distribution(data)

    with tab_resource:
        _render_resource_utilization(data)
