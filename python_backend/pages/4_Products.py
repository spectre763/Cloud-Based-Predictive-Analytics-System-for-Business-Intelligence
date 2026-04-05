# ─── pages/4_Products.py ─────────────────────────────────────────────────────
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import CHART_HEIGHT

def render():
    data     = st.session_state.get("data", {})
    products = data.get("products", pd.DataFrame())
    if products.empty:
        st.warning("No product data available. Use the sidebar to refresh cloud data or seed sample data.")
        return

    st.markdown("## 🏪 Product Intelligence")
    st.markdown("Sales mix, growth-share matrix, and category revenue breakdown.")
    st.markdown("---")

    # ── Filters ───────────────────────────────────────────────────────────────
    cats = ["All"] + sorted(products["category"].unique().tolist())
    sel  = st.selectbox("Filter by Category", cats)
    df   = products if sel == "All" else products[products["category"] == sel]

    df = df.sort_values("revenue", ascending=False)

    col_l, col_r = st.columns(2)

    # ── Treemap ───────────────────────────────────────────────────────────────
    with col_l:
        st.markdown("#### 🌳 Revenue Treemap")
        fig = px.treemap(
            df, path=["category", "name"], values="revenue",
            color="growth",
            color_continuous_scale=[[0,"#F43F5E"],[0.4,"#F59E0B"],[0.7,"#4F8EF7"],[1,"#10B981"]],
            color_continuous_midpoint=0,
            hover_data={"units": True, "rating": True},
        )
        fig.update_traces(
            textinfo="label+value+percent root",
            texttemplate="<b>%{label}</b><br>$%{value:,.0f}",
            marker=dict(line=dict(width=2, color="#07070F")),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0"), height=CHART_HEIGHT,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_colorbar=dict(title="Growth", tickformat=".0%", len=0.6),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Growth-Share (BCG) Matrix ─────────────────────────────────────────────
    with col_r:
        st.markdown("#### 📊 Growth–Share Matrix")
        avg_growth = df["growth"].mean()
        avg_share  = df["market_share"].mean()

        CAT_COLORS = {
            "SaaS": "#4F8EF7", "Platform": "#9B6FEA",
            "Add-On": "#22D3EE", "Enterprise": "#10B981", "Starter": "#F59E0B",
        }

        fig2 = go.Figure()
        for cat in df["category"].unique():
            sub = df[df["category"] == cat]
            fig2.add_trace(go.Scatter(
                x=sub["market_share"],
                y=sub["growth"],
                mode="markers+text",
                marker=dict(
                    size=sub["revenue"] / df["revenue"].max() * 60 + 12,
                    color=CAT_COLORS.get(cat, "#4F8EF7"),
                    opacity=0.8,
                    line=dict(width=1, color="rgba(255,255,255,0.2)"),
                ),
                text=sub["name"].str[:10],
                textposition="top center",
                textfont=dict(size=8, color="#94A3B8"),
                name=cat,
            ))

        # Quadrant lines
        fig2.add_hline(y=avg_growth, line=dict(color="rgba(255,255,255,0.1)", dash="dot"))
        fig2.add_vline(x=avg_share,  line=dict(color="rgba(255,255,255,0.1)", dash="dot"))

        # Quadrant labels
        for (x, y, label) in [
            (df["market_share"].max()*0.85, df["growth"].max()*0.9, "⭐ Stars"),
            (df["market_share"].min()*1.5,  df["growth"].max()*0.9, "❓ Question"),
            (df["market_share"].max()*0.85, df["growth"].min()*1.2, "🐄 Cash Cows"),
            (df["market_share"].min()*1.5,  df["growth"].min()*1.2, "🐕 Dogs"),
        ]:
            fig2.add_annotation(
                x=x, y=y, text=label,
                font=dict(color="rgba(255,255,255,0.2)", size=11),
                showarrow=False,
            )

        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94A3B8"), height=CHART_HEIGHT,
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Market Share"),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                       title="Revenue Growth", tickformat=".0%"),
            legend=dict(orientation="h", y=1.05),
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Category Bar Chart ────────────────────────────────────────────────────
    st.markdown("#### 📦 Revenue by Category")
    cat_rev = df.groupby("category")["revenue"].sum().sort_values(ascending=True)
    fig3 = go.Figure(go.Bar(
        x=cat_rev.values, y=cat_rev.index,
        orientation="h",
        marker=dict(
            color=cat_rev.values,
            colorscale=[[0,"#1A1A2E"],[0.5,"#4F8EF7"],[1,"#9B6FEA"]],
            showscale=False,
        ),
        text=[f"${v:,.0f}" for v in cat_rev.values],
        textposition="outside",
    ))
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8"), height=280,
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False),
        margin=dict(l=10, r=80, t=10, b=10),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Top Products Table ─────────────────────────────────────────────────────
    st.markdown("#### 🏆 Top Products")
    display = df.head(15)[["name","category","revenue","units","price","growth","rating"]].copy()
    display["revenue"] = display["revenue"].apply(lambda x: f"${x:,.0f}")
    display["price"]   = display["price"].apply(lambda x: f"${x:.2f}")
    display["growth"]  = display["growth"].apply(lambda x: f"{x:+.1%}")
    display["rating"]  = display["rating"].apply(lambda x: f"⭐ {x:.1f}")
    st.dataframe(display.rename(columns={
        "name":"Product","category":"Category","revenue":"Revenue",
        "units":"Units","price":"Price","growth":"Growth","rating":"Rating"
    }), use_container_width=True, hide_index=True)

render()
