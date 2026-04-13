"""
Page 2 — SKU Explorer (Hero page)
"How policy choice and forecast quality determine safety stock and cost
 for one product"
"""

import streamlit as st
import plotly.graph_objects as go

from utils.disclaimer import show_banner, show_footer
from utils.colors import PRIMARY, SUCCESS, WARNING, DANGER, NEUTRAL
from utils.scenarios import SCENARIOS, get_scenario_params
from utils.formulas import (
    eoq,
    safety_stock_sQ,
    safety_stock_RS,
    reorder_point,
    order_up_to,
    fill_rate,
    csl_from_z,
    z_from_csl,
    sigma_x_sQ,
    sigma_x_RS,
    annual_holding_cost,
    annual_ordering_cost,
    demo_inventory_path,
    WEEKS_PER_YEAR,
)

st.set_page_config(page_title="SKU Explorer | Inventory Simulator", layout="wide")

show_banner()

# ── SIDEBAR CONTROLS ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## SKU Explorer Controls")
    st.divider()

    scenario_names = list(SCENARIOS.keys()) + ["Custom SKU"]
    selected_name = st.selectbox("Select SKU scenario", scenario_names, index=0)

    if selected_name == "Custom SKU":
        st.markdown("**Custom SKU parameters**")
        sku_family = st.selectbox(
            "Family", ["Powertrain", "Chassis", "Electrical", "Critical"]
        )
        sku_pattern = st.selectbox("Demand pattern", ["Stable", "Volatile", "Lumpy"])
        dm = st.slider("Weekly demand mean (units)", 5, 2000, 200)
        cv = st.slider("Demand CV (variability)", 0.05, 1.0, 0.25)
        ds = dm * cv
        lt_m = st.slider("Lead time mean (weeks)", 1, 20, 4)
        lt_s = st.slider("Lead time std dev (weeks)", 0.0, 5.0, 0.5)
        uc = st.slider("Unit cost ($)", 5, 2000, 100)
        hp = st.slider("Holding cost % p.a.", 0.15, 0.40, 0.25)
        oc = st.slider("Order cost ($ per order)", 50, 3000, 400)
        bpw = st.slider("Backlog cost ($/unit/week)", 1, 500, 20)
        rp = st.slider("Review period (weeks, 0 = continuous)", 0, 4, 0)
        scenario = {
            "tagline": "Custom SKU — your parameters",
            "family": sku_family,
            "demand_pattern": sku_pattern,
            "weekly_demand_mean": dm,
            "weekly_demand_cv": cv,
            "weekly_demand_std": ds,
            "lead_time_mean_weeks": lt_m,
            "lead_time_std_weeks": lt_s,
            "unit_cost": uc,
            "holding_cost_pct": hp,
            "order_cost": oc,
            "backlog_cost_unit_week": bpw,
            "review_period_weeks": rp,
            "recommended_policy": "(s,Q)" if rp == 0 else "(R,S)",
        }
    else:
        scenario = get_scenario_params(selected_name)

    st.divider()

    forecast_mode = st.radio(
        "Forecast quality",
        ["ML-Improved", "Baseline"],
        index=0,
        help=(
            "ML-Improved: bias corrected, σ reduced by 20%.\n"
            "Baseline: +10% demand bias, +20% variability."
        ),
    )

    policy = st.radio(
        "Inventory policy",
        [
            "(s,Q) — continuous review, fixed qty",
            "(R,S) — periodic review, variable qty",
        ],
        index=0 if scenario.get("recommended_policy") == "(s,Q)" else 1,
        help=(
            "(s,Q): reorder whenever inventory hits the trigger level.\n"
            "(R,S): top up to S every R weeks."
        ),
    )
    use_sQ = policy.startswith("(s,Q)")

    target_csl = st.slider(
        "Target service level (CSL)",
        min_value=0.90,
        max_value=0.999,
        value=0.95,
        step=0.001,
        format="%.1f%%",
        help="Probability of no stock-out per replenishment cycle",
    )

    service_metric = st.radio(
        "Primary service metric",
        ["Cycle Service Level (CSL)", "Fill Rate (β)"],
        index=0,
        help=(
            "CSL = probability of no stock-out per cycle.\n"
            "Fill Rate = % of weekly demand served from stock."
        ),
    )

    if not use_sQ:
        review_period = st.slider(
            "Review period (weeks)",
            min_value=1,
            max_value=4,
            value=max(1, scenario.get("review_period_weeks", 1)),
        )
    else:
        review_period = 0

    seed = st.number_input(
        "Trajectory seed (change to re-run demand ↻)", value=42, step=1
    )

