# Data Dictionary - Hospital Dataset (Squad 1)

This document describes the structure and variables of the `cleaned_dataset.csv` prepared by the Data Engineering Squad.

## Original Fields (Cleaned)
| Feature | Data Type | Description |
| :--- | :--- | :--- |
| `encounter_id` | Integer | Unique identifier for an encounter / hospital admission |
| `patient_nbr` | Integer | Unique identifier for a patient |
| `race` | String | Patient's race (e.g., Caucasian, Asian, AfricanAmerican) |
| `gender` | String | Patient's gender (Male, Female) |
| `age` | String | Patient's age group in 10-year intervals |
| `time_in_hospital` | Integer | Number of days between admission and discharge |
| `num_lab_procedures` | Integer | Number of lab tests performed during the encounter |
| `num_procedures` | Integer | Number of procedures (other than lab tests) performed |
| `num_medications` | Integer | Number of distinct generic names administered |
| `diag_1`, `diag_2`, `diag_3` | String | Primary, secondary, and tertiary diagnoses (ICD9 codes) |
| `number_diagnoses` | Integer | Total number of diagnoses entered to the system |
| `diabetesMed` | String | Indicates if any diabetic medication was prescribed (Yes/No) |
| `readmitted` | String | Days to inpatient readmission (<30, >30, or NO) |

## Synthetic Fields Generated
These fields were synthetically generated to provide operational data for machine learning models and business intelligence dashboards.

| Feature | Data Type | Description | Generation Logic |
| :--- | :--- | :--- | :--- |
| `doctor_id` | String | Unique ID assigned to the attending doctor | Randomly generated IDs (e.g., DOC_1234) |
| `department` | String | Hospital department treating the patient | Randomly assigned from a list of 5 major departments |
| `admission_date` | Date | Date when the patient was admitted | Random dates generated between 1999 and 2008 |
| `bed_occupancy` | Integer | Hospital bed occupancy percentage at admission | Random integer between 50% and 100% |
| `location` | String | City and State of the hospital branch | Randomly selected from 5 major US cities |
| `patient_satisfaction` | Integer | Patient satisfaction score | Random scale from 1 (Lowest) to 5 (Highest) |
| `length_of_stay` | Integer | Total days stayed in the hospital | Mapped directly from `time_in_hospital` |

*Note: Columns with excessive missing values (`weight`, `payer_code`, `medical_specialty`) were dropped during preprocessing.*