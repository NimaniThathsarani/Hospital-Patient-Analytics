"""
Doctor-level analysis components for the Doctor Performance Dashboard.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


REQUIRED_DOCTOR_COLUMNS = {
    "doctor_id",
    "department",
    "patient_nbr",
    "encounter_id",
    "length_of_stay",
    "readmitted",
    "patient_satisfaction",
}


def validate_doctor_data(data: pd.DataFrame) -> list[str]:
    """
    Return the required doctor-analysis columns missing from the dataset.

    Args:
        data: Filtered hospital dashboard dataset.

    Returns:
        Sorted list of missing column names.
    """
    return sorted(
        REQUIRED_DOCTOR_COLUMNS.difference(data.columns)
    )


def get_primary_department(
    department_values: pd.Series,
) -> str:
    """
    Return the most frequently occurring department for a doctor.

    The temporary cleaned dataset may assign one doctor to several
    departments. Pasindu's processed dataset will later provide a
    consistent doctor-to-department relationship.

    Args:
        department_values: Department values associated with a doctor.

    Returns:
        Most frequent department name.
    """
    valid_departments = (
        department_values
        .dropna()
        .astype(str)
        .str.strip()
    )

    valid_departments = valid_departments[
        valid_departments.ne("")
    ]

    if valid_departments.empty:
        return "Unknown"

    department_mode = valid_departments.mode()

    if department_mode.empty:
        return valid_departments.iloc[0]

    return department_mode.iloc[0]


def create_doctor_summary(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create one performance-summary row for each doctor.

    Args:
        data: Filtered hospital dashboard dataset.

    Returns:
        Doctor-level summary containing workload and performance KPIs.
    """
    if data.empty:
        return pd.DataFrame()

    working_data = data.copy()

    working_data["is_30_day_readmission"] = (
        working_data["readmitted"]
        .astype(str)
        .str.strip()
        .eq("<30")
    )

    doctor_summary = (
        working_data.groupby(
            "doctor_id",
            as_index=False,
        )
        .agg(
            department=(
                "department",
                get_primary_department,
            ),
            unique_patients=(
                "patient_nbr",
                "nunique",
            ),
            total_encounters=(
                "encounter_id",
                "nunique",
            ),
            average_length_of_stay=(
                "length_of_stay",
                "mean",
            ),
            readmission_rate=(
                "is_30_day_readmission",
                "mean",
            ),
            average_satisfaction=(
                "patient_satisfaction",
                "mean",
            ),
        )
    )

    doctor_summary["readmission_rate"] *= 100

    doctor_summary[
        "average_length_of_stay"
    ] = doctor_summary[
        "average_length_of_stay"
    ].round(2)

    doctor_summary[
        "readmission_rate"
    ] = doctor_summary[
        "readmission_rate"
    ].round(2)

    doctor_summary[
        "average_satisfaction"
    ] = doctor_summary[
        "average_satisfaction"
    ].round(2)

    return doctor_summary.sort_values(
        by=[
            "unique_patients",
            "total_encounters",
        ],
        ascending=[
            False,
            False,
        ],
    ).reset_index(drop=True)


def create_single_doctor_metrics(
    data: pd.DataFrame,
    doctor_id: str,
) -> dict[str, object]:
    """
    Calculate detailed KPIs for one selected doctor.

    Args:
        data: Filtered hospital dashboard dataset.
        doctor_id: Doctor identifier selected by the user.

    Returns:
        Dictionary containing the selected doctor's KPIs.
    """
    doctor_data = data[
        data["doctor_id"].astype(str) == str(doctor_id)
    ].copy()

    if doctor_data.empty:
        return {}

    doctor_data["is_30_day_readmission"] = (
        doctor_data["readmitted"]
        .astype(str)
        .str.strip()
        .eq("<30")
    )

    average_length_of_stay = pd.to_numeric(
        doctor_data["length_of_stay"],
        errors="coerce",
    ).mean()

    average_satisfaction = pd.to_numeric(
        doctor_data["patient_satisfaction"],
        errors="coerce",
    ).mean()

    return {
        "doctor_id": str(doctor_id),
        "department": get_primary_department(
            doctor_data["department"]
        ),
        "unique_patients": int(
            doctor_data["patient_nbr"].nunique()
        ),
        "total_encounters": int(
            doctor_data["encounter_id"].nunique()
        ),
        "average_length_of_stay": (
            round(
                float(average_length_of_stay),
                2,
            )
            if pd.notna(average_length_of_stay)
            else 0.0
        ),
        "readmission_rate": round(
            float(
                doctor_data[
                    "is_30_day_readmission"
                ].mean()
                * 100
            ),
            2,
        ),
        "average_satisfaction": (
            round(
                float(average_satisfaction),
                2,
            )
            if pd.notna(average_satisfaction)
            else 0.0
        ),
    }


