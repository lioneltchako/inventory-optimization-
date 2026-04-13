"""Page 3 — Scenario Comparison.

Side-by-side comparison of three scenarios: Current Policy (A),
Lead Time +14 Days (B), and a user-saved custom scenario (C).
"""

from __future__ import annotations

import streamlit as st

from inventory_simulator.components.charts import cost_breakdown_bar
from inventory_simulator.components.tables import scenario_column
from inventory_simulator.data.contracts import PolicyResult, PrecomputedData


def _policy_to_dict(policy: PolicyResult) -> dict[str, float | str]:
    """Convert a PolicyResult to a display dict."""
    return {
        "service_level": policy.service_level,
        "safety_stock": policy.safety_stock,
        "ss_days_of_cover": policy.ss_days_of_cover,
        "reorder_point": policy.reorder_point,
        "eoq": policy.eoq,
        "total_annual_cost": policy.total_annual_cost,
        "holding_cost": policy.holding_cost,
        "ordering_cost": policy.ordering_cost,
        "stockout_cost": policy.stockout_cost,
    }


def _render_waterfall(baseline: PolicyResult, scenario_b: PolicyResult) -> None:
    """Render waterfall annotation for Scenario B."""
    ss_diff = scenario_b.safety_stock - baseline.safety_stock
    rop_diff = scenario_b.reorder_point - baseline.reorder_point
    cost_diff = scenario_b.total_annual_cost - baseline.total_annual_cost
    st.markdown(
        f"**Impact chain:** Lead time +14d "
        f"&rarr; risk horizon grew by 2 weeks "
        f"&rarr; SS grew by **{ss_diff:+,.0f}** units "
        f"&rarr; ROP grew by **{rop_diff:+,.0f}** units "
        f"&rarr; annual cost changed by **${cost_diff:+,.0f}**"
    )


def render(data: PrecomputedData) -> None:
    """Render the Scenario Comparison page."""
    st.header("What happens if my supplier delays 2 weeks?")

    sku_id = st.session_state.get("selected_sku", list(data.sku_outputs.keys())[0])
    st.caption(f"Comparing scenarios for **{sku_id}**")

    baseline = data.baseline_policies[sku_id]
    scenario_b = data.scenario_b_policies[sku_id]
    baseline_dict = _policy_to_dict(baseline)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        scenario_column("A: Current Policy", baseline_dict)
        st.plotly_chart(
            cost_breakdown_bar(
                baseline.holding_cost,
                baseline.ordering_cost,
                baseline.stockout_cost,
                "Scenario A",
            ),
            use_container_width=True,
        )

    with col_b:
        scenario_b_dict = _policy_to_dict(scenario_b)
        scenario_column("B: Lead Time +14 Days", scenario_b_dict, baseline_dict)
        st.plotly_chart(
            cost_breakdown_bar(
                scenario_b.holding_cost,
                scenario_b.ordering_cost,
                scenario_b.stockout_cost,
                "Scenario B",
            ),
            use_container_width=True,
        )

    with col_c:
        scenario_c_data = st.session_state.get("scenario_c")
        if scenario_c_data:
            c_policy = scenario_c_data["policy"]
            scenario_column("C: Custom Scenario", c_policy, baseline_dict)
            st.plotly_chart(
                cost_breakdown_bar(
                    c_policy["holding_cost"],
                    c_policy["ordering_cost"],
                    c_policy["stockout_cost"],
                    "Scenario C",
                ),
                use_container_width=True,
            )
        else:
            st.subheader("C: Custom Scenario")
            st.info("Save a scenario from the SKU Deep Dive page to compare it here.")

    st.divider()
    st.subheader("Scenario B Impact Analysis")
    _render_waterfall(baseline, scenario_b)
