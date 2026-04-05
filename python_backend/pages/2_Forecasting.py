# ─── pages/2_Forecasting.py ─────────────────────────────────────────────────
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from analytics import feature_importance
from config import CHART_HEIGHT, SCENARIOS

def render():
    data    = st.session_state.get("data", {})
    sales   = data.get("sales", pd.DataFrame())
    kpis_df = data.get("kpis", pd.DataFrame())
    if sales.empty:
        st.warning("No forecasting data available. Use the sidebar to refresh cloud data or seed sample data.")
        return

    st.markdown("## 📈 Revenue Forecasting")
    st.markdown("ML-driven multi-scenario projections with confidence intervals.")
    st.markdown("---")

    # Controls
    c1, c2, c3 = st.columns([1, 1, 2])
    scenario = c1.selectbox("Scenario", list(SCENARIOS.keys()), index=1)
    show_ci  = c2.toggle("Show Confidence Band", value=True)

    hist = sales[~sales["is_forecast"]]
    fc   = sales[sales["is_forecast"]]

    # ── Main Forecast Chart ───────────────────────────────────────────────────
    fig = go.Figure()

    # Confidence band
    if show_ci and not fc.empty:
        x_bound = [hist["month_label"].iloc[-1]] + fc["month_label"].tolist() + fc["month_label"].tolist()[::-1] + [hist["month_label"].iloc[-1]]
        y_bound = [hist["actual"].iloc[-1]] + fc["upper"].tolist() + fc["lower"].tolist()[::-1] + [hist["actual"].iloc[-1]]
        
        fig.add_trace(go.Scatter(
            x=x_bound,
            y=y_bound,
            fill="toself",
            fillcolor="rgba(79,142,247,0.10)",
            line=dict(color="rgba(255,255,255,0)"),
            name="Confidence Band",
            showlegend=True,
        ))

    # Historical actuals
    fig.add_trace(go.Scatter(
        x=hist["month_label"], y=hist["actual"],
        mode="lines+markers",
        line=dict(color="#4F8EF7", width=3),
        marker=dict(size=5),
        name="Historical",
    ))

    # Chosen scenario forecast
    scenario_col = scenario.lower()
    scenario_color = {"pessimistic": "#F43F5E", "base": "#22D3EE", "optimistic": "#10B981"}[scenario_col]

    if not fc.empty:
        # Connect last historical to first forecast
        join_x = [hist["month_label"].iloc[-1], fc["month_label"].iloc[0]]
        join_y = [hist["actual"].iloc[-1], fc[scenario_col].iloc[0]]
        fig.add_trace(go.Scatter(x=join_x, y=join_y,
            mode="lines", line=dict(color=scenario_color, width=2, dash="dash"),
            showlegend=False))

        fig.add_trace(go.Scatter(
            x=fc["month_label"], y=fc[scenario_col],
            mode="lines+markers",
            line=dict(color=scenario_color, width=3, dash="dash"),
            marker=dict(size=7, symbol="diamond"),
            name=f"{scenario} Forecast",
        ))

    # Forecast divider
    if not fc.empty:
        forecast_start = fc["month_label"].iloc[0]
        fig.add_shape(
            type="line",
            x0=forecast_start,
            x1=forecast_start,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(color="rgba(255,255,255,0.2)", dash="dot", width=1),
        )
        fig.add_annotation(
            x=forecast_start,
            y=1.0,
            yref="paper",
            text="Forecast →",
            showarrow=False,
            font=dict(color="#94A3B8", size=11),
            xanchor="left",
            yshift=10,
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8"), height=CHART_HEIGHT + 50,
        legend=dict(orientation="h", y=1.06),
        xaxis=dict(showgrid=False, tickangle=-30, categoryorder="array", categoryarray=sales["month_label"]),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="$"),
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Scenario Comparison ───────────────────────────────────────────────────
    if not fc.empty:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### Scenario Summary")
            rows = []
            for sc in ["pessimistic", "base", "optimistic"]:
                rows.append({
                    "Scenario":  sc.capitalize(),
                    "6-Month Total": f"${fc[sc].sum():,.0f}",
                    "Avg Monthly":   f"${fc[sc].mean():,.0f}",
                    "vs Base %":     f"{((fc[sc].sum()-fc['base'].sum())/fc['base'].sum()*100):+.1f}%",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        with col_b:
            st.markdown("#### 🔍 Feature Importance")
            fi = feature_importance()
            fig2 = go.Figure(go.Bar(
                x=fi["importance"], y=fi["feature"],
                orientation="h",
                marker=dict(
                    color=fi["importance"],
                    colorscale=[[0,"#1A1A2E"],[0.5,"#4F8EF7"],[1,"#9B6FEA"]],
                    showscale=False,
                ),
                text=[f"{v:.0%}" for v in fi["importance"]],
                textposition="outside",
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"), height=300,
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False),
                margin=dict(l=10, r=50, t=10, b=10),
            )
            st.plotly_chart(fig2, use_container_width=True)

render()