def create_monthly_doctor_workload(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create a monthly encounter count for one doctor.

    Args:
        data: Hospital records belonging to one doctor.

    Returns:
        Monthly workload summary.
    """
    if (
        data.empty
        or "admission_date" not in data.columns
    ):
        return pd.DataFrame()

    workload_data = data.copy()

    workload_data["admission_date"] = pd.to_datetime(
        workload_data["admission_date"],
        errors="coerce",
    )

    workload_data = workload_data.dropna(
        subset=["admission_date"]
    )

    if workload_data.empty:
        return pd.DataFrame()

    workload_data["month"] = (
        workload_data["admission_date"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    monthly_workload = (
        workload_data.groupby(
            "month",
            as_index=False,
        )
        .agg(
            total_encounters=(
                "encounter_id",
                "nunique",
            ),
            unique_patients=(
                "patient_nbr",
                "nunique",
            ),
        )
        .sort_values("month")
    )

    return monthly_workload


def create_top_diagnoses(
    data: pd.DataFrame,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return the most frequent primary diagnoses for one doctor.

    Args:
        data: Hospital records belonging to one doctor.
        limit: Maximum number of diagnoses to return.

    Returns:
        Diagnosis-frequency summary.
    """
    if (
        data.empty
        or "diag_1" not in data.columns
    ):
        return pd.DataFrame()

    diagnosis_data = (
        data["diag_1"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    diagnosis_data = diagnosis_data[
        diagnosis_data.ne("")
        & diagnosis_data.str.lower().ne("nan")
    ]

    if diagnosis_data.empty:
        return pd.DataFrame()

    return (
        diagnosis_data.value_counts()
        .head(limit)
        .rename_axis("diagnosis")
        .reset_index(name="encounter_count")
    )


def render_doctor_comparison(
    data: pd.DataFrame,
) -> None:
    """
    Render the interactive doctor-comparison section.

    Args:
        data: Filtered hospital dashboard dataset.
    """
    st.subheader("Doctor Comparison")

    missing_columns = validate_doctor_data(data)

    if missing_columns:
        st.error(
            "Doctor comparison cannot be displayed because "
            f"these columns are missing: "
            f"{', '.join(missing_columns)}"
        )
        return

    doctor_summary = create_doctor_summary(data)

    if doctor_summary.empty:
        st.warning(
            "No doctor records are available for the selected filters."
        )
        return

    st.caption(
        "Compare doctors using patient volume, length of stay, "
        "30-day readmission rate, and patient satisfaction."
    )

    available_doctors = sorted(
        doctor_summary["doctor_id"]
        .astype(str)
        .unique()
        .tolist()
    )

    selected_doctors = st.multiselect(
        "Select doctors for direct comparison",
        options=available_doctors,
        help=(
            "Select up to five doctors. Leave this empty to display "
            "the highest-ranking doctors for the selected metric."
        ),
        key="direct_doctor_comparison",
    )

    if len(selected_doctors) > 5:
        st.warning(
            "Only the first five selected doctors will be compared."
        )
        selected_doctors = selected_doctors[:5]

    maximum_doctors = min(
        20,
        len(doctor_summary),
    )

    minimum_doctors = (
        1
        if maximum_doctors < 5
        else 5
    )

    default_doctors = min(
        10,
        maximum_doctors,
    )

    control_column_1, control_column_2 = st.columns(2)

    with control_column_1:
        doctor_limit = st.slider(
            "Number of ranked doctors to display",
            min_value=minimum_doctors,
            max_value=maximum_doctors,
            value=default_doctors,
            step=1,
            disabled=bool(selected_doctors),
            key="doctor_comparison_limit",
        )

    with control_column_2:
        selected_metric = st.selectbox(
            "Select comparison metric",
            [
                "Unique Patients",
                "Total Encounters",
                "Average Length of Stay",
                "30-Day Readmission Rate",
                "Average Satisfaction",
            ],
            key="doctor_comparison_metric",
        )

    metric_column_map = {
        "Unique Patients": "unique_patients",
        "Total Encounters": "total_encounters",
        "Average Length of Stay": (
            "average_length_of_stay"
        ),
        "30-Day Readmission Rate": (
            "readmission_rate"
        ),
        "Average Satisfaction": (
            "average_satisfaction"
        ),
    }

    selected_column = metric_column_map[
        selected_metric
    ]

    if selected_doctors:
        chart_data = doctor_summary[
            doctor_summary["doctor_id"]
            .astype(str)
            .isin(selected_doctors)
        ].copy()

        chart_title = (
            f"Selected Doctors by {selected_metric}"
        )

    else:
        chart_data = (
            doctor_summary.sort_values(
                by=selected_column,
                ascending=False,
            )
            .head(doctor_limit)
            .copy()
        )

        chart_title = (
            f"Top Doctors by {selected_metric}"
        )

    comparison_chart = px.bar(
        chart_data,
        x=selected_column,
        y="doctor_id",
        orientation="h",
        color="department",
        title=chart_title,
        labels={
            "doctor_id": "Doctor ID",
            selected_column: selected_metric,
            "department": "Department",
        },
        hover_data={
            "unique_patients": True,
            "total_encounters": True,
            "average_length_of_stay": ":.2f",
            "readmission_rate": ":.2f",
            "average_satisfaction": ":.2f",
        },
    )

    comparison_chart.update_layout(
        yaxis={
            "categoryorder": "total ascending",
        },
        margin={
            "l": 20,
            "r": 20,
            "t": 60,
            "b": 20,
        },
        height=max(
            450,
            len(chart_data) * 40,
        ),
        legend_title_text="Department",
    )

    st.plotly_chart(
        comparison_chart,
        use_container_width=True,
    )

    st.markdown("### Doctor Performance Summary")

    display_summary = chart_data.rename(
        columns={
            "doctor_id": "Doctor ID",
            "department": "Department",
            "unique_patients": "Unique Patients",
            "total_encounters": "Total Encounters",
            "average_length_of_stay": (
                "Average Length of Stay"
            ),
            "readmission_rate": (
                "30-Day Readmission Rate (%)"
            ),
            "average_satisfaction": (
                "Average Satisfaction"
            ),
        }
    )

    display_summary = display_summary[
        [
            "Doctor ID",
            "Department",
            "Unique Patients",
            "Total Encounters",
            "Average Length of Stay",
            "30-Day Readmission Rate (%)",
            "Average Satisfaction",
        ]
    ]

    st.dataframe(
        display_summary,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        label="Download Doctor Comparison CSV",
        data=display_summary.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="doctor_performance_comparison.csv",
        mime="text/csv",
    )


def render_doctor_details(
    data: pd.DataFrame,
) -> None:
    """
    Render a detailed drill-down view for one selected doctor.

    Args:
        data: Filtered hospital dashboard dataset.
    """
    st.subheader("Doctor Details")

    missing_columns = validate_doctor_data(data)

    if missing_columns:
        st.error(
            "Doctor details cannot be displayed because "
            f"these columns are missing: "
            f"{', '.join(missing_columns)}"
        )
        return

    available_doctors = sorted(
        data["doctor_id"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if not available_doctors:
        st.warning(
            "No doctors are available for the selected filters."
        )
        return

    selected_doctor = st.selectbox(
        "Select Doctor",
        available_doctors,
        key="doctor_details_selector",
    )

    metrics = create_single_doctor_metrics(
        data,
        selected_doctor,
    )

    if not metrics:
        st.warning(
            "No records were found for the selected doctor."
        )
        return

    st.caption(
        f"Department: {metrics['department']}"
    )

    (
        column_1,
        column_2,
        column_3,
        column_4,
        column_5,
    ) = st.columns(5)

    with column_1:
        st.metric(
            "Unique Patients",
            f"{metrics['unique_patients']:,}",
        )

    with column_2:
        st.metric(
            "Total Encounters",
            f"{metrics['total_encounters']:,}",
        )

    with column_3:
        st.metric(
            "Average Length of Stay",
            (
                f"{metrics['average_length_of_stay']:.2f} days"
            ),
        )

    with column_4:
        st.metric(
            "30-Day Readmission Rate",
            f"{metrics['readmission_rate']:.2f}%",
        )

    with column_5:
        st.metric(
            "Average Satisfaction",
            (
                f"{metrics['average_satisfaction']:.2f} / 5"
            ),
        )

    doctor_data = data[
        data["doctor_id"].astype(str)
        == selected_doctor
    ].copy()

    st.markdown(
        "### Doctor Workload and Diagnosis Analysis"
    )

    chart_column_1, chart_column_2 = st.columns(2)

    monthly_workload = create_monthly_doctor_workload(
        doctor_data
    )

    with chart_column_1:
        if monthly_workload.empty:
            st.info(
                "Monthly workload cannot be displayed because "
                "valid admission-date records are unavailable."
            )
        else:
            workload_chart = px.line(
                monthly_workload,
                x="month",
                y="total_encounters",
                markers=True,
                title="Monthly Encounter Workload",
                labels={
                    "month": "Month",
                    "total_encounters": (
                        "Total Encounters"
                    ),
                },
                hover_data={
                    "unique_patients": True,
                },
            )

            workload_chart.update_layout(
                margin={
                    "l": 20,
                    "r": 20,
                    "t": 60,
                    "b": 20,
                },
                height=420,
            )

            st.plotly_chart(
                workload_chart,
                use_container_width=True,
            )

    top_diagnoses = create_top_diagnoses(
        doctor_data,
        limit=10,
    )

    with chart_column_2:
        if top_diagnoses.empty:
            st.info(
                "Diagnosis analysis cannot be displayed because "
                "valid primary-diagnosis records are unavailable."
            )
        else:
            diagnosis_chart = px.bar(
                top_diagnoses.sort_values(
                    "encounter_count",
                    ascending=True,
                ),
                x="encounter_count",
                y="diagnosis",
                orientation="h",
                title="Most Common Primary Diagnoses",
                labels={
                    "diagnosis": "Primary Diagnosis",
                    "encounter_count": (
                        "Encounter Count"
                    ),
                },
            )

            diagnosis_chart.update_layout(
                margin={
                    "l": 20,
                    "r": 20,
                    "t": 60,
                    "b": 20,
                },
                height=420,
            )

            st.plotly_chart(
                diagnosis_chart,
                use_container_width=True,
            )

    display_columns = [
        column
        for column in [
            "encounter_id",
            "patient_nbr",
            "department",
            "admission_date",
            "length_of_stay",
            "readmitted",
            "patient_satisfaction",
            "diag_1",
        ]
        if column in doctor_data.columns
    ]

    st.markdown("### Encounter Details")

    if not display_columns:
        st.warning(
            "No encounter-detail columns are available."
        )
        return

    encounter_details = doctor_data[
        display_columns
    ].copy()

    if "admission_date" in encounter_details.columns:
        encounter_details[
            "admission_date"
        ] = pd.to_datetime(
            encounter_details["admission_date"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

    st.dataframe(
        encounter_details,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        label="Download Doctor Encounter Details",
        data=encounter_details.to_csv(
            index=False
        ).encode("utf-8"),
        file_name=(
            f"{selected_doctor}_encounter_details.csv"
        ),
        mime="text/csv",
    )