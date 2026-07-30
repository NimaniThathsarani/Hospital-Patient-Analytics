# Doctor Performance Dashboard

## Overview

This Streamlit dashboard provides interactive operational analytics for evaluating doctor and department performance in the Hospital Patient Analytics project.

The dashboard supports hospital management by displaying workload, patient outcomes, length of stay, readmission patterns, and patient satisfaction indicators.

## Dashboard Pages

### Executive Overview

Displays hospital-level KPIs:

- Total doctors
- Unique patients
- Total encounters
- Average length of stay
- 30-day readmission rate
- Average patient satisfaction
- Department performance snapshot
- Monthly hospital workload

### Doctor Comparison

Supports doctor-level comparisons using:

- Unique patients treated
- Total encounters
- Average length of stay
- 30-day readmission rate
- Average patient satisfaction

Users can select up to five doctors for direct comparison or display the highest-ranking doctors for a selected KPI.

The doctor comparison results can also be downloaded as a CSV file.

### Department Performance

Displays department-level operational performance, including:

- Patients treated by department
- Total encounters
- Number of doctors
- Average length of stay
- 30-day readmission rate
- Average patient satisfaction
- Patients per doctor
- Monthly department workload

This page is implemented through the shared department-analysis module.

### Doctor Details

Provides drill-down analysis for one selected doctor:

- Doctor department
- Unique patients
- Total encounters
- Average length of stay
- 30-day readmission rate
- Average satisfaction
- Monthly workload
- Common primary diagnoses
- Encounter-level records

Doctor encounter details can also be downloaded as a CSV file.

## Interactive Filters

The dashboard sidebar contains:

- Admission date range
- Department
- Doctor
- Gender
- Readmission status

All dashboard KPIs, charts, and tables update according to the selected filters.

## KPI Definitions

### Unique Patients

Number of distinct patient identifiers handled by a doctor or department.

### Total Encounters

Number of distinct hospital encounters.

### Average Length of Stay

Average value of the `length_of_stay` field for the filtered records.

### 30-Day Readmission Rate

Calculated as:

```text
Number of encounters where readmitted is "<30"
divided by
Total filtered encounters
multiplied by 100
```

### Average Satisfaction

Average value of the `patient_satisfaction` field on a 1-to-5 scale.

### Patients per Doctor

Calculated as:

```
Unique patients treated by a department
divided by
Number of doctors in that department
```

## Folder Structure

```
Hospital-Patient-Analytics/
│
├── dashboard/
│   ├── app.py
│   ├── overview.py
│   ├── doctor_analysis.py
│   ├── department_analysis.py
│   ├── data_loader.py
│   ├── kpi_calculations.py
│   ├── styles.py
│   ├── README.md
│   │
│   └── screenshots/
│       ├── dashboard_overview.png
│       ├── doctor_comparison.png
│       ├── department_performance.png
│       └── doctor_details.png
│
├── scripts/
│   └── prepare_doctor_dashboard_data.py
│
├── data/
│   ├── raw/
│   │   └── diabetic_data.csv
│   │
│   ├── cleaned/
│   │   ├── cleaned_dataset.csv
│   │   ├── daily_admissions.csv
│   │   ├── encoded_dataset.csv
│   │   ├── final_dataset.csv
│   │   ├── monthly_admissions.csv
│   │   └── weekly_admissions.csv
│   │
│   └── processed/
│       └── doctor_performance_dataset.csv
│
├── models/
│   └── admission_forecasting/
│
├── notebooks/
├── outputs/
├── requirements.txt
├── data_dictionary.md
├── Model_Evaluation_Report.md
├── preprocessing_steps.md
└── README.md
```

The repository already contains the data, models, notebooks, outputs, and project documentation areas shown above.

## Main Dashboard Source Files

`app.py`

Main Streamlit application responsible for:

- Page configuration
- Navigation
- Sidebar filters
- Dataset selection
- Connecting dashboard modules

`overview.py`

Contains:

- Executive KPI calculations
- Department overview charts
- Monthly hospital workload analysis

`doctor_analysis.py`

Contains:

- Doctor-level KPI calculations
- Doctor ranking
- Direct doctor comparison
- Doctor details drill-down
- Workload and diagnosis charts
- CSV download functionality

`department_analysis.py`

Contains:

- Department-level KPI calculations
- Department comparison charts
- Department workload analysis

`data_loader.py`

- Loads and validates the processed dashboard dataset.

`kpi_calculations.py`

- Contains reusable KPI calculation functions.

`styles.py`

- Contains shared CSS styling for the Streamlit dashboard.

`prepare_doctor_dashboard_data.py`

- Creates the dashboard-specific processed dataset from the cleaned hospital dataset.

## Data Source

The application first checks for:

```
data/processed/doctor_performance_dataset.csv
```

If that file is unavailable during development, it uses:

```
data/cleaned/cleaned_dataset.csv
```

The processed doctor-performance dataset is the preferred final dashboard source.

## Installation

From the project root, install the required packages:

```python
python -m pip install streamlit pandas plotly
```

## Run the Dashboard

From the project root, run:

```python
python -m streamlit run dashboard/app.py
```

The dashboard normally opens at:

```
http://localhost:8501
```

## Dashboard Deliverables

The subgroup deliverables include:

- Interactive Streamlit dashboard
- Dashboard source code
- Processed dashboard dataset
- Dashboard screenshots
- KPI documentation
- Git commit history
- Completed feature branch merged into main

## Data Limitations

Some fields used in this dashboard, including doctor, department, admission date, location, and patient satisfaction, were synthetically generated for project demonstration.

The dashboard results should therefore be interpreted as simulated analytical outputs rather than real clinical performance assessments.

Doctor performance should also be evaluated using multiple KPIs and relevant clinical context, not a single measure.