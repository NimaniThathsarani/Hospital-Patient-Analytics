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