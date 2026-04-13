"""Page 1 — Portfolio Health Dashboard.

Shows portfolio-level metrics, ranked SKU table with ML vs classical
safety stock comparison, and row selection for drill-down.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from inventory_simulator.components.cards import summary_card_row
from inventory_simulator.components.tables import portfolio_table
from inventory_simulator.data.contracts import PrecomputedData


def _build_portfolio_df(data: PrecomputedData) -> pd.DataFrame:
    """Build the portfolio health DataFrame for display."""
    rows = []
    for sku_id, sku in data.sku_outputs.items():
        bp = data.baseline_policies[sku_id]
        ml_holding = bp.holding_cost
        cl_holding = data.classical_ss_cost[sku_id]
        rows.append(
            {
                "sku_id": sku_id,
                "category": sku.category,
                "fill_rate_status": bp.fill_rate_status.title(),
                "reorder_point": round(bp.reorder_point),
                "safety_stock": round(bp.safety_stock),
                "ss_days_of_cover": round(bp.ss_days_of_cover, 1),
                "holding_cost": round(bp.holding_cost),
                "stockout_risk": round(data.stockout_risk_scores[sku_id]),
                "mean_error": round(float(np.mean(sku.residuals)), 1),
                "ml_ss_cost": round(ml_holding),
                "classical_ss_cost": round(cl_holding),
                "ss_savings": round(cl_holding - ml_holding),
            }
        )
    return pd.DataFrame(rows)


def _compute_summary_metrics(data: PrecomputedData) -> list[dict[str, str]]:
    """Compute the 5 summary metrics for the card row."""
    total_inv_value = sum(
        (bp.safety_stock + bp.eoq / 2) * data.sku_outputs[sid].unit_cost
        for sid, bp in data.baseline_policies.items()
    )
    avg_sl = 0.95
    below_target = sum(
        1 for bp in data.baseline_policies.values() if bp.fill_rate_status == "critical"
    )
    total_overstock = sum(
        max(0, data.classical_ss[sid] - bp.safety_stock)
        * data.sku_outputs[sid].unit_cost
        for sid, bp in data.baseline_policies.items()
    )
    total_stockout_exp = sum(bp.stockout_cost for bp in data.baseline_policies.values())

    return [
        {"label": "Total Inventory Value", "value": f"${total_inv_value:,.0f}"},
        {"label": "Baseline Service Level", "value": f"{avg_sl * 100:.0f}%"},
        {"label": "SKUs Below Target", "value": str(below_target)},
        {"label": "Overstock Savings (ML)", "value": f"${total_overstock:,.0f}"},
        {"label": "Annual Stockout Exposure", "value": f"${total_stockout_exp:,.0f}"},
    ]


def render(data: PrecomputedData) -> None:
    """Render the Portfolio Health page."""
    st.header(
        "Am I holding too much or too little — and which SKUs are costing me the most?"
    )

    with st.spinner("Computing portfolio metrics..."):
        summary_card_row(_compute_summary_metrics(data))

    st.divider()
    st.subheader("Portfolio SKU Health")

    df = _build_portfolio_df(data)
    df_sorted = df.sort_values("stockout_risk", ascending=False).reset_index(drop=True)
    portfolio_table(df_sorted)

    st.divider()
    st.subheader("Drill into a specific SKU")
    sku_options = list(data.sku_outputs.keys())
    default_idx = 0
    if (
        "selected_sku" in st.session_state
        and st.session_state["selected_sku"] in sku_options
    ):
        default_idx = sku_options.index(st.session_state["selected_sku"])

    selected = st.selectbox(
        "Select a SKU to analyze",
        sku_options,
        index=default_idx,
        key="portfolio_sku_select",
    )
    if selected:
        st.session_state["selected_sku"] = selected
        st.info(
            f"Selected **{selected}** — navigate to "
            "**SKU Deep Dive** in the sidebar for detailed analysis."
        )
