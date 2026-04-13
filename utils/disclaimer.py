"""Shared disclaimer banner and footer functions."""

import streamlit as st


BANNER_TEXT = (
    "**Synthetic data disclaimer** — All parameters and KPIs on this page "
    "are computed from PACCAR-like scenarios designed to reflect real "
    "supply chain behavior. Actual results require real demand data and "
    "ERP integration. Approximated values are labeled with ~."
)


def show_banner() -> None:
    """Render the synthetic data disclaimer banner at the top of every page."""
    st.warning(BANNER_TEXT)


def show_footer(sources: list[str] | None = None) -> None:
    """Render page footer with data sources and methodology note."""
    default = [
        "Vandeput, N. (2020). Inventory Optimization: Models and Simulations. De Gruyter."
    ]
    refs = sources or default
    st.caption(" · ".join(refs))
