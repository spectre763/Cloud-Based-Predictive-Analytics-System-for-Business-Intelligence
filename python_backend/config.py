# ─── config.py ───────────────────────────────────────────────────────────────
# Central configuration for the Predictive Analytics Backend
# ─────────────────────────────────────────────────────────────────────────────

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
PAGES_DIR  = BASE_DIR / "pages"
ASSETS_DIR = BASE_DIR / "assets"

# ── App Meta ───────────────────────────────────────────────────────────────
APP_NAME        = "Cloud-Based Predictive Analytics System for Business Intelligence"
APP_VERSION     = "1.0.0"
APP_ICON        = "📊"
APP_DESCRIPTION = (
    "Firebase-backed business intelligence workspace for forecasting, customer "
    "analytics, product performance, and anomaly monitoring."
)

# ── Data Generation ────────────────────────────────────────────────────────
SEED              = 42          # NumPy random seed for reproducibility
HISTORY_MONTHS    = 24          # Months of historical data to generate
FORECAST_MONTHS   = 6           # Months ahead to forecast
NUM_CUSTOMERS     = 100         # Synthetic customer records
NUM_PRODUCTS      = 15          # Products in catalogue
ANOMALY_INJECT    = True        # Whether to inject synthetic anomalies

# ── Revenue Baseline (USD) ──────────────────────────────────────────────────
BASE_REVENUE       = 850_000    # Monthly base revenue
REVENUE_GROWTH     = 0.015      # MoM growth rate
REVENUE_SEASONALITY = 0.18      # Amplitude of seasonal variation
REVENUE_NOISE      = 0.06       # Random noise fraction

# ── Forecast Scenarios ──────────────────────────────────────────────────────
SCENARIOS = {
    "Pessimistic": -0.08,
    "Base":         0.00,
    "Optimistic":  +0.12,
}

CONFIDENCE_UPPER = 0.15   # +15% upper bound
CONFIDENCE_LOWER = 0.10   # -10% lower bound

# ── Customer Segments ───────────────────────────────────────────────────────
SEGMENTS = ["Champions", "Loyal", "Potential", "At Risk", "Lost"]
SEGMENT_COLORS = {
    "Champions":  "#10B981",
    "Loyal":      "#4F8EF7",
    "Potential":  "#9B6FEA",
    "At Risk":    "#F59E0B",
    "Lost":       "#F43F5E",
}
SEGMENT_WEIGHTS = [0.15, 0.25, 0.30, 0.20, 0.10]

# ── Anomaly Detection ───────────────────────────────────────────────────────
ANOMALY_ZSCORE_THRESHOLD = 2.5
ANOMALY_SEVERITY_MAP = {
    "critical": {"z_min": 3.5, "color": "#F43F5E"},
    "warning":  {"z_min": 2.5, "color": "#F59E0B"},
    "info":     {"z_min": 0.0, "color": "#4F8EF7"},
}

# ── Streamlit UI ────────────────────────────────────────────────────────────
REFRESH_INTERVAL  = 30     # seconds between auto-refresh
CHART_HEIGHT      = 400    # default Plotly chart height (px)
TABLE_PAGE_SIZE   = 15     # rows per page in data tables

# ── Firebase ────────────────────────────────────────────────────────────────
FIRESTORE_COLLECTIONS = {
    "kpis":       "kpis",
    "sales":      "sales",
    "customers":  "customers",
    "products":   "products",
    "anomalies":  "anomalies",
    "activity":   "activity",
}

# ── Feature flags ───────────────────────────────────────────────────────────
USE_FIREBASE      = True   # Set False to run in local-only mode (no Firebase)
DEMO_MODE         = False  # Set True to force local sample data only
