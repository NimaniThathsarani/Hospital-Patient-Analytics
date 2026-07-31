# Risk Assessment Report
High-Risk Patient Identification for Hospital Resource Allocation

Dataset: `final_dataset.csv` — 98,053 inpatient encounters, 68,630 unique patients (1999–2008)
Companion notebook: `Risk_Analysis_Notebook.ipynb`

## 1. Objective

This report identifies which patients are at highest risk of an unplanned 30-day readmission, so care coordination teams have a ranked, explainable list of patients to prioritize.

## 2. Method (brief)

- **Target:** readmission within 30 days (11.3% of encounters), since it's the strongest sign of a preventable gap in care — the dataset only labels ">30 days" (35.3%) and "not readmitted" (53.4%).
- **Model:** Gradient Boosting classifier on 20 engineered features (prior utilization, medication complexity, discharge disposition, demographics), compared against Logistic Regression.
- **Composite Risk Score (0–100):** predicted probability (40%) + age (20%) + prior utilization (20%) + comorbidity count (10%) + high-risk discharge disposition (10%).
- **Risk tiers:** based on the population's own score distribution — Critical (top 5%), High (next 15%), Medium (next 30%), Low (bottom 50%) — so tiers stay meaningfully sized.

## 3. Key Findings

**Model performance:** Gradient Boosting reached an AUC of 0.644 (Logistic Regression: 0.638). This is a modest but genuine signal, consistent with published benchmarks for readmission models built from administrative data alone — useful for prioritization, not for certainty about any one patient.

**Top predictors:** prior inpatient admissions dominate (57% of model weight), followed by high-risk discharge disposition (12%) and other prior-utilization measures.

**Risk tier distribution:**

| Tier | Encounters | Share |
|---|---|---|
| Critical | 4,903 | 5.0% |
| High | 14,708 | 15.0% |
| Medium | 29,416 | 30.0% |
| Low | 49,026 | 50.0% |

**Validation:** actual 30-day readmission rate is 17.7% for Critical+High patients vs. 7.5% for Low — roughly 2.4x higher, confirming the score genuinely separates risk.

## 4. Limitations

- AUC of 0.64 leaves real uncertainty at the individual-patient level; the model should support, not replace, clinical judgment.
- No clinical notes, lab trends, or socioeconomic data are available — adding these would likely improve accuracy.
- Scoring weights are a literature-informed starting point, not tuned against a downstream cost/outcome metric.

## 5. Conclusion

About 1 in 5 patients (Critical + High, 19,611 encounters) carry meaningfully elevated readmission risk, driven mainly by prior hospital utilization and discharge circumstances. The full ranked list is in `patient_risk_scores.csv`.