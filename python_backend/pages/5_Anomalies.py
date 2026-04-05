# ─── pages/5_Anomalies.py ─────────────────────────────────────────────────────
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config import CHART_HEIGHT

SEVERITY_COLOR = {"critical": "#F43F5E", "warning": "#F59E0B", "info": "#4F8EF7"}
SEVERITY_ICON  = {"critical": "🔴", "warning": "🟡", "info": "🔵"}

def render():
    data      = st.session_state.get("data", {})
    anomalies = data.get("anomalies", pd.DataFrame())
    kpis_df   = data.get("kpis", pd.DataFrame())

    st.markdown("## ⚠️ Anomaly Detection")
    st.markdown("Statistical outlier analysis across all key business metrics.")
    st.markdown("---")

    # ── Summary Badges ────────────────────────────────────────────────────────
    total    = len(anomalies)
    critical = len(anomalies[anomalies["severity"] == "critical"]) if not anomalies.empty else 0
    warning  = len(anomalies[anomalies["severity"] == "warning"])  if not anomalies.empty else 0
    resolved = len(anomalies[anomalies["resolved"] == True])       if not anomalies.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, color in [
        (c1, "Total Anomalies",  total,    "#4F8EF7"),
        (c2, "🔴 Critical",      critical, "#F43F5E"),
        (c3, "🟡 Warning",       warning,  "#F59E0B"),
        (c4, "✅ Resolved",      resolved, "#10B981"),
    ]:
        col.markdown(f"""
        <div style="background:rgba(255,255,255,0.04);border-top:3px solid {color};
                    border-radius:12px;padding:14px;text-align:center;">
            <div style="font-size:0.72rem;color:#64748B;">{label}</div>
            <div style="font-size:2rem;font-weight:800;color:{color};">{val}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Revenue time-series with anomaly highlights ───────────────────────────
    st.markdown("#### 📉 Revenue with Anomaly Zones")
    if not kpis_df.empty:
        revenue_anomalies = anomalies[anomalies["metric"] == "revenue"] if not anomalies.empty else pd.DataFrame()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=kpis_df["month_label"], y=kpis_df["revenue"],
            mode="lines+markers",
            line=dict(color="#4F8EF7", width=3),
            marker=dict(size=5),
            fill="tozeroy", fillcolor="rgba(79,142,247,0.06)",
            name="Revenue",
        ))

        # Overlay anomaly markers
        if not revenue_anomalies.empty:
            merged = pd.merge(revenue_anomalies, kpis_df, on="month_label", how="inner")
            for _, row in merged.iterrows():
                color = SEVERITY_COLOR.get(row["severity"], "#F59E0B")
                fig.add_trace(go.Scatter(
                    x=[row["month_label"]], y=[row["revenue_y"]],
                    mode="markers",
                    marker=dict(size=14, color=color,
                                line=dict(width=2, color="white"), symbol="circle"),
                    name=f"Anomaly ({row['severity']})",
                    showlegend=False,
                    hovertemplate=f"<b>{row['severity'].upper()}</b><br>Value: ${row['revenue_y']:,.0f}<br>Expected: ${row['expected']:,.0f}<extra></extra>",
                ))
                # Shaded zone
                idx = kpis_df[kpis_df["month_label"] == row["month_label"]].index
                if len(idx) > 0:
                    i = idx[0]
                    x_zone = kpis_df["month_label"].iloc[max(0,i-1):min(len(kpis_df),i+2)].tolist()
                    y_zone = [kpis_df["revenue"].max() * 1.05] * len(x_zone)
                    y_base = [0] * len(x_zone)
                    fig.add_trace(go.Scatter(
                        x=x_zone + x_zone[::-1], y=y_zone + y_base,
                        fill="toself",
                        fillcolor=f"rgba({','.join(str(int(c,16)) for c in [color[1:3],color[3:5],color[5:7]])},0.07)",
                        line=dict(color="rgba(0,0,0,0)"),
                        showlegend=False,
                    ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94A3B8"), height=CHART_HEIGHT,
            xaxis=dict(showgrid=False, tickangle=-30),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="$"),
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Anomaly Cards ────────────────────────────────────────────────────────
    st.markdown("#### 🔔 Active Alerts")
    if anomalies.empty:
        st.info("No anomalies detected.")
        return

    active = anomalies[anomalies["resolved"] == False].sort_values("z_score", ascending=False)
    if active.empty:
        st.success("All anomalies resolved!")
    else:
        cols = st.columns(2)
        for i, (_, row) in enumerate(active.iterrows()):
            color = SEVERITY_COLOR.get(row["severity"], "#4F8EF7")
            icon  = SEVERITY_ICON.get(row["severity"], "🔵")
            with cols[i % 2]:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.04);
                            border:1px solid {color}50;border-left:4px solid {color};
                            border-radius:10px;padding:16px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:0.8rem;font-weight:700;color:{color};">
                            {icon} {row['severity'].upper()} — {row['metric'].upper()}
                        </span>
                        <span style="font-size:0.7rem;color:#64748B;">{row.get('month_label','')}</span>
                    </div>
                    <div style="margin-top:8px;font-size:0.82rem;color:#E2E8F0;">
                        Observed: <b style="color:{color};">{row['value']:,.2f}</b>
                        &nbsp;|&nbsp; Expected: <b>{row['expected']:,.2f}</b>
                        &nbsp;|&nbsp; Z-score: <b>{row['z_score']:.2f}σ</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Resolved table ────────────────────────────────────────────────────────
    with st.expander("✅ Resolved Anomalies"):
        resolved_df = anomalies[anomalies["resolved"] == True]
        if resolved_df.empty:
            st.info("None resolved yet.")
        else:
            st.dataframe(
                resolved_df[["metric","month_label","value","expected","z_score","severity"]].rename(columns={
                    "metric":"Metric","month_label":"Month","value":"Observed",
                    "expected":"Expected","z_score":"Z-Score","severity":"Severity"
                }),
                use_container_width=True, hide_index=True,
            )

render()
