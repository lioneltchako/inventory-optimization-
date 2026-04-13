"""90-day discrete-event inventory stock trajectory simulator.

Simulates day-by-day inventory position under an (s,Q) continuous-review
policy with stochastic demand and lead times.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_stock_trajectory(
    avg_daily_demand: float,
    demand_std: float,
    lead_time_days: float,
    reorder_point: float,
    order_quantity: float,
    initial_stock: float | None = None,
    horizon: int = 90,
    seed: int = 42,
) -> pd.DataFrame:
    """Simulate daily inventory positions for a single SKU.

    Args:
        avg_daily_demand: Mean daily demand (units/day).
        demand_std: Std dev of daily demand (units/day).
        lead_time_days: Mean lead time (days).
        reorder_point: Inventory level that triggers a replenishment order.
        order_quantity: Fixed replenishment order size (EOQ or target).
        initial_stock: Starting stock level; defaults to ``reorder_point + order_quantity``.
        horizon: Simulation length in days (default 90).
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns:
            day, inventory, demand, order_placed, order_received, stockout.
    """
    rng = np.random.default_rng(seed)

    stock = (
        float(initial_stock)
        if initial_stock is not None
        else reorder_point + order_quantity
    )

    # List of (arrival_day, quantity) tuples for in-transit orders
    in_transit: list[tuple[int, float]] = []

    records: list[dict] = []

    for day in range(horizon):
        # Receive orders arriving today
        received_qty = 0.0
        still_in_transit: list[tuple[int, float]] = []
        for arr_day, qty in in_transit:
            if arr_day <= day:
                stock += qty
                received_qty += qty
            else:
                still_in_transit.append((arr_day, qty))
        in_transit = still_in_transit

        # Stochastic demand — clamped to non-negative
        demand = float(max(0.0, rng.normal(avg_daily_demand, demand_std)))

        # Consume inventory (backorders not modelled — stockout = lost)
        stockout = demand > stock
        consumed = min(demand, stock)
        stock -= consumed

        # Trigger replenishment when stock falls at or below ROP
        order_placed = stock <= reorder_point
        if order_placed:
            lt_sample = max(1.0, rng.normal(lead_time_days, lead_time_days * 0.20))
            arrival = day + int(round(lt_sample))
            in_transit.append((arrival, order_quantity))

        records.append(
            {
                "day": day,
                "inventory": round(stock, 2),
                "demand": round(demand, 2),
                "received": round(received_qty, 2),
                "order_placed": order_placed,
                "stockout": stockout,
            }
        )

    return pd.DataFrame(records)