# ── DERIVE PARAMETERS ─────────────────────────────────────────────────────────
dm_raw = scenario["weekly_demand_mean"]
ds_raw = scenario.get(
    "weekly_demand_std", dm_raw * scenario.get("weekly_demand_cv", 0.2)
)
lt_m = scenario["lead_time_mean_weeks"]
lt_s = scenario["lead_time_std_weeks"]
uc = scenario["unit_cost"]
hp = scenario["holding_cost_pct"]
oc = scenario["order_cost"]
rp = review_period

# Baseline: +10% demand mean (over-forecast bias), +20% σ
dm_base = dm_raw * 1.10
ds_base = ds_raw * 1.20
# ML: corrected bias, 20% tighter σ
dm_ml = dm_raw
ds_ml = ds_raw * 0.80

dm_act = dm_ml if forecast_mode == "ML-Improved" else dm_base
ds_act = ds_ml if forecast_mode == "ML-Improved" else ds_base

z = z_from_csl(target_csl)

annual_demand = dm_raw * WEEKS_PER_YEAR
h_per_unit = uc * hp
q_star = max(eoq(annual_demand, oc, h_per_unit), 1.0)


def calc_ss(dm: float, ds: float) -> tuple[float, float, float, float]:
    """Return (ss, sigma_x, rop_or_S, cycle_demand)."""
    if use_sQ:
        ss_val = safety_stock_sQ(z, dm, ds, lt_m, lt_s)
        sx = sigma_x_sQ(dm, ds, lt_m, lt_s)
        level = reorder_point(dm, lt_m, ss_val)
        cd = dm * lt_m
    else:
        ss_val = safety_stock_RS(z, dm, ds, lt_m, lt_s, rp)
        sx = sigma_x_RS(dm, ds, lt_m, lt_s, rp)
        level = order_up_to(dm, lt_m, rp, ss_val)
        cd = dm * (lt_m + rp)
    return ss_val, sx, level, cd


ss_base, sx_base, level_base, cd_base = calc_ss(dm_base, ds_base)
ss_act, sx_act, level_act, cd_act = calc_ss(dm_act, ds_act)

# Fill rates
fr_base = fill_rate(ss_base, sx_base, max(cd_base, 1.0))
fr_act = fill_rate(ss_act, sx_act, max(cd_act, 1.0))

# Costs
avg_inv_base = ss_base + q_star / 2.0
avg_inv_act = ss_act + q_star / 2.0

hold_base = annual_holding_cost(avg_inv_base, uc, hp)
hold_act = annual_holding_cost(avg_inv_act, uc, hp)
order_cost_annual = annual_ordering_cost(annual_demand, q_star, oc)
total_base = hold_base + order_cost_annual
total_act = hold_act + order_cost_annual
saving_vs_base = total_base - total_act  # positive = saving

ss_value_base = ss_base * uc
ss_value_act = ss_act * uc
delta_ss_units = ss_act - ss_base
delta_ss_val = ss_value_act - ss_value_base

policy_label = "(s,Q) — Continuous Review" if use_sQ else "(R,S) — Periodic Review"
level_label = "Order trigger (ROP)" if use_sQ else "Order-up-to level (S)"

# ── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown(f"# {selected_name}")

fam_color = {
    "Powertrain": PRIMARY,
    "Chassis": WARNING,
    "Electrical": SUCCESS,
    "Critical": DANGER,
}
fc = fam_color.get(scenario["family"], NEUTRAL)

st.markdown(
    f'<p style="font-size:1.1rem;color:#555;">{scenario["tagline"]}</p>'
    f'<span style="background:{fc};color:white;padding:3px 10px;border-radius:12px;'
    f'font-size:0.8rem;margin-right:6px;">{scenario["family"]}</span>'
    f'<span style="background:{NEUTRAL};color:white;padding:3px 10px;border-radius:12px;'
    f'font-size:0.8rem;margin-right:6px;">{scenario.get("demand_pattern", "")}</span>'
    f'<span style="background:{PRIMARY};color:white;padding:3px 10px;border-radius:12px;'
    f'font-size:0.8rem;">{policy_label}</span>',
    unsafe_allow_html=True,
)
st.divider()

