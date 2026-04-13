"""Shared Streamlit UI components for the Inventory Policy Simulator."""

from __future__ import annotations

import streamlit as st

from inventory_simulator.styles.theme import COLOR_MAP


def render_hero_banner(headline: str, subtext: str) -> None:
    """Render a navy gradient hero banner with optional accent HTML in headline.

    Args:
        headline: Main headline text. May contain ``<span class="hero-accent">`` tags.
        subtext: Supporting sentence displayed below the headline.
    """
    st.markdown(
        f"""
        <div class="hero-banner">
            <h2>{headline}</h2>
            <p>{subtext}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_card(text: str) -> None:
    """Render an orange-bordered insight card.

    Args:
        text: Card body text (HTML supported).
    """
    st.markdown(
        f'<div class="insight-card">{text}</div>',
        unsafe_allow_html=True,
    )


def render_disclaimer() -> None:
    """Render the synthetic-data disclaimer caption."""
    st.caption(
        "⚠️ Synthetic data — all parameters reflect realistic heavy-duty truck "
        "parts distribution patterns and do not represent actual PACCAR or "
        "DynaCraft operational data."
    )


def criticality_badge(tier: str) -> str:
    """Return an HTML badge string for a criticality tier.

    Args:
        tier: One of "Critical", "Operational", or "Standard".

    Returns:
        HTML ``<span>`` element with tier-appropriate styling.
    """
    css_class = f"badge-{tier.lower()}"
    return f'<span class="{css_class}">{tier}</span>'


def color_for_criticality(tier: str) -> str:
    """Return the hex color associated with a criticality tier.

    Args:
        tier: One of "Critical", "Operational", or "Standard".

    Returns:
        Hex color string from the central COLOR_MAP.
    """
    mapping = {
        "Critical": COLOR_MAP["danger"],
        "Operational": COLOR_MAP["warning"],
        "Standard": COLOR_MAP["success"],
    }
    return mapping.get(tier, COLOR_MAP["muted"])
