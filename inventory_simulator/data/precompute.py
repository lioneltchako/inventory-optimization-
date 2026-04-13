"""Precomputation module — cached at startup for responsive UI.

Computes baseline policies, SS grids, frontier curves, classical SS
comparison, Scenario B, and portfolio health metrics.
"""

from __future__ import annotations

import numpy as np

from inventory_simulator.data.contracts import (
    PolicyResult,
    PrecomputedData,
    SKUForecastResult,
)
from inventory_simulator.models.cost_engine import compute_total_annual_cost
from inventory_simulator.models.inventory_policy import (
    compute_classical_safety_stock,
    compute_eoq,
    compute_fill_rate_status,
    compute_reorder_point,
    compute_safety_stock,
)

SERVICE_LEVELS: list[float] = [round(0.85 + i * 0.01, 2) for i in range(15)]


def _compute_policy(
    sku: SKUForecastResult,
    service_level: float,
    lead_time_override: int | None = None,
    review_override: int | None = None,
    holding_rate_override: float | None = None,
    demand_multiplier: float = 1.0,
) -> PolicyResult:
    """Compute full policy for a single SKU at a given service level."""
    lt = lead_time_override if lead_time_override is not None else sku.lead_time_days
    rp = review_override if review_override is not None else sku.review_period_days
    hr = (
        holding_rate_override
        if holding_rate_override is not None
        else sku.holding_cost_rate
    )
    awd = sku.avg_weekly_demand * demand_multiplier

    ss = compute_safety_stock(sku.residuals, lt, rp, service_level)
    rop = compute_reorder_point(awd, lt, rp, ss)
    eoq = compute_eoq(awd, sku.unit_cost, hr)

    total, holding, ordering, stockout = compute_total_annual_cost(
        ss,
        eoq,
        sku.unit_cost,
        hr,
        awd,
        sku.residuals,
        lt,
        rp,
        service_level,
        sku.stockout_cost_per_unit,
    )
    avg_daily = awd / 7.0
    days_cover = ss / avg_daily if avg_daily > 0 else 0.0
    status = compute_fill_rate_status(service_level)

    return PolicyResult(
        sku_id=sku.sku_id,
        service_level=service_level,
        safety_stock=ss,
        reorder_point=rop,
        eoq=eoq,
        holding_cost=holding,
        ordering_cost=ordering,
        stockout_cost=stockout,
        total_annual_cost=total,
        ss_days_of_cover=days_cover,
        fill_rate_status=status,
    )


def _compute_stockout_risk_score(sku: SKUForecastResult, policy: PolicyResult) -> float:
    """Score 0-100: higher = worse stockout risk."""
    cv = float(np.std(sku.residuals)) / max(sku.avg_weekly_demand, 1.0)
    sl_gap = max(0.0, 0.95 - policy.service_level)
    raw_score = (cv * 50.0) + (sl_gap * 500.0)
    return min(100.0, max(0.0, raw_score))


def precompute_all(outputs: dict[str, SKUForecastResult]) -> PrecomputedData:
    """Precompute all policy data for the app. Cache with st.cache_data."""
    baseline_policies: dict[str, PolicyResult] = {}
    ss_grid: dict[str, dict[float, PolicyResult]] = {}
    classical_ss: dict[str, float] = {}
    classical_ss_cost: dict[str, float] = {}
    scenario_b_policies: dict[str, PolicyResult] = {}
    stockout_risk_scores: dict[str, float] = {}

    for sku_id, sku in outputs.items():
        baseline = _compute_policy(sku, 0.95)
        baseline_policies[sku_id] = baseline

        grid: dict[float, PolicyResult] = {}
        for sl in SERVICE_LEVELS:
            grid[sl] = _compute_policy(sku, sl)
        ss_grid[sku_id] = grid

        classical = compute_classical_safety_stock(
            sku.demand_history,
            sku.lead_time_days,
            sku.review_period_days,
            0.95,
        )
        classical_ss[sku_id] = classical
        classical_holding = (
            (classical + baseline.eoq / 2.0) * sku.unit_cost * sku.holding_cost_rate
        )
        classical_ss_cost[sku_id] = classical_holding

        scenario_b_policies[sku_id] = _compute_policy(
            sku,
            0.95,
            lead_time_override=sku.lead_time_days + 14,
        )
        stockout_risk_scores[sku_id] = _compute_stockout_risk_score(sku, baseline)

    return PrecomputedData(
        sku_outputs=outputs,
        baseline_policies=baseline_policies,
        ss_grid=ss_grid,
        classical_ss=classical_ss,
        classical_ss_cost=classical_ss_cost,
        scenario_b_policies=scenario_b_policies,
        stockout_risk_scores=stockout_risk_scores,
    )
