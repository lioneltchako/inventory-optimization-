"""Page 4 — Cost vs Service Level Frontier.

Shows the exact cost of any service level choice and the marginal
safety stock required for each percentage point improvement.
"""

from __future__ import annotations

import streamlit as st

from inventory_simulator.components.charts import frontier_chart, ss_vs_service_chart
from inventory_simulator.data.contracts import PrecomputedData
from inventory_simulator.data.precompute import SERVICE_LEVELS


def _get_frontier_data(
    data: PrecomputedData,
    sku_id: str,
) -> tuple[list[float], list[float], list[float]]:
    """Extract frontier data for a single SKU."""
    grid = data.ss_grid[sku_id]
    costs = [grid[sl].total_annual_cost for sl in SERVICE_LEVELS]
    ss_vals = [grid[sl].safety_stock for sl in SERVICE_LEVELS]
    return SERVICE_LEVELS, costs, ss_vals


def _get_portfolio_avg(
    data: PrecomputedData,
) -> tuple[list[float], list[float], list[float]]:
    """Compute portfolio average frontier."""
    n = len(data.sku_outputs)
    avg_costs = [0.0] * len(SERVICE_LEVELS)
    avg_ss = [0.0] * len(SERVICE_LEVELS)
    for sku_id in data.sku_outputs:
        grid = data.ss_grid[sku_id]
        for i, sl in enumerate(SERVICE_LEVELS):
            avg_costs[i] += grid[sl].total_annual_cost / n
            avg_ss[i] += grid[sl].safety_stock / n
    return SERVICE_LEVELS, avg_costs, avg_ss


def _render_frontier_charts(
    data: PrecomputedData,
    view_mode: str,
    sku_id: str,
    selected_sl: float,
) -> None:
    """Render the frontier and SS charts."""
    if view_mode == "Selected SKU":
        st.caption(f"Showing frontier for **{sku_id}**")
        sls, costs, ss_vals = _get_frontier_data(data, sku_id)
        bp = data.baseline_policies[sku_id]
        bl_cost, bl_ss = bp.total_annual_cost, bp.safety_stock
    else:
        st.caption("Showing **portfolio average** frontier")
        sls, costs, ss_vals = _get_portfolio_avg(data)
        n = len(data.baseline_policies)
        bl_cost = (
            sum(bp.total_annual_cost for bp in data.baseline_policies.values()) / n
        )
        bl_ss = sum(bp.safety_stock for bp in data.baseline_policies.values()) / n

    sl_idx = max(0, min(round((selected_sl - 0.85) / 0.01), len(sls) - 1))
    sel_cost, sel_ss = costs[sl_idx], ss_vals[sl_idx]

    st.plotly_chart(
        frontier_chart(sls, costs, 0.95, bl_cost, selected_sl, sel_cost),
        use_container_width=True,
    )
    st.plotly_chart(ss_vs_service_chart(sls, ss_vals), use_container_width=True)

    _render_summary_metrics(sel_cost, sel_ss, bl_cost, bl_ss)


def _render_summary_metrics(
    sel_cost: float,
    sel_ss: float,
    bl_cost: float,
    bl_ss: float,
) -> None:
    """Render the bottom summary metrics row."""
    st.divider()
    c1, c2, c3 = st.columns(3)
    delta_cost = sel_cost - bl_cost
    with c1:
        sign = "+" if delta_cost >= 0 else ""
        st.metric(
            "Cost Delta vs Baseline",
            f"${sel_cost:,.0f}",
            delta=f"{sign}${delta_cost:,.0f}",
            delta_color="inverse",
        )
    with c2:
        st.metric("Safety Stock at Selected SL", f"{sel_ss:,.0f} units")
    with c3:
        st.metric("Marginal SS", f"{sel_ss - bl_ss:+,.0f} units vs baseline")


def render(data: PrecomputedData) -> None:
    """Render the Cost vs Service Level Frontier page."""
    st.header("What is the exact cost of the service level I choose?")

    sku_id = st.session_state.get("selected_sku", list(data.sku_outputs.keys())[0])

    col_select, col_slider = st.columns([2, 3])
    with col_select:
        view_mode = st.radio(
            "View",
            ["Selected SKU", "Portfolio Average"],
            horizontal=True,
            key="frontier_view",
        )
    with col_slider:
        selected_sl = (
            st.slider(
                "Service Level (%)",
                min_value=85,
                max_value=99,
                value=95,
                step=1,
                key="frontier_sl_slider",
            )
            / 100.0
        )

    _render_frontier_charts(data, view_mode, sku_id, selected_sl)
