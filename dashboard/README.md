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

The comparison result can be downloaded as a CSV file.

### Department Performance

Displays department-level operational performance.

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

Doctor encounter details can be downloaded as a CSV file.

## Interactive Filters

The sidebar contains:

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
Encounters where readmitted is "<30"
divided by
Total filtered encounters
multiplied by 100
```

### Average Satisfaction

Average value of the patient-satisfaction field on a 1-to-5 scale.

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

## Run the Dashboard

From the project root, install the required packages:

```python
python -m pip install streamlit pandas plotly
```

Start the dashboard:

```python
python -m streamlit run dashboard/app.py
```

The dashboard normally opens at:

```
http://localhost:8501
```

### Main Source Files

```
dashboard/
├── app.py
├── overview.py
├── doctor_analysis.py
├── department_analysis.py
├── data_loader.py
├── kpi_calculations.py
├── styles.py
├── screenshots/
└── README.md
```

## Data Limitations

Some doctor, department, admission-date, location, and patient-satisfaction fields used in the project are synthetic fields created for analytical demonstration.

Dashboard outputs should therefore be interpreted as project simulation results rather than real clinical performance assessments.

Doctor performance should not be judged using a single KPI. Patient complexity, diagnosis severity, department workload, and other clinical factors should also be considered.