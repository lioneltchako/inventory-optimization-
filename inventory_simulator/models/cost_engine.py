"""Cost engine for inventory policy total annual cost model.

Total Annual Cost = Holding Cost + Ordering Cost + Stockout Cost

Holding Cost  = (SS + EOQ/2) * unit_cost * holding_cost_rate
Ordering Cost = (D / EOQ) * K
Stockout Cost = (D / EOQ) * expected_units_short * stockout_cost_per_unit

Where expected_units_short per cycle = sigma * sqrt(risk_horizon) * L(z),
and L(z) = phi(z) - z*(1 - Phi(z)) is the standard normal loss function.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def standard_normal_loss(z: float) -> float:
    """L(z) = phi(z) - z * (1 - Phi(z))."""
    return float(norm.pdf(z) - z * (1.0 - norm.cdf(z)))


def compute_holding_cost(
    safety_stock: float,
    eoq: float,
    unit_cost: float,
    holding_cost_rate: float,
) -> float:
    """Annual holding cost = (SS + EOQ/2) * unit_cost * holding_rate."""
    return (safety_stock + eoq / 2.0) * unit_cost * holding_cost_rate


def compute_ordering_cost(
    avg_weekly_demand: float,
    eoq: float,
    ordering_cost_per_order: float = 50.0,
) -> float:
    """Annual ordering cost = (D / EOQ) * K."""
    annual_demand = avg_weekly_demand * 52.0
    if eoq <= 0:
        return 0.0
    return (annual_demand / eoq) * ordering_cost_per_order


def compute_stockout_cost(
    avg_weekly_demand: float,
    eoq: float,
    residuals: np.ndarray,
    lead_time_days: int,
    review_period_days: int,
    service_level: float,
    stockout_cost_per_unit: float,
) -> float:
    """Annual stockout cost using the standard normal loss function."""
    annual_demand = avg_weekly_demand * 52.0
    if eoq <= 0:
        return 0.0
    z = norm.ppf(service_level)
    sigma = float(np.std(residuals))
    risk_horizon_weeks = (lead_time_days + review_period_days) / 7.0
    eus = sigma * np.sqrt(risk_horizon_weeks) * standard_normal_loss(z)
    return float((annual_demand / eoq) * eus * stockout_cost_per_unit)


def compute_total_annual_cost(
    safety_stock: float,
    eoq: float,
    unit_cost: float,
    holding_cost_rate: float,
    avg_weekly_demand: float,
    residuals: np.ndarray,
    lead_time_days: int,
    review_period_days: int,
    service_level: float,
    stockout_cost_per_unit: float,
) -> tuple[float, float, float, float]:
    """Return (total, holding, ordering, stockout) annual costs."""
    holding = compute_holding_cost(safety_stock, eoq, unit_cost, holding_cost_rate)
    ordering = compute_ordering_cost(avg_weekly_demand, eoq)
    stockout = compute_stockout_cost(
        avg_weekly_demand,
        eoq,
        residuals,
        lead_time_days,
        review_period_days,
        service_level,
        stockout_cost_per_unit,
    )
    return (holding + ordering + stockout, holding, ordering, stockout)
