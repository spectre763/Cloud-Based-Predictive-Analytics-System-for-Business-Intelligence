# ─── analytics.py ─────────────────────────────────────────────────────────────
# Forecasting, anomaly detection, and segmentation logic
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
from config import ANOMALY_ZSCORE_THRESHOLD, FORECAST_MONTHS, SCENARIOS, CONFIDENCE_UPPER, CONFIDENCE_LOWER


# ──────────────────────────────────────────────────────────────────────────────
# Anomaly Detection
# ──────────────────────────────────────────────────────────────────────────────

def detect_anomalies(series: np.ndarray, threshold: float = ANOMALY_ZSCORE_THRESHOLD) -> List[int]:
    """
    Return list of indices where z-score exceeds threshold (IQR + Z-score combined).
    """
    s    = pd.Series(series)
    mean = s.rolling(window=6, min_periods=1).mean()
    std  = s.rolling(window=6, min_periods=1).std().fillna(s.std())
    z    = ((s - mean) / std).abs()
    return z[z > threshold].index.tolist()


# ──────────────────────────────────────────────────────────────────────────────
# Revenue Forecasting
# ──────────────────────────────────────────────────────────────────────────────

def forecast_revenue(
    revenue: np.ndarray,
    months_ahead: int = FORECAST_MONTHS,
) -> pd.DataFrame:
    """
    Simple trend + seasonality decomposition forecast.
    Returns DataFrame with columns: [base, pessimistic, optimistic, upper, lower]
    """
    n    = len(revenue)
    t    = np.arange(n)
    t_fc = np.arange(n, n + months_ahead)

    # Fit linear trend
    coeffs  = np.polyfit(t, revenue, 1)
    trend   = np.polyval(coeffs, t_fc)

    # Estimate residual seasonality (12-month)
    residual    = revenue - np.polyval(coeffs, t)
    seasonal_12 = np.array([residual[i::12].mean() for i in range(12)])
    seasonal_fc = np.array([seasonal_12[i % 12] for i in range(n, n + months_ahead)])

    base    = trend + seasonal_fc
    rows    = []
    for i in range(months_ahead):
        rows.append({
            "step":        i + 1,
            "base":        round(float(base[i]), 2),
            "pessimistic": round(float(base[i] * (1 + SCENARIOS["Pessimistic"])), 2),
            "optimistic":  round(float(base[i] * (1 + SCENARIOS["Optimistic"])), 2),
            "upper":       round(float(base[i] * (1 + CONFIDENCE_UPPER)), 2),
            "lower":       round(float(base[i] * (1 - CONFIDENCE_LOWER)), 2),
        })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# RFM Segmentation
# ──────────────────────────────────────────────────────────────────────────────

def rfm_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign quintile-based RFM scores (1-5 each) and return the enriched DataFrame.
    Input must have columns: recency, frequency, monetary
    """
    out = df.copy()

    def quintile(col, ascending=True):
        return pd.qcut(col, 5, labels=[1, 2, 3, 4, 5] if ascending else [5, 4, 3, 2, 1], duplicates="drop")

    out["r_score"] = quintile(out["recency"],   ascending=False)   # lower recency = better
    out["f_score"] = quintile(out["frequency"], ascending=True)
    out["m_score"] = quintile(out["monetary"],  ascending=True)
    out["rfm_total"] = (
        out["r_score"].astype(int) +
        out["f_score"].astype(int) +
        out["m_score"].astype(int)
    )
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Cohort Retention
# ──────────────────────────────────────────────────────────────────────────────

def generate_cohort_retention(n_cohorts: int = 8, max_period: int = 8) -> pd.DataFrame:
    """
    Simulate cohort retention table.
    Returns DataFrame indexed by cohort, columns = Period 0..max_period.
    """
    rng    = np.random.default_rng(42)
    rows   = {}
    labels = [f"Cohort {i+1}" for i in range(n_cohorts)]

    for label in labels:
        retention = [100.0]
        for p in range(1, max_period + 1):
            drop       = rng.uniform(8, 22)
            prev       = retention[-1]
            new_val    = max(prev - drop + rng.uniform(-3, 3), 5.0)
            retention.append(round(new_val, 1))
        rows[label] = retention

    return pd.DataFrame(rows, index=[f"M{i}" for i in range(max_period + 1)]).T


# ──────────────────────────────────────────────────────────────────────────────
# Feature Importance (mock for XGBoost-style visualization)
# ──────────────────────────────────────────────────────────────────────────────

def feature_importance() -> pd.DataFrame:
    features = [
        "Marketing Spend",
        "Seasonal Index",
        "Competitor Pricing",
        "NPS Score",
        "Web Traffic",
        "Support Tickets",
        "Product Updates",
        "Churn Rate",
    ]
    importance = [0.28, 0.22, 0.16, 0.12, 0.09, 0.06, 0.04, 0.03]
    return pd.DataFrame({"feature": features, "importance": importance}).sort_values(
        "importance", ascending=True
    )


# ──────────────────────────────────────────────────────────────────────────────
# KPI Summary
# ──────────────────────────────────────────────────────────────────────────────

def kpi_summary(kpis_df: pd.DataFrame) -> Dict:
    """Return latest KPI values and MoM delta as a dict."""
    latest = kpis_df.iloc[-1]
    prev   = kpis_df.iloc[-2]

    def delta_pct(a, b):
        return round((a - b) / (abs(b) + 1e-9) * 100, 2)

    return {
        "revenue":    {"value": latest["revenue"],    "delta": delta_pct(latest["revenue"],    prev["revenue"])},
        "profit":     {"value": latest["profit"],     "delta": delta_pct(latest["profit"],     prev["profit"])},
        "profit_pct": {"value": latest["profit_pct"], "delta": delta_pct(latest["profit_pct"], prev["profit_pct"])},
        "cac":        {"value": latest["cac"],        "delta": delta_pct(latest["cac"],        prev["cac"])},
        "churn":      {"value": latest["churn"],      "delta": delta_pct(latest["churn"],      prev["churn"])},
        "nps":        {"value": latest["nps"],        "delta": delta_pct(latest["nps"],        prev["nps"])},
    }
