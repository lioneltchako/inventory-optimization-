"""
Inventory Policy Simulator — DynaCraft / PACCAR
Senior Demand Planner Demo · Step 1 of 2

Navigation shell and sidebar. Pages live in pages/.
Methodology: Vandeput (2020) "Inventory Optimization: Models and Simulations"
"""

import streamlit as st
from pathlib import Path

# ── Page config — must be first Streamlit call ───────────────────────────────
st.set_page_config(
    page_title="Inventory Policy Simulator | DynaCraft / PACCAR",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load custom CSS ───────────────────────────────────────────────────────────
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📦 Inventory Policy Simulator")
    st.markdown("**DynaCraft / PACCAR** — Senior Demand Planner Demo")
    st.divider()

    st.markdown(
        """
        **Step 1 of 2 — Methodology demo**
        Formula-based simulator with 120 synthetic SKUs.

        *Step 2 (planned):* ML-powered simulation-optimization
        across the full 8,000-SKU portfolio with XGBoost
        forecast integration.
        """
    )
    st.divider()

    # Methodology badge
    st.markdown(
        '<span style="background:#1D9E75;color:white;padding:4px 10px;'
        'border-radius:12px;font-size:0.8rem;">📖 Vandeput (2020)</span>',
        unsafe_allow_html=True,
    )
    st.caption("Inventory Optimization: Models and Simulations. De Gruyter.")

    st.divider()
    st.markdown(
        """
        **Navigate using the pages above ↑**

        1. Overview — The problem & the tool
        2. SKU Explorer — Deep dive on one part
        3. Portfolio — 120-SKU impact view
        4. Methodology — Formulas explained
        5. Business Case — Executive summary
        """
    )

# ── Landing content (shown when user first opens the app) ────────────────────
st.markdown("# 📦 Inventory Policy Simulator")
st.markdown("### DynaCraft / PACCAR · Senior Demand Planner Demo · Step 1 of 2")
st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.info(
        "**1 · Overview**\n\n"
        "Why inventory optimization matters — the cost of getting it wrong."
    )
with col2:
    st.success(
        "**2 · SKU Explorer** ⭐\n\n"
        "Policy choice + forecast quality → safety stock & cost. Hero page."
    )
with col3:
    st.info(
        "**3 · Portfolio**\n\n"
        "120-SKU impact: how individual gains compound across the catalogue."
    )

col4, col5 = st.columns(2)
with col4:
    st.info(
        "**4 · Methodology**\n\n"
        "Formulas explained in plain supply chain language. Trust builder."
    )
with col5:
    st.info(
        "**5 · Business Case**\n\n"
        "Executive summary with one-pager PDF — the screenshot for leadership."
    )

st.divider()
st.markdown(
    "> **Select a page** from the left sidebar to begin the demo.  \n"
    "> Start with **Overview** for context, then **SKU Explorer** for the deep dive."
)
