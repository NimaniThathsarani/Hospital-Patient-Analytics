# Hospital Patient Analytics

## Project Description

Hospital Patient Analytics is a data-driven healthcare analytics solution that leverages data science and machine learning techniques to improve hospital operations, patient care, and resource utilization. The project analyzes patient data to predict hospital readmissions, forecast patient admissions, identify disease trends, segment patients based on demographics and medical history, detect high-risk patients, and provide interactive dashboards that support data-driven decision-making for healthcare professionals and hospital management.

---

## Project Objectives

- Predict patient readmissions using machine learning.
- Forecast daily, weekly, and monthly hospital admissions.
- Analyze disease trends by age group, gender, season, and location.
- Build an interactive Doctor Performance Dashboard.
- Identify high-risk patients and recommend preventive healthcare strategies.
- Optimize hospital resource allocation.
- Perform patient segmentation using clustering techniques.
- Develop an Executive KPI Dashboard for hospital management.

---

## Dataset

**Dataset Name:** Diabetes 130-US Hospitals for Years 1999–2008

**Source:** UCI Machine Learning Repository / Kaggle

The dataset contains patient demographics, diagnoses, medications, hospital visits, admission information, and readmission labels. Synthetic fields such as doctor ID, department, admission date, bed occupancy, and length of stay are added to support advanced analytics and dashboard development.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/NimaniThathsarani/Hospital-Patient-Analytics.git
```

Navigate to the project directory:

```bash
cd Hospital-Patient-Analytics
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Project

Run Jupyter Notebook:

```bash
jupyter notebook
```

Run the Streamlit Dashboard:

```bash
streamlit run dashboards/executive_dashboard/app.py
```
