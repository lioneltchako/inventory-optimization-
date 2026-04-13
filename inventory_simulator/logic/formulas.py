"""Core inventory policy formulas.

All functions are pure (no side effects, no I/O). Parameters use daily time
units unless otherwise noted. Demand and lead-time distributions are assumed
independent and Normal.
"""

from __future__ import annotations

import math

from scipy.stats import norm  # type: ignore[import-untyped]


# ── Economic Order Quantity ───────────────────────────────────────────────────


def eoq(
    annual_demand: float,
    order_cost: float,
    holding_cost_per_unit: float,
) -> float:
    """Return the Economic Order Quantity (units).

    Args:
        annual_demand: Expected annual demand in units.
        order_cost: Fixed cost per replenishment order ($).
        holding_cost_per_unit: Annual holding cost per unit ($ / unit / year).

    Returns:
        Optimal order quantity Q* (units).  Returns 1.0 for degenerate inputs.
    """
    if annual_demand <= 0 or order_cost <= 0 or holding_cost_per_unit <= 0:
        return 1.0
    return math.sqrt(2.0 * annual_demand * order_cost / holding_cost_per_unit)


# ── Demand uncertainty over lead time ────────────────────────────────────────


def sigma_x_sQ(
    demand_mean: float,
    demand_std: float,
    lt_mean: float,
    lt_std: float,
) -> float:
    """Demand std dev over lead time for a continuous-review (s,Q) policy.

    Accounts for both demand variability and stochastic lead times via the
    compound variance formula:
        σ_x = sqrt(μ_L · σ_d² + σ_L² · μ_d²)

    Args:
        demand_mean: Mean daily demand (μ_d).
        demand_std: Std dev of daily demand (σ_d).
        lt_mean: Mean lead time in days (μ_L).
        lt_std: Std dev of lead time in days (σ_L).

    Returns:
        Combined demand standard deviation over the lead time.
    """
    variance = lt_mean * demand_std**2 + lt_std**2 * demand_mean**2
    return math.sqrt(max(variance, 0.0))


def sigma_x_RS(
    demand_mean: float,
    demand_std: float,
    lt_mean: float,
    lt_std: float,
    review_period: float,
) -> float:
    """Demand std dev over replenishment cycle for a periodic-review (R,S) policy.

    The exposure window is the review period R plus the lead time L:
        σ_x = sqrt((μ_L + R) · σ_d² + σ_L² · μ_d²)

    Args:
        demand_mean: Mean daily demand (μ_d).
        demand_std: Std dev of daily demand (σ_d).
        lt_mean: Mean lead time in days (μ_L).
        lt_std: Std dev of lead time in days (σ_L).
        review_period: Review interval R (days).

    Returns:
        Combined demand standard deviation over the replenishment cycle.
    """
    exposure = lt_mean + review_period
    variance = exposure * demand_std**2 + lt_std**2 * demand_mean**2
    return math.sqrt(max(variance, 0.0))


# ── Safety stock ──────────────────────────────────────────────────────────────


def safety_stock_sQ(
    z: float,
    demand_mean: float,
    demand_std: float,
    lt_mean: float,
    lt_std: float,
) -> float:
    """Safety stock for a continuous-review (s,Q) policy.

    Args:
        z: Service-level z-score (from ``z_from_csl``).
        demand_mean: Mean daily demand.
        demand_std: Std dev of daily demand.
        lt_mean: Mean lead time (days).
        lt_std: Std dev of lead time (days).

    Returns:
        Safety stock in units.
    """
    return z * sigma_x_sQ(demand_mean, demand_std, lt_mean, lt_std)


def safety_stock_RS(
    z: float,
    demand_mean: float,
    demand_std: float,
    lt_mean: float,
    lt_std: float,
    review_period: float,
) -> float:
    """Safety stock for a periodic-review (R,S) policy.

    Args:
        z: Service-level z-score.
        demand_mean: Mean daily demand.
        demand_std: Std dev of daily demand.
        lt_mean: Mean lead time (days).
        lt_std: Std dev of lead time (days).
        review_period: Review interval R (days).

    Returns:
        Safety stock in units.
    """
    return z * sigma_x_RS(demand_mean, demand_std, lt_mean, lt_std, review_period)


# ── Reorder point and order-up-to level ───────────────────────────────────────


def reorder_point(
    demand_mean: float,
    lt_mean: float,
    safety_stock: float,
) -> float:
    """Continuous-review reorder point (units).

    ROP = μ_d · μ_L + SS
    """
    return demand_mean * lt_mean + safety_stock


def order_up_to(
    demand_mean: float,
    lt_mean: float,
    review_period: float,
    safety_stock: float,
) -> float:
    """Periodic-review order-up-to level S (units).

    S = μ_d · (μ_L + R) + SS
    """
    return demand_mean * (lt_mean + review_period) + safety_stock


# ── Service level and fill rate ───────────────────────────────────────────────


def z_from_csl(csl: float) -> float:
    """Return the Normal z-score for a given Cycle Service Level probability."""
    return float(norm.ppf(max(min(csl, 0.9999), 0.5001)))


def csl_from_z(z: float) -> float:
    """Return the Cycle Service Level probability for a given z-score."""
    return float(norm.cdf(z))


def normal_loss(z: float) -> float:
    """Standard Normal Loss Function L(z) = φ(z) − z · (1 − Φ(z))."""
    return float(norm.pdf(z) - z * (1.0 - norm.cdf(z)))


def fill_rate(
    safety_stock: float,
    sigma_x: float,
    cycle_demand: float,
) -> float:
    """Type-II fill rate (fraction of demand met without backorder).

    β = 1 − (σ_x / Q) · L(z)

    Args:
        safety_stock: Safety stock in units.
        sigma_x: Demand std dev over lead time (or cycle).
        cycle_demand: Expected demand per replenishment cycle (Q for (s,Q),
            demand over R+L for (R,S)).

    Returns:
        Fill rate β in [0, 1].
    """
    if sigma_x <= 0 or cycle_demand <= 0:
        return 1.0
    z = safety_stock / sigma_x
    beta = 1.0 - (sigma_x / cycle_demand) * normal_loss(z)
    return max(0.0, min(beta, 1.0))


# ── Cost calculations ─────────────────────────────────────────────────────────


def annual_holding_cost(
    avg_inventory: float,
    unit_cost: float,
    holding_pct: float,
) -> float:
    """Annual holding cost ($)."""
    return avg_inventory * unit_cost * holding_pct


def annual_ordering_cost(
    annual_demand: float,
    order_qty: float,
    order_cost: float,
) -> float:
    """Annual ordering cost ($)."""
    if order_qty <= 0:
        return 0.0
    return (annual_demand / order_qty) * order_cost
