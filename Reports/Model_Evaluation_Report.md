# Model Evaluation Report — Admission Forecasting (Squad 3)

## 1. Overview

This report consolidates the work of all three squad members into a single comparison of
admission-forecasting approaches for the hospital's daily, weekly, and monthly patient volumes.

| Person | Contribution |
|---|---|
| A | Data cleaning, daily/weekly/monthly series, EDA, stationarity & seasonality diagnostics |
| B | ARIMA / SARIMA models (`auto_arima`, statsmodels `SARIMAX`) |
| C | Prophet models (daily/weekly/monthly), optional LSTM, model comparison, spike flagging |

## 2. Data & Setup

- Source: Person A's cleaned daily, weekly, and monthly admission counts
  (`data/cleaned/daily_admissions.csv`, `weekly_admissions.csv`, `monthly_admissions.csv`).
- EDA findings (Person A): the daily series is **stationary** (ADF stat = -36.83, p = 0.0; KPSS
  stat = 0.053, p = 0.1), with a **weekly seasonal pattern** (s = 7) and no strong documented
  yearly/holiday effect.
- Train/test split: the **last 6 weeks** of the daily series were held out as the test set
  (same split used by Person B and reused here for Person C's models), with equivalent 12-week
  and 6-month holdouts for the weekly and monthly series respectively.
- All models were scored with the same MAE / RMSE / MAPE function so the numbers are directly
  comparable.

## 3. Model Comparison

| Model | Granularity | MAE | RMSE | MAPE |
|---|---|---|---|---|
| ARIMA/SARIMA | daily | 4.28 | 5.12 | 17.36% |
| Prophet | daily | 4.29 | 5.33 | 17.70% |
| LSTM | daily | 4.33 | 5.13 | 17.46% |
| Prophet | weekly | 19.44 | 37.98 | 23.29% |
| Prophet | monthly | 19.20 | 24.55 | 2.39% |

(Full table: `models/admission_forecasting/model_comparison.csv`)

**Takeaway:** at the daily granularity, ARIMA/SARIMA, Prophet, and LSTM all land within a very
similar error band (MAE ≈ 4.3, MAPE ≈ 17-18%), with ARIMA/SARIMA holding a slight edge on RMSE.
This is consistent with Person A's EDA note that the daily series is close to stationary with
limited structure beyond weekly seasonality — none of the three approaches finds materially more
signal than the others. Prophet's **monthly** forecast is comparatively strong on a percentage
basis (MAPE 2.4%), which fits Prophet's strength on trend + smoothed seasonality at lower-frequency
data; its **weekly** forecast is the weakest of the three granularities and would benefit from more
tuning (e.g. holiday effects, extra regressors) before being used operationally.

**Recommended model:** ARIMA/SARIMA for short-horizon daily staffing decisions; Prophet for
monthly capacity planning, given its lower relative error at that granularity.

Charts:
- `models/admission_forecasting/model_comparison_chart.png` — Actual vs. ARIMA vs. Prophet vs. LSTM (daily test period)
- `models/admission_forecasting/prophet_daily_test_forecast.png`, `lstm_daily_test_forecast.png`, `sarima_test_forecast.png`

## 4. Spike Identification

Using Prophet's 90-day forward forecast (refit on the full daily series) and a threshold of
**mean + 1.5×std ≈ 35 admissions/day**, no day in the next 90 days is forecast to exceed the
threshold. This is a genuine finding rather than a gap in the analysis: it's consistent with the
dataset's stationary, low-variance daily pattern noted in Person A's EDA — there is no strong
seasonal or holiday-driven surge signal in this particular admissions history.

**Resourcing recommendation:** based on the current forecast, no additional staffing action is
indicated for the next 90 days. We recommend re-running the spike check (Section 6 of
`03_prophet_lstm_comparison.ipynb`) each time the forecast is refreshed with new data, since a
future admissions surge (e.g. a real flu-season spike) would immediately surface as a flagged date
range with this same threshold logic.

## 5. Files Produced (Person C)

- `notebooks/03_prophet_lstm_comparison.ipynb` — full Prophet + LSTM pipeline and comparison
- `models/admission_forecasting/prophet_metrics.csv`, `lstm_metrics.csv`, `model_comparison.csv`
- `models/admission_forecasting/prophet_forecast_daily_future.csv` — 90-day forward Prophet forecast
- `models/admission_forecasting/lstm_forecast.csv`
- Charts: `prophet_daily_test_forecast.png`, `prophet_daily_components_fit.png`,
  `lstm_daily_test_forecast.png`, `model_comparison_chart.png`

## 6. Limitations & Next Steps

- The dataset has no real holiday flag column; Prophet's US holiday calendar was used as a proxy
  and its effect wasn't validated against ground truth.
- Weekly/monthly LSTM models were not built (LSTM was scoped to daily only, per the task's
  optional-and-time-permitting guidance).
- All three daily models perform similarly — worth revisiting with additional external features
  (e.g. real holiday/event data, weather, local outbreak data) if more predictive lift is needed.
