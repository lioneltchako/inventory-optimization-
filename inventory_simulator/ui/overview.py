"""Overview page — the business problem and portfolio-level opportunity."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import norm  # type: ignore[import-untyped]

from inventory_simulator.data.generator import PORTFOLIO, PORTFOLIO_SUMMARY
from inventory_simulator.styles.theme import COLOR_MAP
from inventory_simulator.ui.components import (
    render_disclaimer,
    render_hero_banner,
    render_insight_card,
)

# ── Hero banner ───────────────────────────────────────────────────────────────

current_total = PORTFOLIO_SUMMARY["total_current_ss_value"]
saving = PORTFOLIO_SUMMARY["total_annual_saving"]

render_hero_banner(
    headline=(
        f'<span class="hero-accent">${current_total:,.0f}</span> in working capital '
        "locked in sub-optimal safety stock"
    ),
    subtext=(
        f"120 active SKUs across 5 part families · "
        f"${saving:,.0f} annual holding-cost saving identified at 97% service level"
    ),
)

# ── Top KPI row ───────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

ss_freed = float(PORTFOLIO_SUMMARY["total_current_ss_value"]) - float(
    PORTFOLIO_SUMMARY["total_optimal_ss_value"]
)
with col1:
    st.metric(
        "Current Safety Stock Value",
        f"${current_total:,.0f}",
        delta=f"-${ss_freed:,.0f} opportunity",
        delta_color="inverse",
    )
with col2:
    st.metric(
        "Annual Holding-Cost Saving",
        f"${saving:,.0f}",
        delta="at 97% CSL",
    )
with col3:
    st.metric(
        "Critical SKUs",
        str(PORTFOLIO_SUMMARY["n_critical"]),
        delta="Highest priority",
    )
with col4:
    st.metric(
        "Portfolio Fill Rate (Optimal)",
        f"{float(PORTFOLIO_SUMMARY['avg_fill_rate']):.1%}",
    )

st.divider()

# ── Two-column layout: trade-off curve + category breakdown ───────────────────

chart_col, info_col = st.columns([3, 2], gap="large")

with chart_col:
    st.markdown("### Service Level vs. Safety Stock Trade-Off")

    csl_values = np.linspace(0.80, 0.999, 60)
    z_values = norm.ppf(csl_values)

    # Average SKU parameters for the illustrative trade-off curve
    avg_sigma_x = float(PORTFOLIO["sigma_x"].mean())
    avg_cost = float(PORTFOLIO["unit_cost"].mean())
    holding_pct = 0.25

    ss_cost = z_values * avg_sigma_x * avg_cost * holding_pct * float(len(PORTFOLIO))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=csl_values * 100,
            y=ss_cost / 1_000,
            mode="lines",
            line={"color": COLOR_MAP["primary"], "width": 2.5},
            fill="tozeroy",
            fillcolor="rgba(27,58,107,0.08)",
            name="Holding cost",
            hovertemplate="CSL: %{x:.1f}%<br>SS Cost: $%{y:,.0f}K<extra></extra>",
        )
    )

    # Mark current (over-stocked) and optimal operating points
    optimal_csl = 97.0
    current_cost_mark = float(PORTFOLIO["current_ss_value"].sum()) * holding_pct / 1_000
    optimal_cost_mark = float(PORTFOLIO["optimal_ss_value"].sum()) * holding_pct / 1_000

    fig.add_trace(
        go.Scatter(
            x=[optimal_csl],
            y=[optimal_cost_mark],
            mode="markers+text",
            marker={"color": COLOR_MAP["success"], "size": 12, "symbol": "circle"},
            text=["Optimal"],
            textposition="top right",
            name="Optimal (97% CSL)",
            hovertemplate="Optimal<br>CSL: 97%<br>Cost: $%{y:,.0f}K<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[94.0],
            y=[current_cost_mark],
            mode="markers+text",
            marker={"color": COLOR_MAP["danger"], "size": 12, "symbol": "diamond"},
            text=["Current"],
            textposition="top left",
            name="Current (over-stocked)",
            hovertemplate="Current state<br>Cost: $%{y:,.0f}K<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis_title="Cycle Service Level (%)",
        yaxis_title="Annual SS Holding Cost ($K)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"t": 20, "b": 40, "l": 60, "r": 20},
        height=340,
        legend={"orientation": "h", "y": -0.18},
        xaxis={"gridcolor": "#F0F0F0"},
        yaxis={"gridcolor": "#F0F0F0"},
    )
    st.plotly_chart(fig, use_container_width=True)

with info_col:
    st.markdown("### The Problem")
    render_insight_card(
        "Static min/max buffers set years ago no longer reflect today's demand patterns. "
        "The result: excess stock on slow movers, stockouts on fast movers."
    )
    st.markdown(" ")
    render_insight_card(
        f"<b style='color:{COLOR_MAP['accent']}'>${ss_freed:,.0f}</b> in safety stock "
        "can be released without reducing service levels — by aligning policies with "
        "actual demand variability."
    )
    st.markdown(" ")
    render_insight_card(
        f"Critical SKUs (<b>{PORTFOLIO_SUMMARY['n_critical']}</b> parts) account for "
        "the highest stockout penalty. These require the tightest service-level targets "
        "and should be reviewed first."
    )

st.divider()

# ── Category savings bar ──────────────────────────────────────────────────────

st.markdown("### Saving Opportunity by Part Family")

cat_savings = (
    PORTFOLIO.groupby("category")["annual_saving"]
    .sum()
    .sort_values(ascending=True)
    .reset_index()
)

bar_fig = go.Figure(
    go.Bar(
        x=cat_savings["annual_saving"] / 1_000,
        y=cat_savings["category"],
        orientation="h",
        marker_color=COLOR_MAP["accent"],
        hovertemplate="%{y}: $%{x:,.0f}K / yr<extra></extra>",
        text=[f"${v / 1000:,.0f}K" for v in cat_savings["annual_saving"]],
        textposition="outside",
    )
)
bar_fig.update_layout(
    xaxis_title="Annual Saving ($K)",
    yaxis_title=None,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"t": 10, "b": 40, "l": 120, "r": 80},
    height=280,
    xaxis={"gridcolor": "#F0F0F0"},
)
st.plotly_chart(bar_fig, use_container_width=True)

st.divider()
render_disclaimer()
