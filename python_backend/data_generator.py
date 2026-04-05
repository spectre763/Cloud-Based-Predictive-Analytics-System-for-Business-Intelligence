# ─── data_generator.py ─────────────────────────────────────────────────────
# Generates realistic synthetic business time-series data and pushes to Firestore
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
import uuid, logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from config import (
    SEED, HISTORY_MONTHS, FORECAST_MONTHS, NUM_CUSTOMERS, NUM_PRODUCTS,
    BASE_REVENUE, REVENUE_GROWTH, REVENUE_SEASONALITY, REVENUE_NOISE,
    SCENARIOS, CONFIDENCE_UPPER, CONFIDENCE_LOWER,
    SEGMENTS, SEGMENT_WEIGHTS, ANOMALY_INJECT,
)

logger = logging.getLogger(__name__)
rng = np.random.default_rng(SEED)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _month_range(months: int, start: datetime | None = None) -> List[datetime]:
    if start is None:
        start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start -= timedelta(days=30 * months)
    return [start + timedelta(days=30 * i) for i in range(months)]


def _seasonal(t: np.ndarray, amplitude: float = 1.0, period: int = 12) -> np.ndarray:
    return amplitude * np.sin(2 * np.pi * t / period)


# ──────────────────────────────────────────────────────────────────────────────
# KPI & Sales data
# ──────────────────────────────────────────────────────────────────────────────

def generate_kpis() -> pd.DataFrame:
    """Generate monthly KPI snapshots."""
    months = _month_range(HISTORY_MONTHS)
    t      = np.arange(HISTORY_MONTHS)

    revenue = (
        BASE_REVENUE
        * (1 + REVENUE_GROWTH) ** t
        * (1 + _seasonal(t, REVENUE_SEASONALITY))
        * (1 + rng.normal(0, REVENUE_NOISE, HISTORY_MONTHS))
    )

    # Correlated KPIs
    cac        = 180 + rng.normal(0, 15, HISTORY_MONTHS) - t * 0.4
    churn      = np.clip(0.045 - t * 0.0005 + rng.normal(0, 0.003, HISTORY_MONTHS), 0.01, 0.09)
    nps        = np.clip(52 + t * 0.3 + rng.normal(0, 3, HISTORY_MONTHS), 30, 80)
    profit_pct = np.clip(0.22 + t * 0.001 + rng.normal(0, 0.015, HISTORY_MONTHS), 0.10, 0.40)

    records = []
    for i, dt in enumerate(months):
        records.append({
            "_id":        dt.strftime("%Y-%m"),
            "timestamp":  dt.isoformat(),
            "month_label": dt.strftime("%b %Y"),
            "revenue":    round(float(revenue[i]), 2),
            "profit":     round(float(revenue[i] * profit_pct[i]), 2),
            "profit_pct": round(float(profit_pct[i] * 100), 2),
            "cac":        round(float(max(cac[i], 80)), 2),
            "churn":      round(float(churn[i] * 100), 3),
            "nps":        round(float(nps[i]), 1),
        })

    return pd.DataFrame(records)


def generate_sales_forecast(kpis_df: pd.DataFrame) -> pd.DataFrame:
    """Extend KPI revenue with multi-scenario 6-month forecast + confidence bands."""
    last_revenue = kpis_df["revenue"].iloc[-1]
    last_date    = datetime.fromisoformat(kpis_df["timestamp"].iloc[-1])
    t_hist       = np.arange(HISTORY_MONTHS)

    # Simple linear trend over last 6 months
    recent    = kpis_df["revenue"].values[-6:]
    slope     = np.polyfit(np.arange(6), recent, 1)[0]
    seasonal  = _seasonal(np.arange(HISTORY_MONTHS, HISTORY_MONTHS + FORECAST_MONTHS),
                          REVENUE_SEASONALITY * last_revenue)

    records = []

    # Historical actuals
    for _, row in kpis_df.iterrows():
        records.append({
            "_id":        row["_id"] + "_hist",
            "timestamp":  row["timestamp"],
            "month_label": row["month_label"],
            "actual":      row["revenue"],
            "base":        None,
            "pessimistic": None,
            "optimistic":  None,
            "upper":       None,
            "lower":       None,
            "is_forecast": False,
        })

    # Forecast months
    for i in range(FORECAST_MONTHS):
        dt     = last_date + timedelta(days=30 * (i + 1))
        base   = last_revenue + slope * (i + 1) + seasonal[i]
        upper  = base * (1 + CONFIDENCE_UPPER)
        lower  = base * (1 - CONFIDENCE_LOWER)

        records.append({
            "_id":        dt.strftime("%Y-%m") + "_fc",
            "timestamp":  dt.isoformat(),
            "month_label": dt.strftime("%b %Y"),
            "actual":      None,
            "base":        round(base, 2),
            "pessimistic": round(base * (1 + SCENARIOS["Pessimistic"]), 2),
            "optimistic":  round(base * (1 + SCENARIOS["Optimistic"]), 2),
            "upper":       round(upper, 2),
            "lower":       round(lower, 2),
            "is_forecast": True,
        })

    return pd.DataFrame(records)


