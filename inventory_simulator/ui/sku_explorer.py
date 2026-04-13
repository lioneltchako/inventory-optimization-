"""SKU Explorer — hero page for single-SKU deep dive and 90-day simulation."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from inventory_simulator.data.generator import PORTFOLIO
from inventory_simulator.logic.formulas import (
    annual_holding_cost,
    annual_ordering_cost,
    eoq,
    fill_rate,
    normal_loss,
    reorder_point,
    safety_stock_RS,
    safety_stock_sQ,
    sigma_x_RS,
    sigma_x_sQ,
    z_from_csl,
)
from inventory_simulator.logic.simulation import simulate_stock_trajectory
from inventory_simulator.styles.theme import COLOR_MAP, CRITICALITY_COLORS
from inventory_simulator.ui.components import (
    render_disclaimer,
    render_hero_banner,
)

# ── Hero banner ───────────────────────────────────────────────────────────────

render_hero_banner(
    headline="SKU Explorer — 90-Day Simulation",
    subtext=(
        "Select any SKU, choose a policy, set your service-level target. "
        "Observe how parameters drive safety stock, cost, and simulated stock trajectory."
    ),
)

# ── Sidebar controls ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("---")
    st.markdown("### SKU Explorer Controls")

    category_filter = st.selectbox(
        "Filter by Part Family",
        options=["All"] + sorted(PORTFOLIO["category"].unique().tolist()),
    )

    filtered_df = (
        PORTFOLIO
        if category_filter == "All"
        else PORTFOLIO[PORTFOLIO["category"] == category_filter]
    )
    sku_options = filtered_df["sku_id"].tolist()

    selected_sku_id = st.selectbox("Select SKU", options=sku_options)

    row = PORTFOLIO[PORTFOLIO["sku_id"] == selected_sku_id].iloc[0]

    st.markdown("---")
    policy = st.radio(
        "Replenishment Policy", ["(s,Q) Continuous Review", "(R,S) Periodic Review"]
    )
    review_period = 7
    if "(R,S)" in policy:
        review_period = st.slider("Review Period (days)", 3, 30, 7)

    target_csl = st.slider(
        "Target Service Level (CSL)", 0.90, 0.999, 0.97, step=0.005, format="%.3f"
    )
    show_band = st.checkbox("Show demand variability band", value=True)
    sim_seed = st.number_input(
        "Simulation seed", min_value=0, max_value=9999, value=42, step=1
    )

# ── Extract SKU parameters ────────────────────────────────────────────────────

d_mean: float = float(row["avg_daily_demand"])
d_std: float = float(row["demand_std"])
lt_mean: float = float(row["lead_time_days"])
lt_std: float = float(row["lead_time_std"])
unit_cost: float = float(row["unit_cost"])
holding_pct: float = float(row["holding_cost_pct"])
order_cost: float = float(row["order_cost"])
annual_demand: float = float(row["annual_demand"])
criticality: str = str(row["criticality"])
category: str = str(row["category"])

z = z_from_csl(target_csl)

# Compute policy-specific parameters
if "(s,Q)" in policy:
    sx = sigma_x_sQ(d_mean, d_std, lt_mean, lt_std)
    ss = safety_stock_sQ(z, d_mean, d_std, lt_mean, lt_std)
    q_order = eoq(annual_demand, order_cost, unit_cost * holding_pct)
    rop = reorder_point(d_mean, lt_mean, ss)
    policy_label = "(s,Q) Continuous Review"
else:
    sx = sigma_x_RS(d_mean, d_std, lt_mean, lt_std, review_period)
    ss = safety_stock_RS(z, d_mean, d_std, lt_mean, lt_std, review_period)
    q_order = d_mean * (lt_mean + review_period) + ss
    rop = reorder_point(d_mean, lt_mean, ss)
    policy_label = f"(R,S) Periodic Review · R={review_period}d"

fr = fill_rate(ss, sx, max(q_order, 1.0))
ss_value = ss * unit_cost
current_ss_value = float(row["current_ss_value"])
saving = current_ss_value - ss_value
annual_hc_opt = annual_holding_cost(ss, unit_cost, holding_pct)
annual_oc_opt = annual_ordering_cost(annual_demand, q_order, order_cost)

# ── Low SS toast warning ──────────────────────────────────────────────────────

ss_days = ss / max(d_mean, 0.001)
if ss_days < 3.0:
    st.toast(
        f"⚠️ Safety stock is only {ss_days:.1f} days of cover — "
        "consider reviewing lead-time risk for this SKU.",
        icon="⚠️",
    )

# ── SKU identity bar ──────────────────────────────────────────────────────────

tier_color = CRITICALITY_COLORS.get(criticality, COLOR_MAP["muted"])
st.markdown(
    f"**{selected_sku_id}** &nbsp;·&nbsp; {category} &nbsp;·&nbsp; "
    f'<span style="background:{tier_color}22;color:{tier_color};border:1px solid {tier_color}44;'
    f'padding:2px 8px;border-radius:10px;font-size:0.8rem;font-weight:600;">{criticality}</span> '
    f"&nbsp;·&nbsp; Policy: **{policy_label}**",
    unsafe_allow_html=True,
)

st.divider()

# ── KPI comparison row ────────────────────────────────────────────────────────

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Safety Stock (units)",
        f"{ss:.1f}",
        delta=f"{ss - float(row['current_safety_stock_units']):+.1f} vs current",
        delta_color="inverse",
    )
with col2:
    st.metric("Safety Stock Value", f"${ss_value:,.0f}")
with col3:
    st.metric(
        "Saving vs Current",
        f"${saving:,.0f}",
        delta=f"{saving / max(current_ss_value, 1):.0%} release",
    )
with col4:
    st.metric("Fill Rate", f"{fr:.2%}")
with col5:
    st.metric("SS Coverage", f"{ss_days:.1f} days")

st.divider()

# ── 90-day simulation ─────────────────────────────────────────────────────────

st.markdown("### 90-Day Stock Trajectory")

sim_df = simulate_stock_trajectory(
    avg_daily_demand=d_mean,
    demand_std=d_std,
    lead_time_days=lt_mean,
    reorder_point=rop,
    order_quantity=q_order,
    horizon=90,
    seed=int(sim_seed),
)

fig_sim = go.Figure()

# Demand variability band (±1 σ demand propagated as cumulative reference)
if show_band:
    upper_band = sim_df["inventory"] + d_std * np.sqrt(np.arange(1, 91))
    lower_band = np.maximum(
        0.0, sim_df["inventory"] - d_std * np.sqrt(np.arange(1, 91))
    )
    fig_sim.add_trace(
        go.Scatter(
            x=sim_df["day"].tolist() + sim_df["day"].tolist()[::-1],
            y=upper_band.tolist() + lower_band.tolist()[::-1],
            fill="toself",
            fillcolor="rgba(27,58,107,0.07)",
            line={"color": "rgba(0,0,0,0)"},
            name="Demand variability band",
            showlegend=True,
        )
    )

# Inventory trajectory
fig_sim.add_trace(
    go.Scatter(
        x=sim_df["day"],
        y=sim_df["inventory"],
        mode="lines",
        line={"color": COLOR_MAP["primary"], "width": 2},
        name="Inventory level",
    )
)

# Reorder point line
fig_sim.add_hline(
    y=rop,
    line_dash="dash",
    line_color=COLOR_MAP["warning"],
    line_width=1.5,
    annotation_text=f"ROP = {rop:.0f}",
    annotation_position="top right",
)

# Safety stock line
fig_sim.add_hline(
    y=ss,
    line_dash="dot",
    line_color=COLOR_MAP["danger"],
    line_width=1.5,
    annotation_text=f"SS = {ss:.0f}",
    annotation_position="bottom right",
)

# Mark order placements
order_days = sim_df[sim_df["order_placed"]]["day"]
if not order_days.empty:
    fig_sim.add_trace(
        go.Scatter(
            x=order_days,
            y=sim_df.loc[sim_df["order_placed"], "inventory"],
            mode="markers",
            marker={
                "symbol": "triangle-up",
                "color": COLOR_MAP["accent"],
                "size": 9,
            },
            name="Order placed",
        )
    )

# Mark stockouts
stockout_days = sim_df[sim_df["stockout"]]["day"]
if not stockout_days.empty:
    fig_sim.add_trace(
        go.Scatter(
            x=stockout_days,
            y=[0] * len(stockout_days),
            mode="markers",
            marker={
                "symbol": "x",
                "color": COLOR_MAP["danger"],
                "size": 10,
            },
            name="Stockout event",
        )
    )

n_stockouts = int(sim_df["stockout"].sum())
n_orders = int(sim_df["order_placed"].sum())

fig_sim.update_layout(
    xaxis_title="Day",
    yaxis_title="Units on Hand",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"t": 20, "b": 50, "l": 70, "r": 20},
    height=360,
    legend={"orientation": "h", "y": -0.22},
    xaxis={"gridcolor": "#F0F0F0"},
    yaxis={"gridcolor": "#F0F0F0", "rangemode": "tozero"},
)
st.plotly_chart(fig_sim, use_container_width=True)

sim_a, sim_b, sim_c = st.columns(3)
with sim_a:
    st.metric("Simulated Stockout Events", n_stockouts, delta="in 90 days")
with sim_b:
    st.metric("Replenishment Orders Triggered", n_orders)
with sim_c:
    st.metric("Min Inventory Reached", f"{float(sim_df['inventory'].min()):.1f} units")

st.divider()

# ── Cost breakdown ────────────────────────────────────────────────────────────

cost_col, curve_col = st.columns(2, gap="large")

with cost_col:
    st.markdown("### Annual Cost Breakdown (Optimal Policy)")

    labels = ["Safety Stock\nHolding Cost", "Ordering Cost"]
    values = [annual_hc_opt, annual_oc_opt]

    pie_fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            marker_colors=[COLOR_MAP["primary"], COLOR_MAP["accent"]],
            texttemplate="%{label}<br>$%{value:,.0f}",
            hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
            hole=0.45,
        )
    )
    pie_fig.update_layout(
        showlegend=False,
        margin={"t": 10, "b": 10, "l": 10, "r": 10},
        height=260,
        annotations=[
            {
                "text": f"${annual_hc_opt + annual_oc_opt:,.0f}<br>total/yr",
                "x": 0.5,
                "y": 0.5,
                "font_size": 13,
                "showarrow": False,
            }
        ],
    )
    st.plotly_chart(pie_fig, use_container_width=True)

with curve_col:
    st.markdown("### CSL vs. Safety Stock — This SKU")

    csl_range = np.linspace(0.85, 0.999, 50)
    ss_range = [z_from_csl(c) * sx for c in csl_range]
    ss_val_range = [s * unit_cost for s in ss_range]

    curve_fig = go.Figure()
    curve_fig.add_trace(
        go.Scatter(
            x=csl_range * 100,
            y=ss_val_range,
            mode="lines",
            line={"color": COLOR_MAP["primary"], "width": 2},
            hovertemplate="CSL: %{x:.1f}%<br>SS: $%{y:,.0f}<extra></extra>",
        )
    )
    curve_fig.add_vline(
        x=target_csl * 100,
        line_dash="dash",
        line_color=COLOR_MAP["accent"],
        annotation_text=f"Target: {target_csl:.1%}",
        annotation_position="top right",
    )
    curve_fig.add_trace(
        go.Scatter(
            x=[target_csl * 100],
            y=[ss_value],
            mode="markers",
            marker={"color": COLOR_MAP["accent"], "size": 10},
            name="Selected CSL",
            showlegend=False,
        )
    )
    curve_fig.update_layout(
        xaxis_title="CSL (%)",
        yaxis_title="SS Value ($)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"t": 10, "b": 50, "l": 70, "r": 20},
        height=260,
        xaxis={"gridcolor": "#F0F0F0"},
        yaxis={"gridcolor": "#F0F0F0"},
    )
    st.plotly_chart(curve_fig, use_container_width=True)

st.divider()

# ── Formula detail expander ───────────────────────────────────────────────────

with st.expander("Formula detail — how these numbers are derived", expanded=False):
    st.markdown("**Demand variability over the lead time:**")
    if "(s,Q)" in policy:
        st.latex(r"\sigma_x = \sqrt{\mu_L \cdot \sigma_d^2 + \sigma_L^2 \cdot \mu_d^2}")
        st.markdown(
            f"= √({lt_mean:.1f} × {d_std:.3f}² + {lt_std:.2f}² × {d_mean:.3f}²) "
            f"= **{sx:.3f} units**"
        )
    else:
        st.latex(
            r"\sigma_x = \sqrt{(\mu_L + R) \cdot \sigma_d^2 + \sigma_L^2 \cdot \mu_d^2}"
        )
        st.markdown(
            f"= √(({lt_mean:.1f} + {review_period}) × {d_std:.3f}² + "
            f"{lt_std:.2f}² × {d_mean:.3f}²) = **{sx:.3f} units**"
        )

    st.markdown("**Safety stock:**")
    st.latex(r"SS = z \cdot \sigma_x")
    st.markdown(f"= {z:.4f} × {sx:.3f} = **{ss:.2f} units**")

    st.markdown("**Fill rate (Type II) via Normal Loss Function:**")
    st.latex(r"\beta = 1 - \frac{\sigma_x}{Q} \cdot L(z)")
    z_val = ss / max(sx, 1e-9)
    lz = normal_loss(z_val)
    st.markdown(
        f"L(z={z_val:.3f}) = {lz:.5f}, "
        f"β = 1 − ({sx:.3f}/{q_order:.1f}) × {lz:.5f} = **{fr:.4f}**"
    )

render_disclaimer()
