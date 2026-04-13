"""Centralized theming for the Dynacraft Inventory Simulator.

All color definitions and Plotly layout defaults live here.
No hardcoded hex values should appear outside this module.
"""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

COLOR_MAP: dict[str, str] = {
    "healthy": "#2ECC71",
    "at_risk": "#F39C12",
    "critical": "#E74C3C",
    "info": "#2980B9",
    "forecast_band": "#8E44AD",
    "recommended": "#1ABC9C",
    "current": "#95A5A6",
    "background": "#FFFFFF",
    "sidebar": "#1B2A4A",
    "text": "#2C3E50",
    "holding_cost": "#3498DB",
    "ordering_cost": "#E67E22",
    "stockout_cost": "#E74C3C",
}

PLOTLY_LAYOUT_DEFAULTS: dict[str, Any] = {
    "font": {"family": "Inter, Arial, sans-serif", "color": COLOR_MAP["text"]},
    "paper_bgcolor": COLOR_MAP["background"],
    "plot_bgcolor": COLOR_MAP["background"],
    "margin": {"l": 50, "r": 30, "t": 50, "b": 40},
    "legend": {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "right",
        "x": 1,
    },
    "hovermode": "x unified",
}


def apply_theme(fig: go.Figure) -> go.Figure:
    """Apply consistent Dynacraft theming to any Plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS)
    fig.update_xaxes(gridcolor="#ECF0F1", gridwidth=1, zeroline=False)
    fig.update_yaxes(gridcolor="#ECF0F1", gridwidth=1, zeroline=False)
    return fig
