"""Inventory Policy Simulator — DynaCraft / PACCAR.

Entry point for the Streamlit multi-page application. Uses st.navigation()
to wire pages defined in inventory_simulator/ui/. CSS is injected once here
so it applies globally across all pages.
"""

import streamlit as st

from inventory_simulator.styles.theme import COLOR_MAP, get_css

st.set_page_config(
    page_title="Inventory Policy Simulator | PACCAR",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject shared CSS before any page content renders
st.markdown(f"<style>{get_css()}</style>", unsafe_allow_html=True)

# ── Page definitions ──────────────────────────────────────────────────────────

overview_page = st.Page(
    "inventory_simulator/ui/overview.py",
    title="Overview",
    icon="📊",
    default=True,
)
portfolio_page = st.Page(
    "inventory_simulator/ui/portfolio.py",
    title="Portfolio",
    icon="🗂️",
)
sku_explorer_page = st.Page(
    "inventory_simulator/ui/sku_explorer.py",
    title="SKU Explorer",
    icon="🔍",
)
methodology_page = st.Page(
    "inventory_simulator/ui/methodology.py",
    title="Methodology",
    icon="📐",
)
business_case_page = st.Page(
    "inventory_simulator/ui/business_case.py",
    title="Business Case",
    icon="💼",
)

pg = st.navigation(
    {
        "Analytics": [overview_page, portfolio_page, sku_explorer_page],
        "Reference": [methodology_page, business_case_page],
    }
)

# ── Sidebar branding ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        f"""
        <div style='background:{COLOR_MAP["accent"]};color:white;
                    padding:8px 12px;border-radius:6px;font-weight:700;
                    font-size:1rem;margin-bottom:4px;'>
            📦 Inventory Simulator
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("DynaCraft / PACCAR — Demand Planning")

pg.run()
