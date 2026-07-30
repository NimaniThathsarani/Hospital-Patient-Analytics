"""
Shared styling for the Doctor Performance Dashboard.
"""


def apply_dashboard_styles() -> str:
    """
    Return custom CSS used across the Streamlit dashboard.

    Returns:
        str: CSS styling for the dashboard.
    """
    return """
    <style>
        .stApp {
            background-color: #f4f7fb;
        }

        .main .block-container {
            max-width: 1400px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            color: #16324f;
        }

        .dashboard-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #16324f;
            margin-bottom: 0.2rem;
        }

        .dashboard-subtitle {
            font-size: 1rem;
            color: #5f6f7f;
            margin-bottom: 1.5rem;
        }

        .kpi-card {
            background: #ffffff;
            border: 1px solid #dce5ee;
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 4px 12px rgba(22, 50, 79, 0.06);
            min-height: 120px;
        }

        .kpi-label {
            font-size: 0.88rem;
            font-weight: 600;
            color: #667788;
            margin-bottom: 8px;
        }

        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #16324f;
        }

        .section-card {
            background: #ffffff;
            border: 1px solid #dce5ee;
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 4px 12px rgba(22, 50, 79, 0.05);
            margin-bottom: 18px;
        }

        [data-testid="stSidebar"] {
            background-color: #16324f;
        }

        [data-testid="stSidebar"] * {
            color: #ffffff;
        }

        [data-testid="stSidebar"] label {
            font-weight: 600;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid #dce5ee;
            border-radius: 10px;
        }

        .data-note {
            background-color: #fff8e7;
            border-left: 4px solid #d6a84b;
            border-radius: 6px;
            padding: 12px 14px;
            color: #5d4a1f;
            margin: 12px 0;
        }
    </style>
    """