# ──────────────────────────────────────────────────────────────────────────────
# Customers
# ──────────────────────────────────────────────────────────────────────────────

def generate_customers() -> pd.DataFrame:
    n        = NUM_CUSTOMERS
    segments = rng.choice(SEGMENTS, size=n, p=SEGMENT_WEIGHTS)

    # RFM scores differ per segment
    seg_params = {
        "Champions":  dict(r=(1,5),  f=(8,15), m=(800,3000)),
        "Loyal":      dict(r=(3,10), f=(5,10), m=(400,1200)),
        "Potential":  dict(r=(5,15), f=(2,6),  m=(150,600)),
        "At Risk":    dict(r=(15,35),f=(1,4),  m=(50,300)),
        "Lost":       dict(r=(40,90),f=(1,2),  m=(10,100)),
    }

    records = []
    for i in range(n):
        seg = segments[i]
        p   = seg_params[seg]
        r   = int(rng.integers(*p["r"]))
        f   = int(rng.integers(*p["f"]))
        m   = round(float(rng.uniform(*p["m"])), 2)
        ltv = round(m * f * rng.uniform(0.8, 2.5), 2)
        churn_prob = {
            "Champions": rng.uniform(0.02, 0.08),
            "Loyal":     rng.uniform(0.05, 0.15),
            "Potential": rng.uniform(0.15, 0.30),
            "At Risk":   rng.uniform(0.35, 0.65),
            "Lost":      rng.uniform(0.60, 0.95),
        }[seg]

        records.append({
            "_id":        str(uuid.uuid4()),
            "segment":    seg,
            "recency":    r,
            "frequency":  f,
            "monetary":   m,
            "ltv":        ltv,
            "churn_prob": round(float(churn_prob), 3),
            "country":    rng.choice(["US","IN","UK","DE","FR","JP","CA","AU","BR","SG"]),
            "joined_days": int(rng.integers(10, 900)),
        })

    return pd.DataFrame(records)


# ──────────────────────────────────────────────────────────────────────────────
# Products
# ──────────────────────────────────────────────────────────────────────────────

PRODUCT_NAMES = [
    "Analytics Pro","DataVault","InsightHub","CloudSync","MetricFlow",
    "PulseBoard","CoreReport","SignalAI","NexusMap","TrendLens",
    "BIConnect","FlowTrack","SmartPivot","AuditGuard","StreamLine",
    "DataBridge","RevenueIQ","PredictEngine","AlertMesh","QueryForge",
]

CATEGORIES = ["SaaS", "Platform", "Add-On", "Enterprise", "Starter"]

def generate_products() -> pd.DataFrame:
    n = min(NUM_PRODUCTS, len(PRODUCT_NAMES) * 2)
    records = []
    for i in range(n):
        name     = PRODUCT_NAMES[i % len(PRODUCT_NAMES)] + (f" {i//len(PRODUCT_NAMES)+1}" if i >= len(PRODUCT_NAMES) else "")
        category = rng.choice(CATEGORIES)
        units    = int(rng.integers(50, 2000))
        price    = round(float(rng.uniform(29, 499)), 2)
        revenue  = round(units * price * rng.uniform(0.8, 1.0), 2)
        growth   = round(float(rng.uniform(-0.12, 0.45)), 3)
        market_share = round(float(rng.uniform(0.02, 0.18)), 3)

        records.append({
            "_id":          str(uuid.uuid4()),
            "name":         name,
            "category":     category,
            "units":        units,
            "price":        price,
            "revenue":      revenue,
            "growth":       growth,
            "market_share": market_share,
            "rating":       round(float(rng.uniform(3.2, 4.9)), 1),
        })

    return pd.DataFrame(records)


# ──────────────────────────────────────────────────────────────────────────────
# Anomalies
# ──────────────────────────────────────────────────────────────────────────────

