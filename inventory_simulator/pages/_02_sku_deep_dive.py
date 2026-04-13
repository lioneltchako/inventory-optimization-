"""Page 2 — SKU Deep Dive (Main Demo Screen).

Interactive parameter sliders, live policy output with cost breakdown,
demand/forecast chart, and inventory simulation.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from inventory_simulator.components.cards import metric_card
from inventory_simulator.components.charts import (
    cost_breakdown_bar,
    demand_forecast_chart,
    inventory_simulation_chart,
)
from inventory_simulator.data.contracts import (
    PolicyResult,
    PrecomputedData,
    SKUForecastResult,
)
from inventory_simulator.data.precompute import _compute_policy


def _simulate_inventory(
    avg_weekly_demand: float,
    rop: float,
    eoq: float,
    lead_time_weeks: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate 52-week inventory trajectory."""
    levels = np.zeros(52)
    stockout_weeks_list: list[int] = []
    on_hand = rop + eoq
    pending_orders: list[int] = []

    for week in range(52):
        on_hand -= avg_weekly_demand
        pending_orders = [p - 1 for p in pending_orders]
        arrived = sum(1 for p in pending_orders if p <= 0)
        on_hand += arrived * eoq
        pending_orders = [p for p in pending_orders if p > 0]
        if on_hand <= rop and len(pending_orders) == 0:
            pending_orders.append(max(lead_time_weeks, 1))
        if on_hand < 0:
            stockout_weeks_list.append(week + 1)
        levels[week] = on_hand

    return levels, np.array(stockout_weeks_list)


def _render_sliders(
    sku: SKUForecastResult,
    col: DeltaGenerator,
) -> tuple[float, int, int, float, float]:
    """Render parameter sliders in the left column."""
    with col:
        st.subheader("Parameters")
        service_level = (
            st.slider(
                "Target Service Level",
                min_value=85,
                max_value=99,
                value=95,
                step=1,
                key="sl_slider",
            )
            / 100.0
        )

        lt_adj = st.slider(
            "Lead Time Adjustment (days)",
            min_value=-7,
            max_value=14,
            value=0,
            step=1,
            key="lt_slider",
        )
        eff_lt = max(1, sku.lead_time_days + lt_adj)
        st.caption(f"Effective lead time: {eff_lt} days")

        review_options = {"Daily (1)": 1, "Weekly (7)": 7, "Biweekly (14)": 14}
        default_key = next(
            (k for k, v in review_options.items() if v == sku.review_period_days),
            "Weekly (7)",
        )
        review_sel = st.selectbox(
            "Review Period",
            list(review_options.keys()),
            index=list(review_options.keys()).index(default_key),
            key="rp_select",
        )
        review_period = review_options[review_sel]

        holding_rate = (
            st.slider(
                "Holding Cost Rate (%)",
                min_value=15,
                max_value=40,
                value=int(sku.holding_cost_rate * 100),
                step=1,
                key="hr_slider",
            )
            / 100.0
        )

        demand_scenario = st.selectbox(
            "Demand Scenario",
            ["Baseline", "Surge +20%", "Drop -30%"],
            key="demand_select",
        )
        multiplier_map = {"Baseline": 1.0, "Surge +20%": 1.2, "Drop -30%": 0.7}
        demand_mult = multiplier_map[demand_scenario]

    return service_level, eff_lt, review_period, holding_rate, demand_mult


def _render_policy_output(
    col: DeltaGenerator,
    policy: PolicyResult,
    baseline: PolicyResult,
) -> None:
    """Render live policy output in the center column."""
    with col:
        st.subheader("Recommended Policy")
        c1, c2 = st.columns(2)
        with c1:
            metric_card(
                "Safety Stock",
                f"{policy.safety_stock:,.0f} units",
                delta=f"{policy.safety_stock - baseline.safety_stock:+,.0f} vs baseline",
            )
            metric_card(
                "Reorder Point",
                f"{policy.reorder_point:,.0f}",
                delta=f"{policy.reorder_point - baseline.reorder_point:+,.0f} vs baseline",
            )
        with c2:
            metric_card("EOQ", f"{policy.eoq:,.0f} units")
            metric_card("SS Days of Cover", f"{policy.ss_days_of_cover:,.1f} days")

        delta_cost = policy.total_annual_cost - baseline.total_annual_cost
        sign = "+" if delta_cost >= 0 else ""
        st.metric(
            "Annual Total Cost",
            f"${policy.total_annual_cost:,.0f}",
            delta=f"{sign}${delta_cost:,.0f} vs baseline",
            delta_color="inverse",
        )
        st.plotly_chart(
            cost_breakdown_bar(
                policy.holding_cost, policy.ordering_cost, policy.stockout_cost
            ),
            use_container_width=True,
        )


