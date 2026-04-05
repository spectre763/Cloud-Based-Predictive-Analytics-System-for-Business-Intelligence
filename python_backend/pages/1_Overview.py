# ─── pages/1_Overview.py ─────────────────────────────────────────────────────
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from analytics import kpi_summary
from config import CHART_HEIGHT

def render():
    data    = st.session_state.get("data", {})
    kpis_df = data.get("kpis", pd.DataFrame())
    if kpis_df.empty:
        st.warning("No analytics data loaded. Use the sidebar to refresh cloud data or seed sample data.")
        return

    summary = kpi_summary(kpis_df)

    st.markdown("## 🏠 Executive Overview")
    st.markdown("Real-time business health at a glance — last 24 months of performance.")
    st.markdown("---")

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    cards = [
        (c1, "💰 Revenue",       f"${summary['revenue']['value']:,.0f}",    summary['revenue']['delta'],    "%"),
        (c2, "📊 Profit",        f"${summary['profit']['value']:,.0f}",     summary['profit']['delta'],     "%"),
        (c3, "📉 Margin",        f"{summary['profit_pct']['value']:.1f}%",  summary['profit_pct']['delta'], "pp"),
        (c4, "🎯 CAC",           f"${summary['cac']['value']:.0f}",         summary['cac']['delta'],        "% MoM"),
        (c5, "⚠️  Churn",        f"{summary['churn']['value']:.2f}%",       summary['churn']['delta'],      "% MoM"),
        (c6, "⭐ NPS",           f"{summary['nps']['value']:.0f}",           summary['nps']['delta'],        "pp"),
    ]
    for col, label, val, delta, unit in cards:
        color = "#10B981" if delta < 0 and label in ["🎯 CAC","⚠️  Churn"] else \
                "#F43F5E" if delta < 0 else "#10B981"
        arrow = "▲" if delta > 0 else "▼"
        col.markdown(f"""
        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                    border-radius:12px;padding:16px 14px;text-align:center;">
            <div style="font-size:0.72rem;color:#64748B;font-weight:500;">{label}</div>
            <div style="font-size:1.55rem;font-weight:800;color:#E2E8F0;margin:6px 0;">{val}</div>
            <div style="font-size:0.72rem;color:{color};">{arrow} {abs(delta):.1f}{unit}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Revenue Trend ─────────────────────────────────────────────────────────
    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.markdown("#### 📈 Revenue Trend (24 months)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=kpis_df["month_label"], y=kpis_df["revenue"],
            mode="lines+markers",
            line=dict(color="#4F8EF7", width=3),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(79,142,247,0.08)",
            name="Revenue",
        ))
        fig.add_trace(go.Scatter(
            x=kpis_df["month_label"], y=kpis_df["profit"],
            mode="lines", line=dict(color="#10B981", width=2, dash="dot"),
            name="Profit",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94A3B8"), height=CHART_HEIGHT,
            legend=dict(orientation="h", y=1.08),
            xaxis=dict(showgrid=False, tickangle=-30),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="$"),
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("#### 🎯 KPI Gauge — NPS")
        nps_val = summary["nps"]["value"]
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=nps_val,
            delta={"reference": kpis_df["nps"].iloc[-2], "valueformat": ".1f"},
            gauge={
                "axis": {"range": [0, 80], "tickcolor": "#64748B"},
                "bar": {"color": "#4F8EF7"},
                "steps": [
                    {"range": [0, 30],  "color": "rgba(244,63,94,0.2)"},
                    {"range": [30, 55], "color": "rgba(245,158,11,0.2)"},
                    {"range": [55, 80], "color": "rgba(16,185,129,0.2)"},
                ],
                "threshold": {"line": {"color": "#9B6FEA", "width": 3}, "value": 60},
            },
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E2E8F0"),
            height=220, margin=dict(l=20, r=20, t=30, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("##### 📋 Churn vs CAC")
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=kpis_df["month_label"], y=kpis_df["churn"],
            line=dict(color="#F43F5E", width=2), name="Churn %",
        ))
        fig3.add_trace(go.Scatter(
            x=kpis_df["month_label"], y=kpis_df["cac"] / kpis_df["cac"].max() * kpis_df["churn"].max(),
            line=dict(color="#F59E0B", width=2, dash="dot"), name="CAC (norm)",
        ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94A3B8"), height=180,
            legend=dict(orientation="h", y=1.1, font=dict(size=10)),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ── Activity Feed ──────────────────────────────────────────────────────────
    st.markdown("#### 🔔 Recent Activity")
    activity = data.get("activity", pd.DataFrame())
    if not activity.empty:
        cols = st.columns(3)
        for i, (_, row) in enumerate(activity.head(9).iterrows()):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03);border-left:3px solid #4F8EF7;
                            border-radius:8px;padding:10px 14px;margin-bottom:8px;">
                    <div style="font-size:0.82rem;font-weight:600;color:#E2E8F0;">{row['description']}</div>
                    <div style="font-size:0.7rem;color:#64748B;margin-top:2px;">{row['source']} · {row['timestamp'][:10]}</div>
                </div>
                """, unsafe_allow_html=True)

render()
