"""Portfolio page — opportunity map across all 120 SKUs."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from inventory_simulator.data.generator import PORTFOLIO
from inventory_simulator.styles.theme import COLOR_MAP, CRITICALITY_COLORS
from inventory_simulator.ui.components import render_disclaimer, render_hero_banner

# ── Hero banner ───────────────────────────────────────────────────────────────

render_hero_banner(
    headline="Portfolio Opportunity Map",
    subtext=(
        "120 SKUs plotted by demand variability vs. safety-stock excess. "
        "Size = annual spend. Colour = criticality tier."
    ),
)

# ── Filters ───────────────────────────────────────────────────────────────────

filter_col, metric_col = st.columns([2, 3], gap="large")

with filter_col:
    categories = ["All"] + sorted(PORTFOLIO["category"].unique().tolist())
    selected_cat = st.selectbox("Filter by Part Family", categories)

    criticalities = ["All", "Critical", "Operational", "Standard"]
    selected_crit = st.selectbox("Filter by Criticality Tier", criticalities)

df = PORTFOLIO.copy()
if selected_cat != "All":
    df = df[df["category"] == selected_cat]
if selected_crit != "All":
    df = df[df["criticality"] == selected_crit]

with metric_col:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("SKUs shown", len(df))
    with m2:
        st.metric(
            "Current SS Value",
            f"${df['current_ss_value'].sum():,.0f}",
        )
    with m3:
        st.metric(
            "Optimal SS Value",
            f"${df['optimal_ss_value'].sum():,.0f}",
        )
    with m4:
        st.metric(
            "Annual Saving",
            f"${df['annual_saving'].sum():,.0f}",
        )

st.divider()

# ── Opportunity Map scatter ───────────────────────────────────────────────────

scatter_col, bar_col = st.columns([3, 2], gap="large")

with scatter_col:
    st.markdown("### Opportunity Map — CV vs. Safety Stock Days")

    fig_scatter = px.scatter(
        df,
        x="cv",
        y="current_safety_stock_days",
        color="criticality",
        size="annual_spend",
        size_max=30,
        hover_name="sku_id",
        hover_data={
            "category": True,
            "unit_cost": ":.2f",
            "avg_daily_demand": ":.2f",
            "current_safety_stock_days": ":.1f",
            "annual_saving": ":,.0f",
            "cv": ":.2f",
            "annual_spend": False,
        },
        color_discrete_map=CRITICALITY_COLORS,
        labels={
            "cv": "Demand Variability (CV)",
            "current_safety_stock_days": "Current Safety Stock (days)",
            "criticality": "Tier",
        },
    )

    # Quadrant reference lines (medians)
    cv_mid = float(df["cv"].median())
    ss_mid = float(df["current_safety_stock_days"].median())

    for xval, yval, label, ax, ay in [
        (
            cv_mid * 0.4,
            ss_mid * 1.6,
            "Low variability<br>High stock → Over-stocked",
            40,
            -30,
        ),
        (
            cv_mid * 1.8,
            ss_mid * 1.6,
            "High variability<br>High stock → Priority",
            -60,
            -30,
        ),
        (
            cv_mid * 0.4,
            ss_mid * 0.4,
            "Low variability<br>Low stock → Well-managed",
            40,
            30,
        ),
        (
            cv_mid * 1.8,
            ss_mid * 0.4,
            "High variability<br>Low stock → Review policy",
            -60,
            30,
        ),
    ]:
        fig_scatter.add_annotation(
            x=xval,
            y=yval,
            text=label,
            showarrow=False,
            font={"size": 9, "color": COLOR_MAP["muted"]},
            bgcolor="rgba(255,255,255,0.7)",
            borderpad=3,
        )

    fig_scatter.add_vline(
        x=cv_mid,
        line_dash="dot",
        line_color=COLOR_MAP["muted"],
        line_width=1,
    )
    fig_scatter.add_hline(
        y=ss_mid,
        line_dash="dot",
        line_color=COLOR_MAP["muted"],
        line_width=1,
    )

    fig_scatter.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"t": 20, "b": 40, "l": 60, "r": 20},
        height=420,
        xaxis={"gridcolor": "#F0F0F0"},
        yaxis={"gridcolor": "#F0F0F0"},
        legend={"orientation": "h", "y": -0.18},
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ── Top-10 savings bar ────────────────────────────────────────────────────────

with bar_col:
    st.markdown("### Top 10 SKUs by Saving")

    top10 = df.nlargest(10, "annual_saving")[
        ["sku_id", "category", "criticality", "annual_saving", "current_ss_value"]
    ]

    bar_colors = [
        CRITICALITY_COLORS.get(c, COLOR_MAP["muted"]) for c in top10["criticality"]
    ]

    fig_bar = go.Figure(
        go.Bar(
            x=top10["annual_saving"],
            y=top10["sku_id"],
            orientation="h",
            marker_color=bar_colors,
            hovertemplate="%{y}<br>Saving: $%{x:,.0f}/yr<extra></extra>",
            text=[f"${v:,.0f}" for v in top10["annual_saving"]],
            textposition="outside",
        )
    )
    fig_bar.update_layout(
        xaxis_title="Annual Saving ($/yr)",
        yaxis_title=None,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"t": 20, "b": 40, "l": 80, "r": 60},
        height=420,
        yaxis={"autorange": "reversed"},
        xaxis={"gridcolor": "#F0F0F0"},
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ── Treemap by category ───────────────────────────────────────────────────────

st.markdown("### Current Safety Stock by Category and Criticality")

treemap_df = (
    df.groupby(["category", "criticality"])["current_ss_value"].sum().reset_index()
)
treemap_df["label"] = treemap_df["category"] + " / " + treemap_df["criticality"]

fig_tree = px.treemap(
    treemap_df,
    path=["category", "criticality"],
    values="current_ss_value",
    color="criticality",
    color_discrete_map=CRITICALITY_COLORS,
    custom_data=["current_ss_value"],
)
fig_tree.update_traces(
    hovertemplate="<b>%{label}</b><br>SS Value: $%{customdata[0]:,.0f}<extra></extra>",
    texttemplate="<b>%{label}</b><br>$%{value:,.0f}",
)
fig_tree.update_layout(
    margin={"t": 10, "b": 10, "l": 10, "r": 10},
    height=320,
)
st.plotly_chart(fig_tree, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────

with st.expander("View full SKU table", expanded=False):
    display_cols = [
        "sku_id",
        "category",
        "criticality",
        "avg_daily_demand",
        "cv",
        "lead_time_days",
        "unit_cost",
        "current_safety_stock_days",
        "current_ss_value",
        "optimal_ss_value",
        "annual_saving",
    ]
    styled = df[display_cols].rename(
        columns={
            "sku_id": "SKU",
            "category": "Family",
            "criticality": "Tier",
            "avg_daily_demand": "Avg Demand/day",
            "cv": "CV",
            "lead_time_days": "Lead Time (d)",
            "unit_cost": "Unit Cost ($)",
            "current_safety_stock_days": "Current SS (d)",
            "current_ss_value": "Current SS ($)",
            "optimal_ss_value": "Optimal SS ($)",
            "annual_saving": "Annual Saving ($)",
        }
    )
    st.dataframe(
        styled.sort_values("Annual Saving ($)", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "⬇ Download CSV",
        data=styled.to_csv(index=False),
        file_name="paccar_sku_portfolio.csv",
        mime="text/csv",
    )

render_disclaimer()
