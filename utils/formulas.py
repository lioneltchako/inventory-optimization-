"""
Inventory optimization formulas.
Methodology: Vandeput (2020) "Inventory Optimization: Models and Simulations"
All functions are formula-only — no simulation loops.
"""

import math
import numpy as np
from scipy.stats import norm

# ── Service level z-scores ───────────────────────────────────────────────────
Z_90 = 1.282
Z_95 = 1.645
Z_975 = 1.960
Z_99 = 2.326
Z_999 = 3.090

WEEKS_PER_YEAR = 52


def eoq(annual_demand: float, order_cost: float, holding_cost_per_unit: float) -> float:
    """
    Economic Order Quantity — optimal order size to minimize total cost.
    [Vandeput Ch. 2, eq. 2.2]

    Q* = sqrt(2 × D × S / h)
      D = annual demand (units/year)
      S = ordering cost per order ($)
      h = holding cost per unit per year ($/unit/year)
    """
    if holding_cost_per_unit <= 0:
        return 0.0
    return math.sqrt(2.0 * annual_demand * order_cost / holding_cost_per_unit)


def sigma_x_sQ(
    demand_mean: float,
    demand_std: float,
    lt_mean: float,
    lt_std: float,
) -> float:
    """
    Demand uncertainty over the replenishment lead time for (s,Q) policy.
    [Vandeput Ch. 6, eq. 6.4]

    σx = sqrt(μL × σd² + σL² × μd²)
    Both demand variability AND lead time variability contribute.
    """
    return math.sqrt(lt_mean * demand_std**2 + lt_std**2 * demand_mean**2)


def sigma_x_RS(
    demand_mean: float,
    demand_std: float,
    lt_mean: float,
    lt_std: float,
    review_period: int,
) -> float:
    """
    Demand uncertainty over review + lead time for (R,S) policy.
    [Vandeput Ch. 6, eq. 6.5]

    σx = sqrt((μL + R) × σd² + σL² × μd²)
    The review period R adds a 'blind spot' — you can't react between reviews.
    """
    return math.sqrt(
        (lt_mean + review_period) * demand_std**2 + lt_std**2 * demand_mean**2
    )


def safety_stock_sQ(
    z: float,
    demand_mean: float,
    demand_std: float,
    lt_mean: float,
    lt_std: float,
) -> float:
    """
    Safety stock for (s,Q) continuous review policy with stochastic lead time.
    [Vandeput Ch. 6, eq. 6.4]

    SS = Z × σx    where σx = sqrt(μL × σd² + σL² × μd²)
    """
    sx = sigma_x_sQ(demand_mean, demand_std, lt_mean, lt_std)
    return z * sx


def safety_stock_RS(
    z: float,
    demand_mean: float,
    demand_std: float,
    lt_mean: float,
    lt_std: float,
    review_period: int,
) -> float:
    """
    Safety stock for (R,S) periodic review policy with stochastic lead time.
    [Vandeput Ch. 6, eq. 6.5]

    SS = Z × σx    where σx = sqrt((μL + R) × σd² + σL² × μd²)
    """
    sx = sigma_x_RS(demand_mean, demand_std, lt_mean, lt_std, review_period)
    return z * sx


def reorder_point(demand_mean: float, lt_mean: float, safety_stock: float) -> float:
    """
    Reorder point (order trigger level) for (s,Q) policy.
    [Vandeput Ch. 5, Section 5.1]

    ROP = μd × μL + SS
    "Order when on-hand inventory falls to this level."
    """
    return demand_mean * lt_mean + safety_stock


def order_up_to(
    demand_mean: float,
    lt_mean: float,
    review_period: int,
    safety_stock: float,
) -> float:
    """
    Order-up-to level S for (R,S) periodic review policy.
    [Vandeput Ch. 5]

    S = μd × (μL + R) + SS
    "Top up to this level at every review."
    """
    return demand_mean * (lt_mean + review_period) + safety_stock


def normal_loss(z: float) -> float:
    """
    Standard normal loss function — expected units short per unit of σx.
    [Vandeput Ch. 7, eq. 7.1]

    L(z) = φ(z) − z × (1 − Φ(z))
      φ = standard normal PDF
      Φ = standard normal CDF
    """
    return norm.pdf(z) - z * (1.0 - norm.cdf(z))


def fill_rate(safety_stock: float, sigma_x: float, cycle_demand: float) -> float:
    """
    Fill rate β — proportion of demand served directly from stock.
    [Vandeput Ch. 7, eq. 7.3]

    β = 1 − (σx / dc) × L(z)
      dc = cycle demand (demand per order cycle)
      z  = SS / σx
    """
    if sigma_x <= 0 or cycle_demand <= 0:
        return 1.0
    z = safety_stock / sigma_x if sigma_x > 0 else 0.0
    ln_z = normal_loss(z)
    beta = 1.0 - (sigma_x / cycle_demand) * ln_z
    return min(max(beta, 0.0), 1.0)


def csl_from_z(z: float) -> float:
    """Cycle service level from z-score. CSL = Φ(z)."""
    return float(norm.cdf(z))


def z_from_csl(csl: float) -> float:
    """Z-score from cycle service level target."""
    return float(norm.ppf(csl))


def annual_holding_cost(
    avg_inventory: float, unit_cost: float, holding_pct: float
) -> float:
    """
    Annual holding cost = avg inventory × unit cost × holding rate.
    avg_inventory typically = SS + EOQ/2.
    """
    return avg_inventory * unit_cost * holding_pct


def annual_ordering_cost(
    annual_demand: float, eoq_qty: float, order_cost: float
) -> float:
    """
    Annual ordering cost = (annual demand / EOQ) × cost per order.
    """
    if eoq_qty <= 0:
        return 0.0
    return (annual_demand / eoq_qty) * order_cost


def demo_inventory_path(
    demand_mean: float,
    demand_std: float,
    rop: float,
    order_qty: float,
    lead_time: float,
    weeks: int = 52,
    seed: int = 42,
) -> dict:
    """
    Lightweight (s,Q) inventory simulation for demo visualization.
    NOT a full Monte Carlo engine — single path, integer-week lead times.
    Returns weeks, inventory levels, order events, stockout flags.
    """
    rng = np.random.default_rng(seed)
    lt_int = max(1, int(round(lead_time)))

    inventory = float(rop + order_qty * 0.5)  # start comfortably above ROP
    on_order: list[tuple[int, float]] = []  # (arrival_week, qty)

    inv_levels: list[float] = []
    stockout_weeks: list[int] = []

    for week in range(weeks):
        # Arrive pending orders
        arrived = [qty for (arr, qty) in on_order if arr == week]
        for qty in arrived:
            inventory += qty
        on_order = [(arr, qty) for (arr, qty) in on_order if arr != week]

        # Simulate demand
        demand = max(0.0, rng.normal(demand_mean, demand_std))
        inventory -= demand

        if inventory < 0:
            stockout_weeks.append(week)
            inventory = 0.0

        inv_levels.append(inventory)

        # Trigger reorder if inventory position below ROP
        inventory_position = inventory + sum(qty for (_, qty) in on_order)
        if inventory_position <= rop:
            on_order.append((week + lt_int, order_qty))

    return {
        "weeks": list(range(weeks)),
        "inventory": inv_levels,
        "rop": rop,
        "safety_stock": rop - demand_mean * lead_time,
        "stockout_weeks": stockout_weeks,
    }
