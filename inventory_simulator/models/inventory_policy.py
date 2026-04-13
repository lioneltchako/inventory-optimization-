"""Inventory policy calculations using ML forecast-error based safety stock.

Safety stock covers only what the ML model could not predict — the residual
uncertainty. Using raw demand variability would double-count trend and
seasonality that the model already explains, inflating stock unnecessarily.
This is the key insight from Phase 1: the forecast residuals (not raw demand
noise) are the correct input for sizing safety stock.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def compute_safety_stock(
    residuals: np.ndarray,
    lead_time_days: int,
    review_period_days: int,
    service_level: float,
) -> float:
    """SS(alpha) = Z(alpha) * sigma_residuals * sqrt(risk_horizon_weeks).

    All residuals are in weekly units.
    """
    z_alpha = norm.ppf(service_level)
    sigma_residuals = float(np.std(residuals))
    risk_horizon_weeks = (lead_time_days + review_period_days) / 7.0
    return float(z_alpha * sigma_residuals * np.sqrt(risk_horizon_weeks))


def compute_classical_safety_stock(
    demand_history: np.ndarray,
    lead_time_days: int,
    review_period_days: int,
    service_level: float,
) -> float:
    """Classical SS using raw demand variability (for comparison only)."""
    z_alpha = norm.ppf(service_level)
    sigma_demand = float(np.std(demand_history))
    risk_horizon_weeks = (lead_time_days + review_period_days) / 7.0
    return float(z_alpha * sigma_demand * np.sqrt(risk_horizon_weeks))


def compute_reorder_point(
    avg_weekly_demand: float,
    lead_time_days: int,
    review_period_days: int,
    safety_stock: float,
) -> float:
    """ROP = forecast_demand_over_risk_horizon + SS."""
    risk_horizon_weeks = (lead_time_days + review_period_days) / 7.0
    forecast_demand = avg_weekly_demand * risk_horizon_weeks
    return forecast_demand + safety_stock


def compute_eoq(
    avg_weekly_demand: float,
    unit_cost: float,
    holding_cost_rate: float,
    ordering_cost: float = 50.0,
) -> float:
    """EOQ = sqrt(2 * D * K / h)."""
    annual_demand = avg_weekly_demand * 52.0
    h = unit_cost * holding_cost_rate
    if h <= 0:
        return annual_demand / 12.0
    return float(np.sqrt(2.0 * annual_demand * ordering_cost / h))


def compute_fill_rate_status(service_level: float) -> str:
    """Classify fill rate status relative to 95% target."""
    if service_level >= 0.95:
        return "healthy"
    if service_level >= 0.90:
        return "at_risk"
    return "critical"