# ── [2] METRIC TILES ──────────────────────────────────────────────────────────
mc1, mc2, mc3, mc4 = st.columns(4)

with mc1:
    st.metric(
        label=f"Safety stock (units) — ~${ss_value_act:,.0f} value",
        value=f"~{ss_act:.0f} units",
        delta=f"{delta_ss_units:+.0f} units vs baseline",
        delta_color="inverse",  # negative delta is good (fewer units needed)
    )
with mc2:
    st.metric(
        label=level_label,
        value=f"~{level_act:.0f} units",
        delta=f"{level_act - level_base:+.0f} vs baseline",
        delta_color="inverse",
    )
with mc3:
    st.metric(
        label="Optimal order qty (EOQ)",
        value=f"~{q_star:.0f} units",
        help="Economic Order Quantity — minimizes total ordering + holding cost",
    )
with mc4:
    color_delta = "normal" if saving_vs_base >= 0 else "inverse"
    st.metric(
        label="Annual cost saving vs baseline",
        value=f"~${abs(saving_vs_base):,.0f}",
        delta=f"{'saved' if saving_vs_base >= 0 else 'added cost'} vs baseline",
        delta_color=color_delta,
    )

st.divider()

# ── [3] FORMULA PANEL ─────────────────────────────────────────────────────────
with st.expander(
    "📐 Show the calculation — how safety stock is derived", expanded=True
):
    fcol1, fcol2 = st.columns([1, 1.2])

    with fcol1:
        if use_sQ:
            st.markdown("**Formula: (s,Q) policy — Vandeput (2020) Ch. 6, eq. 6.4**")
            st.latex(
                r"\sigma_x = \sqrt{\mu_L \cdot \sigma_d^2 + \sigma_L^2 \cdot \mu_d^2}"
            )
            st.latex(r"SS = Z_{\alpha} \cdot \sigma_x")
            st.latex(r"\text{Order trigger} = \mu_d \cdot \mu_L + SS")

            st.markdown("**Substituting current values:**")
            st.latex(
                rf"\sigma_x = \sqrt{{{lt_m:.1f} \cdot {ds_act:.1f}^2 "
                rf"+ {lt_s:.1f}^2 \cdot {dm_act:.1f}^2}} = {sx_act:.1f}"
            )
            st.latex(
                rf"SS = {z:.3f} \cdot {sx_act:.1f} = \mathbf{{{ss_act:.0f} \text{{ units}}}}"
            )
            st.latex(
                rf"\text{{Order trigger}} = {dm_act:.1f} \cdot {lt_m:.1f} + {ss_act:.0f} "
                rf"= \mathbf{{{level_act:.0f} \text{{ units}}}}"
            )
        else:
            st.markdown("**Formula: (R,S) policy — Vandeput (2020) Ch. 6, eq. 6.5**")
            st.latex(
                r"\sigma_x = \sqrt{(\mu_L + R) \cdot \sigma_d^2 + \sigma_L^2 \cdot \mu_d^2}"
            )
            st.latex(r"SS = Z_{\alpha} \cdot \sigma_x")
            st.latex(r"S = \mu_d \cdot (\mu_L + R) + SS")

            st.markdown("**Substituting current values:**")
            st.latex(
                rf"\sigma_x = \sqrt{{({lt_m:.1f} + {rp}) \cdot {ds_act:.1f}^2 "
                rf"+ {lt_s:.1f}^2 \cdot {dm_act:.1f}^2}} = {sx_act:.1f}"
            )
            st.latex(
                rf"SS = {z:.3f} \cdot {sx_act:.1f} = \mathbf{{{ss_act:.0f} \text{{ units}}}}"
            )
            st.latex(
                rf"S = {dm_act:.1f} \cdot ({lt_m:.1f} + {rp}) + {ss_act:.0f} "
                rf"= \mathbf{{{level_act:.0f} \text{{ units}}}}"
            )

    with fcol2:
        st.markdown(
            f"""
            <div style="background:#f0f4fa;border-left:4px solid {PRIMARY};
                 padding:1rem;border-radius:0 8px 8px 0;line-height:1.8;">
            <strong>Plain-language explanation:</strong><br><br>
            <strong>σx</strong> = demand uncertainty over the replenishment time.<br>
            The higher it is, the more buffer stock you need.<br><br>
            Both <strong>demand variability (σd = {ds_act:.1f} units/week)</strong> AND
            <strong>lead time variability (σL = {lt_s:.1f} weeks)</strong> contribute.<br><br>
            For PACCAR's international supply chains, long and
            unreliable lead times make σL just as important as σd.<br><br>
            <strong>Z = {z:.3f}</strong> = the protection factor at {target_csl * 100:.1f}% CSL.
            Higher service targets require exponentially more buffer stock.
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── [4] FILL RATE vs CSL ──────────────────────────────────────────────────────
st.markdown("### Fill rate vs. Cycle service level — what's the difference?")

sc1, sc2 = st.columns(2)
csl_val = csl_from_z(z)
fr_display = fr_act

with sc1:
    st.markdown(
        f"""
        <div style="background:#f0f4fa;border:2px solid {PRIMARY};border-radius:10px;
             padding:1.2rem;text-align:center;">
        <h2 style="color:{PRIMARY};margin:0;">{csl_val * 100:.1f}%</h2>
        <strong>Cycle Service Level (CSL)</strong><br>
        <span style="color:#555;font-size:0.9rem;">
        Probability of <em>no stock-out</em> in a single replenishment cycle
        </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with sc2:
    st.markdown(
        f"""
        <div style="background:#f0faf6;border:2px solid {SUCCESS};border-radius:10px;
             padding:1.2rem;text-align:center;">
        <h2 style="color:{SUCCESS};margin:0;">{fr_display * 100:.1f}%</h2>
        <strong>Fill Rate (β)</strong><br>
        <span style="color:#555;font-size:0.9rem;">
        % of weekly demand <em>served directly from stock</em>
        </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.warning(
    f"**Same safety stock — very different numbers.** "
    f"Setting safety stock to achieve {csl_val * 100:.1f}% CSL "
    f"actually delivers ~{fr_display * 100:.1f}% fill rate on this SKU. "
    f"Most PACCAR planners track fill rate — make sure your safety stock target "
    f"is calibrated to the right metric, or you may be over-stocking significantly."
)

st.divider()

# ── [5] ANNUAL COST BREAKDOWN ─────────────────────────────────────────────────
st.markdown("### Annual cost breakdown — baseline vs. current settings")

# CHOICE: using a grouped bar because the side-by-side comparison per cost component
# makes it immediately clear where savings come from (holding cost, not ordering).
fig_cost = go.Figure()

categories = ["Holding Cost", "Ordering Cost", "Total Cost"]
vals_base = [hold_base, order_cost_annual, total_base]
vals_act = [hold_act, order_cost_annual, total_act]

fig_cost.add_trace(
    go.Bar(
        name="Baseline",
        x=categories,
        y=vals_base,
        marker_color=NEUTRAL,
        text=[f"${v:,.0f}" for v in vals_base],
        textposition="outside",
    )
)
fig_cost.add_trace(
    go.Bar(
        name=f"Current ({forecast_mode})",
        x=categories,
        y=vals_act,
        marker_color=SUCCESS if forecast_mode == "ML-Improved" else WARNING,
        text=[f"${v:,.0f}" for v in vals_act],
        textposition="outside",
    )
)

# Annotate savings on the Total bar
if saving_vs_base > 0:
    fig_cost.add_annotation(
        x="Total Cost",
        y=max(total_base, total_act) * 1.15,
        text=f"saves ~${saving_vs_base:,.0f}/year",
        showarrow=False,
        font=dict(color=SUCCESS, size=13, family="Arial Black"),
    )

fig_cost.update_layout(
    title="Annual inventory cost: holding + ordering",
    barmode="group",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    template="plotly_white",
    yaxis_title="Annual cost ($)",
    xaxis_title="Cost component",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=420,
)
st.plotly_chart(fig_cost, use_container_width=True)

st.divider()

# ── [6] 52-WEEK INVENTORY TRAJECTORY ─────────────────────────────────────────
st.markdown("### 52-week inventory trajectory — simulated demand path")

path = demo_inventory_path(
    demand_mean=dm_act,
    demand_std=ds_act,
    rop=level_act,
    order_qty=q_star,
    lead_time=lt_m,
    weeks=52,
    seed=int(seed),
)

weeks_x = path["weeks"]
inv_y = path["inventory"]
rop_line = path["rop"]
ss_line = max(path["safety_stock"], 0)
so_weeks = path["stockout_weeks"]

fig_traj = go.Figure()

# Safety stock zone
fig_traj.add_hrect(
    y0=0,
    y1=ss_line,
    fillcolor=SUCCESS,
    opacity=0.08,
    line_width=0,
    annotation_text="Safety stock zone",
    annotation_position="top right",
    annotation_font_color=SUCCESS,
)

# On-hand inventory
fig_traj.add_trace(
    go.Scatter(
        x=weeks_x,
        y=inv_y,
        name="On-hand inventory",
        line=dict(color=PRIMARY, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(24, 95, 165, 0.07)",
    )
)

# ROP line
fig_traj.add_hline(
    y=rop_line,
    line_dash="dash",
    line_color=WARNING,
    annotation_text=f"{level_label}: {rop_line:.0f}",
    annotation_position="right",
    annotation_font_color=WARNING,
)

# Safety stock line
if ss_line > 0:
    fig_traj.add_hline(
        y=ss_line,
        line_dash="dot",
        line_color=NEUTRAL,
        annotation_text=f"Safety stock: {ss_line:.0f}",
        annotation_position="right",
        annotation_font_color=NEUTRAL,
    )

# Stock-out markers
if so_weeks:
    fig_traj.add_trace(
        go.Scatter(
            x=so_weeks,
            y=[0] * len(so_weeks),
            mode="markers",
            name="Stock-out week",
            marker=dict(symbol="triangle-up", color=DANGER, size=14),
        )
    )

fig_traj.update_layout(
    title=(
        f"{policy_label} — {selected_name[:30]} — "
        f"~{target_csl * 100:.1f}% CSL → ~{fr_display * 100:.1f}% fill rate"
    ),
    xaxis_title="Week",
    yaxis_title="Units on hand",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    template="plotly_white",
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_traj, use_container_width=True)

n_stockouts = len(so_weeks)
if n_stockouts > 0:
    st.error(
        f"⚠️ {n_stockouts} stock-out week(s) in this 52-week path. "
        f"Consider raising the service level target or reviewing lead time assumptions."
    )
else:
    st.success(
        f"✓ Zero stock-outs in this 52-week path at {target_csl * 100:.1f}% CSL."
    )

st.divider()

# ── [7] INSIGHT CALLOUT ───────────────────────────────────────────────────────
comparable_skus = {
    "Powertrain": 500,
    "Chassis": 300,
    "Electrical": 200,
    "Critical": 100,
}.get(scenario["family"], 300)

portfolio_impact = abs(saving_vs_base) * comparable_skus

if forecast_mode == "ML-Improved":
    st.success(
        f"**✦ ML forecast active — systematic bias corrected.**  \n"
        f"Safety stock drops from ~{ss_base:.0f} → ~{ss_act:.0f} units "
        f"(~${ss_value_base:,.0f} → ~${ss_value_act:,.0f} in held inventory).  \n"
        f"Annual cost saving: ~${saving_vs_base:,.0f} per SKU.  \n"
        f"On ~{comparable_skus} comparable {scenario['family']} SKUs, "
        f"that compounds to **~${portfolio_impact:,.0f} freed annually.**"
    )
else:
    st.warning(
        f"**⚠ Baseline forecast active — bias is inflating safety stock.**  \n"
        f"The +10% demand bias and +20% variability inflate safety stock "
        f"from ~{ss_act:.0f} → ~{ss_base:.0f} units.  \n"
        f"Switch to ML-Improved to see the saving: ~${abs(saving_vs_base):,.0f}/year per SKU.  \n"
        f"On ~{comparable_skus} {scenario['family']} SKUs: **~${portfolio_impact:,.0f}/year**."
    )

st.info(
    "→ **Next: Portfolio View** — see how these individual SKU results add up "
    "across the full 120-SKU synthetic PACCAR portfolio."
)

show_footer(
    [
        "(s,Q) formula: Vandeput (2020) eq. 6.4",
        "Fill rate: eq. 7.3",
        "All KPIs approximated (~) from synthetic parameters",
    ]
)
