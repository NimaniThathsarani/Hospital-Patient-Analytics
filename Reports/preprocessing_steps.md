# Data Preprocessing Steps

This document outlines the data cleaning, feature engineering, and encoding steps performed by the Data Engineering Squad (Squad 1) to prepare the `diabetic_data.csv` for downstream machine learning and BI tasks.

### Step 1: Handling Missing Values
* **Identifying Nulls:** In the raw dataset, missing values were represented by the `'?'` character. These were all converted to standard `NaN` values using Pandas.
* **Dropping Heavily Missing Columns:** Columns with a critically high percentage of missing values were completely dropped from the dataset to prevent model skewness.
  * Dropped Columns: `weight` (~97% missing), `payer_code`, and `medical_specialty`.
* **Dropping Rows with Missing Critical Data:** Rows containing `NaN` in essential categorical or diagnostic columns (`diag_1`, `diag_2`, `diag_3`, `race`, `gender`) were dropped to maintain data integrity.

### Step 2: Synthetic Feature Engineering
Since the original dataset lacked operational hospital fields required by other squads, realistic synthetic data was generated using `numpy.random`:
* **`doctor_id`**: Generated unique string identifiers (e.g., 'DOC_4592').
* **`department`**: Randomly assigned patients to 'Cardiology', 'Endocrinology', 'General Medicine', 'Neurology', or 'Surgery'.
* **`admission_date`**: Generated random datetime objects distributed between January 1, 1999, and December 31, 2008.
* **`bed_occupancy`**: Generated random integers between 50 and 100 to represent hospital capacity percentage.
* **`location`**: Assigned a realistic US city location (e.g., 'New York, NY', 'Chicago, IL').
* **`patient_satisfaction`**: Generated a numeric rating from 1 to 5.
* **`length_of_stay`**: Duplicated from `time_in_hospital` for naming clarity required by specific modeling tasks.

### Step 3: Categorical Encoding
To support the Machine Learning squad, an encoded version of the dataset was created:
* **One-Hot Encoding:** Applied `pd.get_dummies(drop_first=True)` to convert categorical variables into machine-readable numeric formats.
* Encoded Columns: `race`, `gender`, `department`, `location`, `readmitted`, `diabetesMed`, and `change`.

### Step 4: Final Deliverables Generated
The Python script successfully outputted three main files into the `data/cleaned/` directory:
1. `cleaned_dataset.csv`: Cleaned data containing original and synthetic operational fields.
2. `encoded_dataset.csv`: Fully numeric/one-hot encoded dataset ready for predictive modeling.
3. `final_dataset.csv`: A duplicate fallback of the encoded dataset for merged pipeline tasks.