"""Page 5 — Next Steps & Methodology.

Roadmap and methodology explanations for the Dynacraft demo.
"""

from __future__ import annotations

import streamlit as st

from inventory_simulator.data.contracts import PrecomputedData


def _render_roadmap() -> None:
    """Render the implementation roadmap table."""
    st.subheader("Implementation Roadmap")
    roadmap_data = [
        (
            "1",
            "Done",
            "ML demand forecasting engine (Phase 1). Validated XGBoost vs baseline "
            "across full portfolio: ~7% MAE reduction, ~10% RMSE reduction, bias nearly "
            "eliminated (approx. -10% to approx. -1%). Proven that ML forecast residuals are "
            "the correct input for safety stock sizing.",
        ),
        (
            "2",
            "This Demo",
            "Inventory policy & cost optimization layer (Phase 2). Takes Phase 1 "
            "forecasts + residuals and computes safety stock, ROP, EOQ, and cost tradeoffs. "
            "Gives the director live control over policy parameters and scenario comparison.",
        ),
        (
            "3",
            "Next",
            "Conformal prediction — replace Z(alpha) x sigma with coverage-guaranteed "
            "quantiles. Same formula structure, no distributional assumption.",
        ),
        (
            "4",
            "Future",
            "Joint ROP + Q optimization under budget & service level constraints.",
        ),
        (
            "5",
            "Future",
            "Live ERP integration — replace synthetic data with Phase 1 feed.",
        ),
    ]
    header = "| Step | Status | Description |\n|------|--------|-------------|\n"
    rows = "\n".join(f"| {s} | {status} | {desc} |" for s, status, desc in roadmap_data)
    st.markdown(header + rows)


def _render_methodology() -> None:
    """Render methodology explainers in expandable sections."""
    st.subheader("Methodology")

    with st.expander("Why ML forecast error in safety stock (not demand variability)"):
        st.markdown(
            "Traditional safety stock formulas use the standard deviation of raw demand "
            "to size buffer inventory. But if you have a good forecast model, that raw "
            "variability includes trend and seasonality that the model already predicts. "
            "Counting it again inflates safety stock unnecessarily. Instead, we use the "
            "standard deviation of the model's residuals — the part of demand that the "
            "model could NOT predict. This gives a leaner, more accurate safety stock "
            "that reflects true uncertainty, not already-explained patterns."
        )

    with st.expander("Why risk horizon matters (square-root scaling)"):
        st.markdown(
            "Safety stock must cover uncertainty over the entire period from when you "
            "place an order to when it arrives and is reviewed — the risk horizon "
            "(lead time + review period). Uncertainty grows with the square root of "
            "time: if your lead time doubles, your safety stock grows by about 41%, "
            "not 100%. This square-root relationship is why even small lead time "
            "changes can meaningfully impact inventory costs, and why Scenario B "
            "(+14 days) shows a visible cost increase."
        )

    with st.expander("Why conformal prediction is the natural next step"):
        st.markdown(
            "Our current approach assumes residuals are roughly normal when we use "
            "Z(alpha) to set the safety stock multiplier. But the residual distribution "
            "in this demo is visibly right-skewed — the normal assumption underestimates "
            "tail risk. Conformal prediction provides coverage-guaranteed prediction "
            "intervals without any distributional assumption. It uses the same formula "
            "structure but replaces Z(alpha) x sigma with an empirical quantile from "
            "the residuals, giving honest coverage even with skewed or heavy-tailed errors."
        )

    with st.expander("Why joint optimization matters (EOQ and ROP are coupled)"):
        st.markdown(
            "In this demo, we compute EOQ and ROP independently — EOQ minimizes the "
            "holding-vs-ordering tradeoff, then ROP is set based on the safety stock "
            "formula. But in reality, order quantity affects how often you face stockout "
            "risk (more frequent, smaller orders mean more risk exposure cycles per year). "
            "Joint optimization of Q and ROP under a budget constraint and a minimum "
            "service level target would find the true cost-optimal policy. This is the "
            "standard (Q, R) model and would be the next analytical upgrade."
        )


def render(_data: PrecomputedData) -> None:
    """Render the Next Steps & Methodology page."""
    st.header("How do we make this real for Dynacraft?")
    _render_roadmap()
    st.divider()
    _render_methodology()
