"""
Shared styling for the Doctor Performance Dashboard.
"""


def apply_dashboard_styles() -> str:
    """
    Return custom CSS used across the Streamlit dashboard.

    Returns:
        CSS styling for the complete dashboard.
    """
    return """
    <style>
        /* Main application */
        .stApp {
            background-color: #f4f7fb;
            color: #16324f;
        }

        .main .block-container {
            max-width: 1500px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        /* Dashboard heading */
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

        /* Main content headings */
        [data-testid="stMain"] h1,
        [data-testid="stMain"] h2,
        [data-testid="stMain"] h3,
        [data-testid="stMain"] h4 {
            color: #16324f !important;
        }

        /* Main widget labels */
        [data-testid="stMain"] [data-testid="stWidgetLabel"] p {
            color: #334e68 !important;
            font-weight: 600;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #dce5ee;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(22, 50, 79, 0.06);
            min-height: 118px;
        }

        [data-testid="stMetricLabel"] p {
            color: #667788 !important;
            font-size: 0.88rem;
            font-weight: 600;
        }

        [data-testid="stMetricValue"] {
            color: #16324f !important;
            font-weight: 700;
        }

        [data-testid="stMetricDelta"] {
            color: #334e68 !important;
        }

        /* Alert messages */
        [data-testid="stAlert"][data-baseweb="notification"] {
            border-radius: 10px;
        }

        [data-testid="stAlert"] p {
            color: #2c3e50 !important;
            font-weight: 500;
        }

        div[data-testid="stAlert"]:has(
            [data-testid="stAlertContentWarning"]
        ) {
            background-color: #fff4cc !important;
            border: 1px solid #e7c55a !important;
        }

        div[data-testid="stAlert"]:has(
            [data-testid="stAlertContentInfo"]
        ) {
            background-color: #dceeff !important;
            border: 1px solid #8fc0ea !important;
        }

        div[data-testid="stAlert"]:has(
            [data-testid="stAlertContentSuccess"]
        ) {
            background-color: #dcf5e7 !important;
            border: 1px solid #80c99f !important;
        }

        div[data-testid="stAlert"]:has(
            [data-testid="stAlertContentError"]
        ) {
            background-color: #fde2e2 !important;
            border: 1px solid #dc8d8d !important;
        }

        /* Download buttons */
        [data-testid="stDownloadButton"] button {
            background-color: #163a5c !important;
            border: 1px solid #163a5c !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            padding: 0.55rem 1rem !important;
            transition:
                background-color 0.2s ease,
                border-color 0.2s ease,
                transform 0.2s ease;
        }

        [data-testid="stDownloadButton"] button p,
        [data-testid="stDownloadButton"] button span,
        [data-testid="stDownloadButton"] button div {
            color: #ffffff !important;
        }

        [data-testid="stDownloadButton"] button:hover {
            background-color: #245d87 !important;
            border-color: #245d87 !important;
            color: #ffffff !important;
            transform: translateY(-1px);
        }

        [data-testid="stDownloadButton"] button:focus {
            background-color: #163a5c !important;
            border-color: #7fb3d5 !important;
            color: #ffffff !important;
            box-shadow: 0 0 0 0.2rem rgba(127, 179, 213, 0.3);
        }

        [data-testid="stDownloadButton"] button:active {
            background-color: #102d47 !important;
            border-color: #102d47 !important;
            color: #ffffff !important;
            transform: translateY(0);
        }

        /* Custom cards */
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

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #163a5c;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: #ffffff;
        }

        [data-testid="stSidebar"] label {
            font-weight: 600;
        }

        /* Select and multiselect widgets */
        [data-baseweb="select"] > div {
            background-color: #111827;
            border-color: #334155;
            color: #ffffff;
        }

        [data-baseweb="popover"] {
            color: #ffffff;
        }

        [data-baseweb="popover"] ul {
            background-color: #10141c;
        }

        [data-baseweb="popover"] li {
            color: #ffffff;
        }

        /* Data tables */
        [data-testid="stDataFrame"] {
            border: 1px solid #dce5ee;
            border-radius: 10px;
            overflow: hidden;
        }

        /* Custom data note */
        .data-note {
            background-color: #fff4cc;
            border: 1px solid #e7c55a;
            border-left: 4px solid #d6a84b;
            border-radius: 8px;
            padding: 12px 14px;
            color: #5d4a1f;
            margin: 12px 0;
        }

        /* Captions */
        [data-testid="stCaptionContainer"] {
            color: #60758a !important;
        }

        hr {
            border-color: #d6e0e9;
        }
    </style>
    """