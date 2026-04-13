"""Data contracts between Phase 1 (forecast) and Phase 2 (inventory policy).

SKUForecastResult combines Phase 1 forecast outputs with inventory metadata.
Phase 2 computes all policy outputs (SS, ROP, EOQ, costs) at runtime.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import numpy.typing as npt


@dataclasses.dataclass
class SKUForecastResult:
    """Single SKU's Phase 1 outputs plus ERP/business context.

    Phase 1 provides: sku_id, category, forecast, residuals,
    demand_history, avg_weekly_demand, model_mae, model_bias.

    Phase 2 adds: lead_time_days, review_period_days, unit_cost,
    holding_cost_rate, stockout_cost_per_unit.

    Phase 2 COMPUTES at startup: safety stock, ROP, fill rate,
    EOQ, costs — these are NOT stored here.
    """

    sku_id: str
    category: str
    forecast: npt.NDArray[np.float64]
    residuals: npt.NDArray[np.float64]
    demand_history: npt.NDArray[np.float64]
    avg_weekly_demand: float
    model_mae: float
    model_bias: float
    lead_time_days: int
    review_period_days: int
    unit_cost: float
    holding_cost_rate: float
    stockout_cost_per_unit: float


@dataclasses.dataclass
class PolicyResult:
    """Computed inventory policy for a single SKU at a given service level."""

    sku_id: str
    service_level: float
    safety_stock: float
    reorder_point: float
    eoq: float
    holding_cost: float
    ordering_cost: float
    stockout_cost: float
    total_annual_cost: float
    ss_days_of_cover: float
    fill_rate_status: str


@dataclasses.dataclass
class ScenarioData:
    """A named scenario with its parameter overrides and policy results."""

    name: str
    service_level: float
    lead_time_days: int
    review_period_days: int
    holding_cost_rate: float
    demand_multiplier: float
    policies: dict[str, PolicyResult]


@dataclasses.dataclass
class PrecomputedData:
    """All precomputed data for the app, cached at startup."""

    sku_outputs: dict[str, SKUForecastResult]
    baseline_policies: dict[str, PolicyResult]
    ss_grid: dict[str, dict[float, PolicyResult]]
    classical_ss: dict[str, float]
    classical_ss_cost: dict[str, float]
    scenario_b_policies: dict[str, PolicyResult]
    stockout_risk_scores: dict[str, float]
