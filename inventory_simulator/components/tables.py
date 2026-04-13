"""Table components for portfolio display."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from inventory_simulator.theme import COLOR_MAP


def _color_fill_rate(val: str) -> str:
    """Return background-color style for fill rate status."""
    color_lookup = {
        "healthy": COLOR_MAP["healthy"],
        "at_risk": COLOR_MAP["at_risk"],
        "critical": COLOR_MAP["critical"],
    }
    bg = color_lookup.get(val, "")
    if bg:
        return f"background-color: {bg}; color: white; border-radius: 4px"
    return ""


def portfolio_table(df: pd.DataFrame) -> None:
    """Render the portfolio health table with conditional formatting."""
    display_df = df.copy()
    display_df = display_df.rename(
        columns={
            "sku_id": "SKU ID",
            "category": "Category",
            "fill_rate_status": "Service Status",
            "reorder_point": "Current ROP",
            "safety_stock": "Safety Stock (units)",
            "ss_days_of_cover": "SS (days cover)",
            "holding_cost": "Annual Holding ($)",
            "stockout_risk": "Stockout Risk",
            "mean_error": "Mean Error",
            "ml_ss_cost": "ML-Based SS ($)",
            "classical_ss_cost": "Classical SS ($)",
            "ss_savings": "ML Savings ($)",
        }
    )
    st.dataframe(
        display_df,
        use_container_width=True,
        height=450,
        hide_index=True,
    )


def scenario_column(
    scenario_name: str,
    policy_data: dict[str, float | str],
    baseline_data: dict[str, float | str] | None = None,
) -> None:
    """Render a scenario column with metrics and deltas."""
    st.subheader(scenario_name)
    _render_metric(
        "Service Level", policy_data, baseline_data, "service_level", pct=True
    )
    _render_metric(
        "Safety Stock (units)", policy_data, baseline_data, "safety_stock", fmt_int=True
    )
    _render_metric("SS (days cover)", policy_data, baseline_data, "ss_days_of_cover")
    _render_metric("ROP", policy_data, baseline_data, "reorder_point", fmt_int=True)
    _render_metric("EOQ", policy_data, baseline_data, "eoq", fmt_int=True)
    _render_metric(
        "Annual Cost", policy_data, baseline_data, "total_annual_cost", dollar=True
    )


def _render_metric(
    label: str,
    data: dict[str, float | str],
    baseline: dict[str, float | str] | None,
    key: str,
    pct: bool = False,
    dollar: bool = False,
    fmt_int: bool = False,
) -> None:
    """Render a single metric with optional delta vs baseline."""
    val = data.get(key, 0)
    value_str = _format_value(val, pct=pct, dollar=dollar, fmt_int=fmt_int)
    delta_str = None
    if baseline and key in baseline:
        diff = float(val) - float(baseline[key])  # type: ignore[arg-type]
        if abs(diff) > 0.01:
            delta_str = _format_value(
                diff, pct=pct, dollar=dollar, fmt_int=fmt_int, signed=True
            )
    st.metric(label=label, value=value_str, delta=delta_str)


def _format_value(
    val: float | str,
    pct: bool = False,
    dollar: bool = False,
    fmt_int: bool = False,
    signed: bool = False,
) -> str:
    """Format a numeric value for display."""
    if isinstance(val, str):
        return val
    prefix = "+" if signed and val > 0 else ""
    if pct:
        return f"{prefix}{val * 100:.1f}%" if abs(val) < 1.5 else f"{prefix}{val:.1f}%"
    if dollar:
        return f"{prefix}${val:,.0f}"
    if fmt_int:
        return f"{prefix}{val:,.0f}"
    return f"{prefix}{val:,.1f}"
