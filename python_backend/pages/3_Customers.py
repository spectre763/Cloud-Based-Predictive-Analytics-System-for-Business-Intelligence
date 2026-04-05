# ─── pages/3_Customers.py ─────────────────────────────────────────────────────
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from analytics import generate_cohort_retention
from config import SEGMENT_COLORS, CHART_HEIGHT

def render():
    data      = st.session_state.get("data", {})
    customers = data.get("customers", pd.DataFrame())
    if customers.empty:
        st.warning("No customer data available. Use the sidebar to refresh cloud data or seed sample data.")
        return

    st.markdown("## 👥 Customer Analytics & Segmentation")
    st.markdown("RFM analysis, cohort retention, LTV distribution, and churn risk profiling.")
    st.markdown("---")

    # ── Segment filter ──────────────────────────────────────────────────────
    segs = ["All"] + sorted(customers["segment"].unique().tolist())
    sel  = st.selectbox("Filter by Segment", segs)
    df   = customers if sel == "All" else customers[customers["segment"] == sel]

    # ── Summary counts ──────────────────────────────────────────────────────
    seg_counts = customers.groupby("segment").size().reset_index(name="count")
    seg_totals = customers.groupby("segment")["ltv"].sum().reset_index(name="total_ltv")
    seg_df     = seg_counts.merge(seg_totals, on="segment")

    cols = st.columns(5)
    for i, row in seg_df.iterrows():
        color = SEGMENT_COLORS.get(row["segment"], "#4F8EF7")
        with cols[i % 5]:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.04);border:1px solid {color}40;
                        border-radius:12px;padding:14px;text-align:center;border-top:3px solid {color};">
                <div style="font-size:0.7rem;color:#64748B;font-weight:600;">{row['segment'].upper()}</div>
                <div style="font-size:1.4rem;font-weight:800;color:#E2E8F0;">{row['count']:,}</div>
                <div style="font-size:0.7rem;color:{color};">LTV ${row['total_ltv']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2])

    # ── RFM Scatter ──────────────────────────────────────────────────────────
    with col_l:
        st.markdown("#### 🎯 RFM Customer Map (Recency vs Monetary)")
        sample = df.sample(min(500, len(df)), random_state=42)
        fig = go.Figure()
        for seg, color in SEGMENT_COLORS.items():
            s = sample[sample["segment"] == seg]
            if s.empty:
                continue
            fig.add_trace(go.Scatter(
                x=s["recency"], y=s["monetary"],
                mode="markers",
                marker=dict(
                    color=color, size=np.clip(s["frequency"]*2.5, 4, 18),
                    opacity=0.75, line=dict(width=0.5, color="rgba(0,0,0,0.3)"),
                ),
                name=seg,
                text=s["segment"],
                hovertemplate="<b>%{text}</b><br>Recency: %{x}d<br>Monetary: $%{y:,.0f}<extra></extra>",
            ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94A3B8"), height=CHART_HEIGHT,
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", title="Recency (days)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", title="Monetary Value ($)"),
            legend=dict(orientation="h", y=1.06),
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Churn Gauge + Donut ───────────────────────────────────────────────────
    with col_r:
        st.markdown("#### ⚠️ Churn Risk Distribution")
        avg_churn = df["churn_prob"].mean() * 100
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_churn,
            number={"suffix": "%", "font": {"color": "#F43F5E", "size": 36}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#64748B"},
                "bar":  {"color": "#F43F5E"},
                "steps": [
                    {"range": [0, 20],  "color": "rgba(16,185,129,0.2)"},
                    {"range": [20, 50], "color": "rgba(245,158,11,0.2)"},
                    {"range": [50,100], "color": "rgba(244,63,94,0.2)"},
                ],
            },
            title={"text": "Avg Churn Probability", "font": {"color": "#94A3B8", "size": 13}},
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E2E8F0"),
            height=230, margin=dict(l=20, r=20, t=30, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### 🍩 Segment Mix")
        fig3 = go.Figure(go.Pie(
            labels=seg_df["segment"], values=seg_df["count"],
            hole=0.55,
            marker=dict(colors=[SEGMENT_COLORS[s] for s in seg_df["segment"]],
                        line=dict(color="#07070F", width=2)),
        ))
        fig3.update_traces(textinfo="percent+label", textfont_size=11)
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"),
            height=220, margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ── Cohort Retention Heatmap ───────────────────────────────────────────────
    st.markdown("#### 🔄 Cohort Retention Heatmap")
    cohort = generate_cohort_retention()
    fig4 = go.Figure(go.Heatmap(
        z=cohort.values,
        x=cohort.columns.tolist(),
        y=cohort.index.tolist(),
        colorscale=[[0,"#F43F5E"],[0.4,"#F59E0B"],[0.7,"#4F8EF7"],[1,"#10B981"]],
        text=[[f"{v:.0f}%" for v in row] for row in cohort.values],
        texttemplate="%{text}",
        hovertemplate="Cohort: %{y}<br>Period: %{x}<br>Retention: %{z:.1f}%<extra></extra>",
        showscale=True,
    ))
    fig4.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8"), height=300,
        xaxis=dict(side="top"),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    st.plotly_chart(fig4, use_container_width=True)

    # ── LTV Distribution ──────────────────────────────────────────────────────
    st.markdown("#### 💰 Customer LTV Distribution by Segment")
    fig5 = go.Figure()
    for seg, color in SEGMENT_COLORS.items():
        sub = df[df["segment"] == seg]["ltv"]
        if sub.empty:
            continue
        fig5.add_trace(go.Box(
            y=sub, name=seg,
            marker_color=color, boxmean=True,
            line=dict(width=2),
        ))
    fig5.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8"), height=300,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="$"),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig5, use_container_width=True)

render()
