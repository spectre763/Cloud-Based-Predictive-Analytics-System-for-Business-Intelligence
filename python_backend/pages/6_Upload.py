import io
import pandas as pd
import streamlit as st

from firebase_client import batch_write, delete_collection, has_firebase_credentials, USE_FIREBASE

st.markdown("# 📤 Upload Dataset")
st.markdown("Upload your own business data as a CSV file to sync it directly with your Firebase dashboard.")

if not USE_FIREBASE or not has_firebase_credentials():
    st.warning("Firebase is not properly configured. Uploads will run locally but not sync to the cloud.")

# ── Define schemas for validation and templates ──────────────────────────────────
COLLECTIONS = {
    "kpis": {
        "title": "Monthly KPIs",
        "desc": "Core monthly business metrics used for the overview and forecasting charts.",
        "cols": ["month_label", "revenue", "profit", "profit_pct", "cac", "churn", "nps"],
        "dtypes": {"month_label": "str", "revenue": "float", "profit": "float", "profit_pct": "float", "cac": "float", "churn": "float", "nps": "float"},
        "sample": [
            {"month_label": "Jan 2026", "revenue": 850000, "profit": 195500, "profit_pct": 23.0, "cac": 150.5, "churn": 4.5, "nps": 65.0},
            {"month_label": "Feb 2026", "revenue": 870000, "profit": 201000, "profit_pct": 23.1, "cac": 145.0, "churn": 4.3, "nps": 66.2},
        ]
    },
    "customers": {
        "title": "Customer Data",
        "desc": "Customer segmentation, retention, and lifetime value data.",
        "cols": ["segment", "recency", "frequency", "monetary", "ltv", "churn_prob"],
        "dtypes": {"segment": "str", "recency": "int", "frequency": "int", "monetary": "float", "ltv": "float", "churn_prob": "float"},
        "sample": [
            {"segment": "Champions", "recency": 12, "frequency": 8, "monetary": 2500, "ltv": 15000, "churn_prob": 0.05},
            {"segment": "At Risk", "recency": 65, "frequency": 2, "monetary": 120, "ltv": 450, "churn_prob": 0.55},
        ]
    },
    "products": {
        "title": "Product Catalogue",
        "desc": "Product performance and revenue contribution data.",
        "cols": ["name", "category", "revenue", "growth", "rating"],
        "dtypes": {"name": "str", "category": "str", "revenue": "float", "growth": "float", "rating": "float"},
        "sample": [
            {"name": "Analytics Pro", "category": "SaaS", "revenue": 120000, "growth": 0.15, "rating": 4.8},
            {"name": "DataVault", "category": "Platform", "revenue": 85000, "growth": -0.02, "rating": 4.1},
        ]
    }
}

target_key = st.selectbox(
    "Select target collection to replace:",
    options=list(COLLECTIONS.keys()),
    format_func=lambda x: COLLECTIONS[x]["title"]
)

schema = COLLECTIONS[target_key]
st.caption(schema["desc"])

# ── Download Template ────────────────────────────────────────────────────────────
template_df = pd.DataFrame(schema["sample"])
csv_buffer = io.StringIO()
template_df.to_csv(csv_buffer, index=False)

st.download_button(
    label=f"📥 Download {schema['title']} CSV Template",
    data=csv_buffer.getvalue(),
    file_name=f"{target_key}_template.csv",
    mime="text/csv",
)

st.markdown("---")

# ── File Uploader ────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload your filled CSV dataset here", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Validation
        missing_cols = [c for c in schema["cols"] if c not in df.columns]
        if missing_cols:
            st.error(f"Validation failed. Missing required columns: {missing_cols}")
        else:
            st.success(f"File uploaded successfully! ({len(df)} rows found)")
            
            with st.expander("Preview data", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)

            if st.button("🚀 Confirm & Sync to Firebase", type="primary", use_container_width=True):
                with st.spinner(f"Overwriting '{target_key}' collection in Firebase..."):
                    # Process and clean
                    df = df.dropna(subset=schema["cols"])
                    
                    if "timestamp" not in df.columns and target_key == "kpis":
                        # Auto-generate iso timestamps if missing
                        df["timestamp"] = pd.date_range(start="2024-01-01", periods=len(df), freq="M").astype(str)

                    records = df.to_dict(orient="records")
                    
                    if USE_FIREBASE:
                        delete_collection(target_key)
                        written = batch_write(target_key, records)
                        # We also force refresh the app state data
                        if "data" in st.session_state:
                            st.session_state["data"][target_key] = df
                        st.success(f"Successfully synced {written} records to Firebase! You can view the changes live in the dashboard.")
                    else:
                        st.info("Local mode only: Upload processed, but not pushed to Firebase.")

    except Exception as e:
        st.error(f"Error parsing CSV: {e}")

st.markdown("""
<div style="margin-top: 3rem; padding: 1rem; border-radius: 8px; background: rgba(79, 142, 247, 0.1); border: 1px solid rgba(79, 142, 247, 0.3);">
    <h4 style="margin-top:0; color: #4F8EF7;">💡 How to see your data live</h4>
    <ol style="margin-bottom:0;">
        <li><b>Web Dashboard:</b> Since your Firebase config connects natively to the database, pushing new data here will <i>instantaneously</i> update all your web dashboard charts.</li>
        <li><b>Firebase Console:</b> You can verify the raw document data at <a href="https://console.cloud.google.com/datastore/databases/-default-/entities?project=ccassignment-7f9c4">Firestore</a>.</li>
    </ol>
</div>
""", unsafe_allow_html=True)