def generate_anomalies(kpis_df: pd.DataFrame) -> pd.DataFrame:
    """Detect and inject anomalies in the revenue series."""
    from analytics import detect_anomalies          # local import to avoid circular
    revenue    = kpis_df["revenue"].values
    anomalies  = detect_anomalies(revenue)
    records    = []

    for idx in anomalies:
        row      = kpis_df.iloc[idx]
        expected = float(kpis_df["revenue"].iloc[max(0, idx-3):idx].mean())
        actual   = float(row["revenue"])
        z        = abs(actual - expected) / (float(kpis_df["revenue"].std()) + 1e-9)

        severity = "info"
        if z >= 3.5:
            severity = "critical"
        elif z >= 2.5:
            severity = "warning"

        records.append({
            "_id":      str(uuid.uuid4()),
            "metric":   "revenue",
            "timestamp": row["timestamp"],
            "month_label": row["month_label"],
            "value":    actual,
            "expected": round(expected, 2),
            "z_score":  round(z, 3),
            "severity": severity,
            "resolved": bool(rng.choice([True, False], p=[0.4, 0.6])),
        })

    # Inject a couple of extra synthetic anomalies (churn spike, CAC spike)
    for metric, col, factor in [("churn", "churn", 1.9), ("cac", "cac", 1.7)]:
        idx  = int(rng.integers(3, len(kpis_df) - 3))
        row  = kpis_df.iloc[idx]
        base = float(kpis_df[col].mean())
        val  = base * factor
        records.append({
            "_id":      str(uuid.uuid4()),
            "metric":   metric,
            "timestamp": row["timestamp"],
            "month_label": row["month_label"],
            "value":    round(val, 3),
            "expected": round(base, 3),
            "z_score":  round(factor * 1.2, 2),
            "severity": "warning",
            "resolved": False,
        })

    return pd.DataFrame(records)


# ──────────────────────────────────────────────────────────────────────────────
# Activity Feed
# ──────────────────────────────────────────────────────────────────────────────

ACTIVITY_ITEMS = [
    ("🆕 New deal closed",      "Sales",    "deal_closed"),
    ("⚠️  Anomaly detected",    "System",   "anomaly"),
    ("📊 Report generated",     "BI",       "report"),
    ("👤 New customer signup",  "CRM",      "signup"),
    ("🔔 Churn risk alert",     "CRM",      "churn_risk"),
    ("📈 Forecast updated",     "Analytics","forecast"),
    ("✅ Goal achieved",        "Sales",    "goal"),
    ("🔄 Data sync complete",   "System",   "sync"),
]

def generate_activity(n: int = 30) -> pd.DataFrame:
    now     = datetime.utcnow()
    records = []
    for i in range(n):
        item = ACTIVITY_ITEMS[i % len(ACTIVITY_ITEMS)]
        records.append({
            "_id":        str(uuid.uuid4()),
            "description": item[0],
            "source":     item[1],
            "type":       item[2],
            "timestamp":  (
                now - timedelta(minutes=int(i * 47 + rng.integers(0, 30)))
            ).isoformat(),
        })
    return pd.DataFrame(records)


# ──────────────────────────────────────────────────────────────────────────────
# Master seed function
# ──────────────────────────────────────────────────────────────────────────────

def generate_all() -> Dict[str, pd.DataFrame]:
    """Generate all datasets and return as a dict of DataFrames."""
    logger.info("Generating KPIs …")
    kpis     = generate_kpis()

    logger.info("Generating sales forecast …")
    sales    = generate_sales_forecast(kpis)

    logger.info("Generating customers …")
    customers = generate_customers()

    logger.info("Generating products …")
    products = generate_products()

    logger.info("Generating anomalies …")
    anomalies = generate_anomalies(kpis)

    logger.info("Generating activity …")
    activity  = generate_activity()

    return {
        "kpis":      kpis,
        "sales":     sales,
        "customers": customers,
        "products":  products,
        "anomalies": anomalies,
        "activity":  activity,
    }


def seed_firestore(push: bool = True) -> Dict[str, pd.DataFrame]:
    """Generate data and optionally push to Firestore. Returns the DataFrames."""
    data = generate_all()

    if push:
        from firebase_client import batch_write, delete_collection
        for name, df in data.items():
            logger.info("Seeding '%s' (%d rows) …", name, len(df))
            delete_collection(name)
            batch_write(name, df.to_dict("records"))
        logger.info("Firestore seeded successfully.")

    return data
