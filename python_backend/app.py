# ─── app.py ───────────────────────────────────────────────────────────────────
# Streamlit entry point for the cloud BI analytics workspace
# Run: streamlit run app.py
# ─────────────────────────────────────────────────────────────────────────────

import importlib.util

import pandas as pd
import streamlit as st

from config import (
    APP_DESCRIPTION,
    APP_ICON,
    APP_NAME,
    APP_VERSION,
    DEMO_MODE,
    FIRESTORE_COLLECTIONS,
    PAGES_DIR,
    USE_FIREBASE,
)

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global dark theme override ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: #07070F !important;
    color: #E2E8F0 !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #11111E 0%, #0E0E1C 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
}

div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04) !important;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}

.stButton > button {
    background: linear-gradient(135deg, #4F8EF7, #22D3EE) !important;
    border: none !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 10px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    color: #94A3B8 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4F8EF7, #22D3EE) !important;
    color: white !important;
}

#MainMenu, footer, header { visibility: hidden; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #4F8EF7; border-radius: 2px; }

[data-testid="stSidebarNav"] { display: none !important; }

div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.05) !important;
    border-color: rgba(255,255,255,0.1) !important;
    color: #E2E8F0 !important;
}
</style>
""", unsafe_allow_html=True)

DATASETS = tuple(FIRESTORE_COLLECTIONS.keys())
PAGES = {
    "🏠 Home": PAGES_DIR / "1_Overview.py",
    "📈 Forecasting": PAGES_DIR / "2_Forecasting.py",
    "👥 Customers": PAGES_DIR / "3_Customers.py",
    "🏪 Products": PAGES_DIR / "4_Products.py",
    "⚠️  Anomalies": PAGES_DIR / "5_Anomalies.py",
    "📤 Upload Data": PAGES_DIR / "6_Upload.py",
}


def _normalise_frame(name: str, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "timestamp" in df.columns:
        df["timestamp"] = df["timestamp"].astype(str)
        df = df.sort_values("timestamp")
    elif name == "products" and "revenue" in df.columns:
        df = df.sort_values("revenue", ascending=False)
    elif name == "customers" and {"segment", "ltv"}.issubset(df.columns):
        df = df.sort_values(["segment", "ltv"], ascending=[True, False])

    return df.reset_index(drop=True)


def _load_local_data(message: str, state: str = "info"):
    from data_generator import generate_all

    return generate_all(), {
        "state": state,
        "source": "Sample analytics data",
        "message": message,
    }

def _load_zero_data(message: str, state: str = "info"):
    now = pd.Timestamp.now()
    months = [now - pd.DateOffset(months=i) for i in range(23, -1, -1)]
    kpis = pd.DataFrame({
        "timestamp": [m.strftime("%Y-%m-%dT00:00:00Z") for m in months],
        "month_label": [m.strftime("%b %y") for m in months],
        "revenue": [0.0] * 24, "profit": [0.0] * 24, "profit_pct": [0.0] * 24,
        "cac": [0.0] * 24, "churn": [0.0] * 24, "nps": [0.0] * 24
    })
    empty_data = {
        "kpis": kpis,
        "customers": pd.DataFrame(columns=["segment", "recency", "frequency", "monetary", "ltv", "churn_prob"]),
        "products": pd.DataFrame(columns=["name", "category", "revenue", "growth", "rating"]),
        "anomalies": pd.DataFrame(columns=["timestamp", "metric", "value", "expected", "z_score", "severity"]),
        "activity": pd.DataFrame(columns=["timestamp", "description", "source"]),
        "sales": pd.DataFrame(columns=["step", "base", "pessimistic", "optimistic", "upper", "lower"])
    }
    return empty_data, {
        "state": state,
        "source": "Zero-Initialized Dataset",
        "message": message,
    }


def load_app_data():
    if USE_FIREBASE and not DEMO_MODE:
        from firebase_client import get_db, has_firebase_credentials, read_collection

        if not has_firebase_credentials():
            return _load_local_data(
                "Firebase is enabled, but the Python backend does not have a real "
                "service account yet. Add credentials to "
                "`python_backend/.streamlit/secrets.toml` or set "
                "`GOOGLE_APPLICATION_CREDENTIALS` to load Firestore data.",
                state="warning",
            )

        if get_db() is None:
            return _load_local_data(
                "Firebase credentials were found, but Firestore could not be reached. "
                "Check the service account, project access, and Firestore setup.",
                state="error",
            )

        cloud_data = {
            name: _normalise_frame(name, pd.DataFrame(read_collection(name)))
            for name in DATASETS
        }

        if all(df.empty for df in cloud_data.values()):
            return _load_zero_data(
                "Firestore database is connected, but currently empty. Upload your datasets to begin.",
                state="info",
            )

        missing = [name for name, df in cloud_data.items() if df.empty]
        if missing:
            return cloud_data, {
                "state": "info",
                "source": "Firebase Firestore",
                "message": "Live analytics data loaded, but some collections are empty: " + ", ".join(missing),
            }

        return cloud_data, {
            "state": "success",
            "source": "Firebase Firestore",
            "message": "Live analytics data loaded from Firebase Firestore.",
        }

    reason = (
        "Demo mode is enabled in config.py."
        if DEMO_MODE
        else "Firebase access is disabled in config.py."
    )
    return _load_local_data(
        f"{reason} Showing locally generated analytics data instead of Firestore."
    )


def _save_loaded_data(data, meta):
    st.session_state["data"] = data
    st.session_state["data_meta"] = meta


def _show_data_message(meta):
    message = meta.get("message")
    if not message:
        return

    state = meta.get("state", "info")
    if state == "success":
        st.success(message)
    elif state == "warning":
        st.warning(message)
    elif state == "error":
        st.error(message)
    else:
        st.info(message)


if "data" not in st.session_state or "data_meta" not in st.session_state:
    with st.spinner("Loading analytics workspace …"):
        _save_loaded_data(*load_app_data())

data_meta = st.session_state["data_meta"]

with st.sidebar:
    st.markdown(f"""
    <div style="padding: 1rem 0 1.25rem 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 1rem;">
        <div style="font-size: 1.05rem; line-height: 1.35; font-weight: 800;
                    background: linear-gradient(135deg,#4F8EF7,#22D3EE);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            {APP_NAME}
        </div>
        <div style="font-size: 0.72rem; color: #64748B; margin-top: 6px;">
            v{APP_VERSION} · Cloud Computing Project
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption(f"Data source: {data_meta.get('source', 'Unavailable')}")
    st.markdown("### Navigation")
    page = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")

    st.markdown("---")

    if st.button("🗑️ Clear All Cloud Data (Reset)", use_container_width=True):
        with st.spinner("Deleting all documents from Firebase …"):
            from firebase_client import delete_collection
            for name in DATASETS:
                delete_collection(name)
            _save_loaded_data(*load_app_data())
        st.rerun()

    if st.button("🔄 Seed Firestore With Sample Data", use_container_width=True):
        with st.spinner("Generating and pushing new data (this takes ~15s) …"):
            from data_generator import seed_firestore
            from firebase_client import has_firebase_credentials

            push_to_firestore = USE_FIREBASE and has_firebase_credentials()
            data = seed_firestore(push=push_to_firestore)
            meta = {
                "state": "success" if push_to_firestore else "warning",
                "source": "Firebase Firestore" if push_to_firestore else "Sample analytics data",
                "message": (
                    "Sample analytics data generated and pushed to Firebase Firestore."
                    if push_to_firestore
                    else "Sample analytics data generated locally. Firestore was not "
                    "updated because backend Firebase credentials are not configured."
                ),
            }
            _save_loaded_data(data, meta)
        st.rerun()

    st.markdown(f"""
    <div style="position: fixed; bottom: 1.5rem; left: 1rem;
                font-size: 0.7rem; color: #334155;">
        Firebase · Streamlit · Plotly<br/>
        Business Intelligence Analytics
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div style="padding: 0.25rem 0 1rem 0;">
    <div style="font-size: 2rem; font-weight: 800; color: #E2E8F0; line-height: 1.2;">
        {APP_NAME}
    </div>
    <div style="font-size: 0.95rem; color: #94A3B8; margin-top: 0.45rem;">
        {APP_DESCRIPTION}
    </div>
</div>
""", unsafe_allow_html=True)
_show_data_message(data_meta)

page_file = str(PAGES[page])
spec = importlib.util.spec_from_file_location("page_module", page_file)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
