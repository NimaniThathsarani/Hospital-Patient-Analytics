# Thimira - Season & Location Analysis

## Method
- Parsed `admission_date` into month and season.
- Consolidated the one-hot location columns into a single `location` field.
- Summarized encounter volume, length of stay, patient satisfaction, and readmission rate by season and location.

## Key Findings
- The busiest season is **Summer** with **24722** encounters, while **Winter** is the least active with **24302** encounters.
- Encounter volume is fairly balanced across locations, with **Phoenix, AZ** slightly highest at **19703** encounters and **New York, NY** lowest at **19506**.
- Average length of stay and readmission rate vary only modestly by season, suggesting no extreme seasonal pressure in this dataset.
- `Unknown` records indicate missing location flags, so location coverage is not perfectly complete in the source data.
- The heatmap shows a consistent spread across the available locations, with no single season collapsing into one city.

## Season Summary
```
season | encounters | avg_length_of_stay | avg_patient_satisfaction | readmission_over_30_rate
-------+------------+--------------------+--------------------------+-------------------------
Winter | 24302      | 4.445848078347461  | 2.9901654184840756       | 35.5%                   
Spring | 24609      | 4.405014425616645  | 3.0159291316185137       | 35.2%                   
Summer | 24722      | 4.402920475689669  | 3.0074832133322547       | 35.1%                   
Fall   | 24420      | 4.4346027846027845 | 3.006838656838657        | 35.5%                   
```

## Location Summary
```
location        | encounters | avg_length_of_stay | avg_patient_satisfaction | readmission_over_30_rate
----------------+------------+--------------------+--------------------------+-------------------------
Phoenix, AZ     | 19703      | 4.430036035121555  | 3.009440186773588        | 35.5%                   
Unknown         | 19687      | 4.417636003454056  | 2.9969015086097426       | 35.7%                   
Los Angeles, CA | 19623      | 4.437242011924782  | 3.006675839576008        | 35.1%                   
Houston, TX     | 19534      | 4.42392751100645   | 2.996058155011774        | 35.0%                   
New York, NY    | 19506      | 4.400902286475956  | 3.016712806316005        | 35.5%                   
```

## Saved Charts
- `thimira_monthly_trend.svg`
- `thimira_season_distribution.svg`
- `thimira_location_distribution.svg`
- `thimira_season_location_heatmap.svg`
