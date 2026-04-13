"""Dynacraft Inventory Simulator — Entry Point.

Portfolio demo for a supply chain director: ML-forecast-error-based
inventory policy optimization across 50 SKUs.
"""

from __future__ import annotations

import types

import streamlit as st

from inventory_simulator.data.contracts import PrecomputedData
from inventory_simulator.data.generator import generate_phase1_outputs
from inventory_simulator.data.precompute import precompute_all
from inventory_simulator.pages import (
    _01_portfolio as p01_portfolio,
    _02_sku_deep_dive as p02_sku_deep_dive,
    _03_scenario as p03_scenario,
    _04_frontier as p04_frontier,
    _05_next_steps as p05_next_steps,
)

st.set_page_config(
    page_title="Dynacraft Inventory Simulator",
    page_icon="🏭",
    layout="wide",
)

PAGE_MAP: dict[str, types.ModuleType] = {
    "Portfolio Health": p01_portfolio,
    "SKU Deep Dive": p02_sku_deep_dive,
    "Scenario Comparison": p03_scenario,
    "Cost vs Service Level": p04_frontier,
    "Next Steps & Methodology": p05_next_steps,
}


@st.cache_data(show_spinner="Generating SKU data & computing policies...")
def _load_data() -> PrecomputedData:
    """Load and precompute all data at startup."""
    outputs = generate_phase1_outputs(seed=42)
    return precompute_all(outputs)


def _render_sidebar(data: PrecomputedData) -> str:
    """Render the sidebar with branding and navigation."""
    with st.sidebar:
        st.title("🏭 Dynacraft")
        st.caption("Inventory Policy Simulator")
        st.divider()
        page = st.radio("Navigate", list(PAGE_MAP.keys()), label_visibility="collapsed")
        st.divider()
        selected_sku = st.session_state.get(
            "selected_sku", list(data.sku_outputs.keys())[0]
        )
        if page not in ("Portfolio Health", "Next Steps & Methodology"):
            st.caption(f"Active SKU: **{selected_sku}**")
        st.caption("Phase 2: Inventory Optimization Layer")
    return page  # type: ignore[return-value]


def main() -> None:
    """Main application entry point."""
    if "selected_sku" not in st.session_state:
        st.session_state["selected_sku"] = "DYN-0001"

    data = _load_data()
    page = _render_sidebar(data)
    module = PAGE_MAP[page]
    module.render(data)  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
