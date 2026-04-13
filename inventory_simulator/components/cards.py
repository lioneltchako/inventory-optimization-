"""Metric card components for the Dynacraft dashboard."""

from __future__ import annotations

import streamlit as st


def metric_card(
    label: str,
    value: str,
    delta: str | None = None,
    delta_color: str = "normal",
) -> None:
    """Render a single st.metric card."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def summary_card_row(metrics: list[dict[str, str]]) -> None:
    """Render a row of metric cards from a list of dicts."""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            metric_card(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                delta_color=m.get("delta_color", "normal"),
            )