def _render_charts(
    col: DeltaGenerator,
    sku: SKUForecastResult,
    policy: PolicyResult,
    baseline: PolicyResult,
    demand_mult: float,
    eff_lt: int,
) -> None:
    """Render demand/forecast and simulation charts."""
    with col:
        weekly_fc = np.array(
            [
                sku.forecast[i * 7 : (i + 1) * 7].sum()
                for i in range(len(sku.forecast) // 7)
            ]
        )
        st.plotly_chart(
            demand_forecast_chart(
                sku.demand_history,
                weekly_fc,
                sku.residuals,
                baseline.reorder_point,
                policy.reorder_point,
            ),
            use_container_width=True,
        )

        awd = sku.avg_weekly_demand * demand_mult
        lt_weeks = max(1, eff_lt // 7)
        levels, stockouts = _simulate_inventory(
            awd, policy.reorder_point, policy.eoq, lt_weeks
        )
        st.plotly_chart(
            inventory_simulation_chart(levels, stockouts, policy.reorder_point),
            use_container_width=True,
        )


def _handle_save_scenario(policy: PolicyResult, params: dict[str, Any]) -> None:
    """Handle save scenario button click."""
    st.session_state["scenario_c"] = {
        "name": "Custom Scenario",
        "service_level": params["service_level"],
        "lead_time_days": params["eff_lt"],
        "review_period_days": params["review_period"],
        "holding_cost_rate": params["holding_rate"],
        "demand_multiplier": params["demand_mult"],
        "policy": {
            "safety_stock": policy.safety_stock,
            "reorder_point": policy.reorder_point,
            "eoq": policy.eoq,
            "holding_cost": policy.holding_cost,
            "ordering_cost": policy.ordering_cost,
            "stockout_cost": policy.stockout_cost,
            "total_annual_cost": policy.total_annual_cost,
            "ss_days_of_cover": policy.ss_days_of_cover,
            "service_level": params["service_level"],
        },
    }
    st.success("Scenario saved! View it on the Scenario Comparison page.")


def render(data: PrecomputedData) -> None:
    """Render the SKU Deep Dive page."""
    st.header("If I change my service level target, what does it cost me?")

    sku_options = list(data.sku_outputs.keys())
    default_idx = 0
    if (
        "selected_sku" in st.session_state
        and st.session_state["selected_sku"] in sku_options
    ):
        default_idx = sku_options.index(st.session_state["selected_sku"])

    selected_sku = st.selectbox(
        "Select SKU", sku_options, index=default_idx, key="dd_sku_select"
    )
    st.session_state["selected_sku"] = selected_sku
    sku = data.sku_outputs[selected_sku]
    baseline = data.baseline_policies[selected_sku]

    col_left, col_center, col_right = st.columns([1, 1.5, 2])
    sl, eff_lt, review_period, holding_rate, demand_mult = _render_sliders(
        sku, col_left
    )

    policy = _compute_policy(
        sku,
        sl,
        lead_time_override=eff_lt,
        review_override=review_period,
        holding_rate_override=holding_rate,
        demand_multiplier=demand_mult,
    )

    _render_policy_output(col_center, policy, baseline)
    _render_charts(col_right, sku, policy, baseline, demand_mult, eff_lt)

    st.divider()
    params: dict[str, Any] = {
        "service_level": sl,
        "eff_lt": eff_lt,
        "review_period": review_period,
        "holding_rate": holding_rate,
        "demand_mult": demand_mult,
    }
    if st.button("Save as Scenario C", type="primary"):
        _handle_save_scenario(policy, params)
