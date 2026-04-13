"""Plotly chart components for the Dynacraft Inventory Simulator."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from inventory_simulator.theme import COLOR_MAP, apply_theme


def demand_forecast_chart(
    demand_history: np.ndarray,
    forecast_weekly: np.ndarray,
    residuals: np.ndarray,
    current_rop_weekly: float,
    recommended_rop_weekly: float,
) -> go.Figure:
    """Demand history bars + forecast line with residual-based uncertainty."""
    fig = go.Figure()
    n_hist = len(demand_history)
    weeks_hist = list(range(1, n_hist + 1))

    fig.add_trace(
        go.Bar(
            x=weeks_hist,
            y=demand_history,
            name="Historical Demand",
            marker_color=COLOR_MAP["info"],
            opacity=0.5,
        )
    )

    n_fc = len(forecast_weekly)
    weeks_fc = list(range(n_hist + 1, n_hist + n_fc + 1))
    _add_uncertainty_bands(fig, weeks_fc, forecast_weekly, residuals)

    fig.add_trace(
        go.Scatter(
            x=weeks_fc,
            y=forecast_weekly,
            name="ML Forecast",
            line={"color": COLOR_MAP["recommended"], "width": 2},
        )
    )

    _add_rop_lines(fig, current_rop_weekly, recommended_rop_weekly)

    fig.update_layout(
        title="Demand History & ML Forecast",
        xaxis_title="Week",
        yaxis_title="Units / Week",
        barmode="overlay",
    )
    return apply_theme(fig)


def _add_uncertainty_bands(
    fig: go.Figure,
    weeks: list[int],
    forecast: np.ndarray,
    residuals: np.ndarray,
) -> None:
    """Add percentile-based forecast uncertainty bands."""
    p2_5 = float(np.percentile(residuals, 2.5))
    p16 = float(np.percentile(residuals, 16))
    p84 = float(np.percentile(residuals, 84))
    p97_5 = float(np.percentile(residuals, 97.5))

    fig.add_trace(
        go.Scatter(
            x=weeks + weeks[::-1],
            y=list(forecast + p97_5) + list((forecast + p2_5)[::-1]),
            fill="toself",
            fillcolor="rgba(142,68,173,0.1)",
            line={"width": 0},
            name="Forecast uncertainty (from model residuals) 95%",
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weeks + weeks[::-1],
            y=list(forecast + p84) + list((forecast + p16)[::-1]),
            fill="toself",
            fillcolor="rgba(142,68,173,0.2)",
            line={"width": 0},
            name="Forecast uncertainty (from model residuals) 68%",
            showlegend=True,
        )
    )


def _add_rop_lines(
    fig: go.Figure,
    current_rop: float,
    recommended_rop: float,
) -> None:
    """Add ROP reference lines."""
    fig.add_hline(
        y=current_rop,
        line_dash="dash",
        line_color=COLOR_MAP["current"],
        annotation_text="Current ROP",
    )
    fig.add_hline(
        y=recommended_rop,
        line_color=COLOR_MAP["recommended"],
        annotation_text="Recommended ROP",
    )


def inventory_simulation_chart(
    sim_levels: np.ndarray,
    stockout_weeks: np.ndarray,
    rop_level: float,
) -> go.Figure:
    """Simulated 52-week inventory trajectory with stockout markers."""
    fig = go.Figure()
    weeks = list(range(1, len(sim_levels) + 1))

    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=sim_levels,
            name="Inventory Level",
            line={"color": COLOR_MAP["info"], "width": 2},
            fill="tozeroy",
            fillcolor="rgba(41,128,185,0.1)",
        )
    )

    if len(stockout_weeks) > 0:
        fig.add_trace(
            go.Scatter(
                x=stockout_weeks.tolist(),
                y=[0] * len(stockout_weeks),
                mode="markers",
                name="Stockout Event",
                marker={"color": COLOR_MAP["critical"], "size": 10, "symbol": "x"},
            )
        )

    fig.add_hline(
        y=rop_level,
        line_dash="dash",
        line_color=COLOR_MAP["at_risk"],
        annotation_text="Reorder Point",
    )
    fig.update_layout(
        title="Simulated Inventory Trajectory (52 weeks)",
        xaxis_title="Week",
        yaxis_title="Units on Hand",
    )
    return apply_theme(fig)


def cost_breakdown_bar(
    holding: float,
    ordering: float,
    stockout: float,
    title: str = "Annual Cost Breakdown",
) -> go.Figure:
    """Stacked bar chart of cost components."""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=["Cost"],
            y=[holding],
            name="Holding",
            marker_color=COLOR_MAP["holding_cost"],
        )
    )
    fig.add_trace(
        go.Bar(
            x=["Cost"],
            y=[ordering],
            name="Ordering",
            marker_color=COLOR_MAP["ordering_cost"],
        )
    )
    fig.add_trace(
        go.Bar(
            x=["Cost"],
            y=[stockout],
            name="Stockout",
            marker_color=COLOR_MAP["stockout_cost"],
        )
    )
    fig.update_layout(barmode="stack", title=title, yaxis_title="$ / Year")
    return apply_theme(fig)


def frontier_chart(
    service_levels: list[float],
    costs: list[float],
    baseline_sl: float,
    baseline_cost: float,
    selected_sl: float | None = None,
    selected_cost: float | None = None,
) -> go.Figure:
    """Service level vs total annual cost frontier curve."""
    fig = go.Figure()
    sl_pct = [s * 100 for s in service_levels]

    fig.add_trace(
        go.Scatter(
            x=sl_pct,
            y=costs,
            name="Cost Frontier",
            line={"color": COLOR_MAP["info"], "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[baseline_sl * 100],
            y=[baseline_cost],
            mode="markers+text",
            name="Baseline (95%)",
            marker={"color": COLOR_MAP["current"], "size": 12},
            text=["Baseline"],
            textposition="top right",
        )
    )

    if selected_sl is not None and selected_cost is not None:
        delta = selected_cost - baseline_cost
        delta_text = f"{'+' if delta >= 0 else ''}${delta:,.0f}"
        fig.add_trace(
            go.Scatter(
                x=[selected_sl * 100],
                y=[selected_cost],
                mode="markers+text",
                name="Selected",
                marker={"color": COLOR_MAP["recommended"], "size": 12},
                text=[delta_text],
                textposition="top left",
            )
        )

    fig.update_layout(
        title="Cost vs Service Level Frontier",
        xaxis_title="Service Level (%)",
        yaxis_title="Annual Total Cost ($)",
    )
    return apply_theme(fig)


def ss_vs_service_chart(
    service_levels: list[float],
    ss_values: list[float],
) -> go.Figure:
    """Safety stock units vs service level chart."""
    fig = go.Figure()
    sl_pct = [s * 100 for s in service_levels]

    fig.add_trace(
        go.Scatter(
            x=sl_pct,
            y=ss_values,
            name="Safety Stock",
            line={"color": COLOR_MAP["forecast_band"], "width": 2},
            fill="tozeroy",
            fillcolor="rgba(142,68,173,0.1)",
        )
    )
    fig.update_layout(
        title="Safety Stock vs Service Level",
        xaxis_title="Service Level (%)",
        yaxis_title="Safety Stock (units)",
    )
    return apply_theme(fig)
