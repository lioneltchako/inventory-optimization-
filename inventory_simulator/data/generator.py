"""Synthetic 120-SKU PACCAR heavy-duty truck parts portfolio.

Parameters reflect realistic distribution patterns for heavy-duty truck
aftermarket parts. All values are synthetic; they do not represent actual
PACCAR or DynaCraft operational data.

The module-level constants PORTFOLIO (DataFrame) and PORTFOLIO_SUMMARY (dict)
are generated once at import time using a fixed random seed for reproducibility.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from inventory_simulator.logic.formulas import (
    eoq,
    fill_rate,
    reorder_point,
    sigma_x_sQ,
    z_from_csl,
)

_RNG = np.random.default_rng(42)

# ── Category parameter profiles ───────────────────────────────────────────────
# Each entry defines the distribution of SKU parameters within a category.

_CATEGORY_PARAMS: dict[str, dict] = {
    "Engine": {
        "n": 24,
        "cost_lo": 45.0,
        "cost_hi": 650.0,
        "demand_lo": 0.6,
        "demand_hi": 14.0,
        "cv_lo": 0.20,
        "cv_hi": 0.50,
        "lt_lo": 7.0,
        "lt_hi": 21.0,
        "lt_cv": 0.22,
    },
    "Transmission": {
        "n": 24,
        "cost_lo": 350.0,
        "cost_hi": 4000.0,
        "demand_lo": 0.06,
        "demand_hi": 3.5,
        "cv_lo": 0.35,
        "cv_hi": 0.80,
        "lt_lo": 14.0,
        "lt_hi": 45.0,
        "lt_cv": 0.35,
    },
    "Axle": {
        "n": 24,
        "cost_lo": 28.0,
        "cost_hi": 480.0,
        "demand_lo": 1.2,
        "demand_hi": 20.0,
        "cv_lo": 0.15,
        "cv_hi": 0.40,
        "lt_lo": 5.0,
        "lt_hi": 14.0,
        "lt_cv": 0.18,
    },
    "Brake": {
        "n": 24,
        "cost_lo": 18.0,
        "cost_hi": 280.0,
        "demand_lo": 2.5,
        "demand_hi": 28.0,
        "cv_lo": 0.15,
        "cv_hi": 0.35,
        "lt_lo": 3.0,
        "lt_hi": 10.0,
        "lt_cv": 0.15,
    },
    "Electrical": {
        "n": 24,
        "cost_lo": 90.0,
        "cost_hi": 2800.0,
        "demand_lo": 0.10,
        "demand_hi": 6.0,
        "cv_lo": 0.45,
        "cv_hi": 0.90,
        "lt_lo": 14.0,
        "lt_hi": 60.0,
        "lt_cv": 0.40,
    },
}

_TARGET_CSL: float = 0.97  # cycle service level for optimal policy
_HOLDING_PCT: float = 0.25  # annual holding cost fraction of unit value
_ORDER_COST: float = 85.0  # fixed replenishment cost per order ($)
_REVIEW_PERIOD: int = 7  # review interval for (R,S) policy (days)

# Status-quo overstock multiplier: current SS is 2–6× the optimal level,
# reflecting the cost of using static min/max buffers without demand-signal feedback.
_OVERSTOCK_LO: float = 2.0
_OVERSTOCK_HI: float = 6.0


def _assign_criticality(spend: float, p30: float, p80: float) -> str:
    """Map annual spend to a criticality tier.

    Args:
        spend: SKU annual spend proxy (annual_demand × unit_cost).
        p30: 30th-percentile threshold for Standard / Operational boundary.
        p80: 80th-percentile threshold for Operational / Critical boundary.

    Returns:
        "Critical", "Operational", or "Standard".
    """
    if spend >= p80:
        return "Critical"
    if spend >= p30:
        return "Operational"
    return "Standard"


def _generate_skus() -> pd.DataFrame:
    """Generate the 120-SKU synthetic portfolio DataFrame."""
    z_target = z_from_csl(_TARGET_CSL)
    rows: list[dict] = []
    sku_idx = 1

    for cat, p in _CATEGORY_PARAMS.items():
        n: int = p["n"]
        costs = _RNG.uniform(p["cost_lo"], p["cost_hi"], size=n)
        demands = _RNG.uniform(p["demand_lo"], p["demand_hi"], size=n)
        cvs = _RNG.uniform(p["cv_lo"], p["cv_hi"], size=n)
        lts = _RNG.uniform(p["lt_lo"], p["lt_hi"], size=n)

        for i in range(n):
            d_mean: float = float(demands[i])
            d_std: float = d_mean * float(cvs[i])
            lt_mean: float = float(lts[i])
            lt_std: float = lt_mean * float(p["lt_cv"])
            cost: float = float(costs[i])

            # Optimal safety stock at target CSL
            sx = sigma_x_sQ(d_mean, d_std, lt_mean, lt_std)
            ss_opt_units: float = z_target * sx
            ss_opt_value: float = ss_opt_units * cost

            # EOQ for replenishment cycle
            annual_demand: float = d_mean * 365.0
            holding_unit: float = cost * _HOLDING_PCT
            q_eoq: float = eoq(annual_demand, _ORDER_COST, holding_unit)

            # Reorder point
            rop: float = reorder_point(d_mean, lt_mean, ss_opt_units)

            # Fill rate at optimal SS
            fr: float = fill_rate(ss_opt_units, sx, max(q_eoq, 1.0))

            # Current (status-quo) safety stock — over-stocked by overstock factor
            overstock_factor: float = float(_RNG.uniform(_OVERSTOCK_LO, _OVERSTOCK_HI))
            current_ss_units: float = ss_opt_units * overstock_factor
            current_ss_days: float = current_ss_units / max(d_mean, 0.001)
            current_ss_value: float = current_ss_units * cost

            # Annual holding-cost saving from right-sizing
            annual_saving: float = (current_ss_value - ss_opt_value) * _HOLDING_PCT

            rows.append(
                {
                    "sku_id": f"SKU-{sku_idx:03d}",
                    "category": cat,
                    "avg_daily_demand": round(d_mean, 3),
                    "demand_std": round(d_std, 3),
                    "lead_time_days": round(lt_mean, 1),
                    "lead_time_std": round(lt_std, 2),
                    "unit_cost": round(cost, 2),
                    "holding_cost_pct": _HOLDING_PCT,
                    "order_cost": _ORDER_COST,
                    "annual_demand": round(annual_demand, 1),
                    "eoq_units": round(q_eoq, 1),
                    "reorder_point": round(rop, 1),
                    "current_safety_stock_units": round(current_ss_units, 1),
                    "current_safety_stock_days": round(current_ss_days, 1),
                    "current_ss_value": round(current_ss_value, 2),
                    "optimal_safety_stock_units": round(ss_opt_units, 1),
                    "optimal_ss_value": round(ss_opt_value, 2),
                    "target_csl": _TARGET_CSL,
                    "fill_rate": round(min(fr, 0.9999), 4),
                    "annual_saving": round(annual_saving, 2),
                    "sigma_x": round(sx, 3),
                    "cv": round(float(cvs[i]), 4),
                    "overstock_factor": round(overstock_factor, 2),
                }
            )
            sku_idx += 1

    df = pd.DataFrame(rows)

    # Annual spend proxy drives criticality segmentation
    df["annual_spend"] = df["annual_demand"] * df["unit_cost"]
    thresholds = df["annual_spend"].quantile([0.30, 0.80])
    p30: float = float(thresholds[0.30])
    p80: float = float(thresholds[0.80])
    df["criticality"] = df["annual_spend"].apply(
        lambda s: _assign_criticality(float(s), p30, p80)  # type: ignore[arg-type]
    )

    return df.reset_index(drop=True)


# ── Module-level singletons ───────────────────────────────────────────────────

PORTFOLIO: pd.DataFrame = _generate_skus()

PORTFOLIO_SUMMARY: dict[str, float | int] = {
    "total_current_ss_value": float(PORTFOLIO["current_ss_value"].sum()),
    "total_optimal_ss_value": float(PORTFOLIO["optimal_ss_value"].sum()),
    "total_annual_saving": float(PORTFOLIO["annual_saving"].sum()),
    "avg_fill_rate": float(PORTFOLIO["fill_rate"].mean()),
    "avg_target_csl": float(_TARGET_CSL),
    "n_critical": int((PORTFOLIO["criticality"] == "Critical").sum()),
    "n_operational": int((PORTFOLIO["criticality"] == "Operational").sum()),
    "n_standard": int((PORTFOLIO["criticality"] == "Standard").sum()),
    "total_skus": int(len(PORTFOLIO)),
}
