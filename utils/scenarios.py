"""
Six pre-built PACCAR SKU profiles for the demo.
Each profile is a "character" in the demo story — contrasts are deliberate
and educational. Parameters are synthetic PACCAR-like estimates (~).
"""

from typing import Any

SCENARIOS: dict[str, dict[str, Any]] = {
    "Powertrain — Oil Filter": {
        "tagline": "High-volume, stable demand. The textbook easy win.",
        "family": "Powertrain",
        "demand_pattern": "Stable",
        "weekly_demand_mean": 850,
        "weekly_demand_cv": 0.15,
        "lead_time_mean_weeks": 3,
        "lead_time_std_weeks": 0.5,
        "unit_cost": 12,
        "holding_cost_pct": 0.25,
        "order_cost": 300,
        "backlog_cost_unit_week": 5,
        "review_period_weeks": 0,  # 0 = (s,Q) continuous review
        "recommended_policy": "(s,Q)",
    },
    "Chassis — Brake Pad Set": {
        "tagline": "Moderate volatility. Classic batched periodic ordering.",
        "family": "Chassis",
        "demand_pattern": "Volatile",
        "weekly_demand_mean": 420,
        "weekly_demand_cv": 0.30,
        "lead_time_mean_weeks": 5,
        "lead_time_std_weeks": 1.0,
        "unit_cost": 45,
        "holding_cost_pct": 0.25,
        "order_cost": 500,
        "backlog_cost_unit_week": 15,
        "review_period_weeks": 1,
        "recommended_policy": "(R,S)",
    },
    "Electrical — ECU Sensor": {
        "tagline": "Volatile demand. Long international lead time — σL hurts.",
        "family": "Electrical",
        "demand_pattern": "Volatile",
        "weekly_demand_mean": 180,
        "weekly_demand_cv": 0.50,
        "lead_time_mean_weeks": 7,
        "lead_time_std_weeks": 2.0,
        "unit_cost": 180,
        "holding_cost_pct": 0.28,
        "order_cost": 800,
        "backlog_cost_unit_week": 40,
        "review_period_weeks": 2,
        "recommended_policy": "(R,S)",
    },
    "Critical — Fuel Injector Kit": {
        "tagline": "Lumpy demand. Stock-out cost is very high — react immediately.",
        "family": "Powertrain",
        "demand_pattern": "Lumpy",
        "weekly_demand_mean": 28,
        "weekly_demand_cv": 0.70,
        "lead_time_mean_weeks": 10,
        "lead_time_std_weeks": 2.5,
        "unit_cost": 420,
        "holding_cost_pct": 0.30,
        "order_cost": 1200,
        "backlog_cost_unit_week": 120,
        "review_period_weeks": 0,
        "recommended_policy": "(s,Q)",
    },
    "Critical — Turbo Housing": {
        "tagline": "Very slow mover. Cannot afford a stock-out. High unit value.",
        "family": "Electrical",
        "demand_pattern": "Lumpy",
        "weekly_demand_mean": 8,
        "weekly_demand_cv": 0.85,
        "lead_time_mean_weeks": 14,
        "lead_time_std_weeks": 3.5,
        "unit_cost": 1150,
        "holding_cost_pct": 0.30,
        "order_cost": 2000,
        "backlog_cost_unit_week": 350,
        "review_period_weeks": 0,
        "recommended_policy": "(s,Q)",
    },
    "Chassis — Wheel Bearing Kit": {
        "tagline": "Steady throughput. Textbook EOQ product — low CV, reliable LT.",
        "family": "Chassis",
        "demand_pattern": "Stable",
        "weekly_demand_mean": 620,
        "weekly_demand_cv": 0.20,
        "lead_time_mean_weeks": 4,
        "lead_time_std_weeks": 0.5,
        "unit_cost": 65,
        "holding_cost_pct": 0.25,
        "order_cost": 450,
        "backlog_cost_unit_week": 20,
        "review_period_weeks": 1,
        "recommended_policy": "(R,S)",
    },
}


def get_scenario_params(name: str) -> dict[str, Any]:
    """Return scenario dict with derived demand_std field added."""
    s = SCENARIOS[name].copy()
    s["weekly_demand_std"] = s["weekly_demand_mean"] * s["weekly_demand_cv"]
    return s
