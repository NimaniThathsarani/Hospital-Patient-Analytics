# Hospital Patient Analytics - Patient Segmentation

## Project Overview

This project performs patient segmentation using the K-Means clustering algorithm. The objective is to group patients with similar demographic, clinical, and healthcare utilization characteristics into distinct clusters.

## Dataset

Input Dataset:

- final_dataset.csv

Dataset Size:

- 98,053 patient records
- 65 original features

## Methodology

### Data Preprocessing

- Removed identifier columns
  - encounter_id
  - patient_nbr

- Removed columns with excessive missing values
  - max_glu_serum
  - A1Cresult

- Converted age ranges into numerical values

- Removed diagnosis code columns
  - diag_1
  - diag_2
  - diag_3

- Encoded medication-related categorical features

- Converted boolean features into numeric values

### Feature Scaling

- Applied StandardScaler to standardize feature values before clustering.

### Clustering

- Algorithm: K-Means Clustering
- Tested multiple cluster counts using the Elbow Method
- Final Number of Clusters (K): 4

### Evaluation

- Silhouette Score: 0.0592

## Results

Patient records were segmented into four clusters.

Cluster Distribution:

| Cluster | Patients |
|----------|----------|
| 0 | 1,984 |
| 1 | 19,266 |
| 2 | 33,155 |
| 3 | 43,648 |

## Project Structure

## Data Encoding

Medication Features:

| Original Value | Encoded Value |
|---------------|---------------|
| No | 0 |
| Steady | 1 |
| Up | 2 |
| Down | 3 |

These encodings were applied to medication-related columns such as:

- metformin
- insulin
- glipizide
- glyburide
- and other diabetes medications.

## Cluster Information

The Cluster column represents the patient segment assigned by the K-Means clustering model.

| Cluster ID |
|------------|
| 0 |
| 1 |
| 2 |
| 3 |

The numerical cluster IDs do not have predefined meanings. Detailed interpretation of each segment should be performed using cluster profile analysis.

## Output Dataset

The file `final_dataset_clustered.csv` contains:

- All processed patient features
- Encoded medication features
- A final `Cluster` column generated using K-Means clustering

This dataset is intended for:

- Cluster profiling
- Patient segment analysis
- Data visualization
- Healthcare insights and reporting