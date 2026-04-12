"""
Synthetic 120-SKU portfolio dataset for PACCAR-like demo.
Generated at import with numpy.random.seed(42).
All values are formula-derived approximations (~).

Distribution:
  40% Powertrain · 25% Chassis · 20% Electrical · 15% Critical
  55% Stable · 25% Volatile · 20% Lumpy
"""

import numpy as np
import pandas as pd

from utils.formulas import (
    eoq,
    safety_stock_sQ,
    safety_stock_RS,
    reorder_point,
    annual_holding_cost,
    annual_ordering_cost,
    fill_rate,
    sigma_x_sQ,
    sigma_x_RS,
    WEEKS_PER_YEAR,
    z_from_csl,
)

# ── Constants ─────────────────────────────────────────────────────────────────
N_SKUS = 120
TARGET_CSL = 0.95  # baseline service level target for portfolio
ML_CV_FACTOR = 0.80  # ML reduces demand σ by 20%
ML_BIAS_FACTOR = 1.00  # ML removes systematic bias
BASE_BIAS = 1.10  # baseline inflates demand mean by 10% (over-forecast)

FAMILY_WEIGHTS = {
    "Powertrain": 0.40,
    "Chassis": 0.25,
    "Electrical": 0.20,
    "Critical": 0.15,
}
PATTERN_WEIGHTS = {"Stable": 0.55, "Volatile": 0.25, "Lumpy": 0.20}

# CV range by pattern
CV_PARAMS = {
    "Stable": (0.10, 0.25),
    "Volatile": (0.30, 0.60),
    "Lumpy": (0.55, 1.00),
}

# Lead time (weeks) by family
LT_PARAMS = {
    "Powertrain": (2, 5, 0.5),  # (mean_min, mean_max, std)
    "Chassis": (3, 6, 1.0),
    "Electrical": (5, 10, 1.5),
    "Critical": (8, 16, 3.0),
}

# Order cost by family ($)
ORDER_COST_RANGE = {
    "Powertrain": (200, 600),
    "Chassis": (300, 700),
    "Electrical": (500, 1200),
    "Critical": (800, 2500),
}

# Holding cost % by family
HOLDING_PCT = {
    "Powertrain": 0.25,
    "Chassis": 0.25,
    "Electrical": 0.28,
    "Critical": 0.30,
}


def _generate_portfolio() -> pd.DataFrame:
    rng = np.random.default_rng(42)

    families = list(FAMILY_WEIGHTS.keys())
    fam_probs = list(FAMILY_WEIGHTS.values())
    patterns = list(PATTERN_WEIGHTS.keys())
    pat_probs = list(PATTERN_WEIGHTS.values())

    rows = []
    for i in range(N_SKUS):
        family = rng.choice(families, p=fam_probs)
        pattern = rng.choice(patterns, p=pat_probs)

        # Unit cost — log-normal, centre ≈ $85, range $8–$1,800
        unit_cost = float(np.clip(rng.lognormal(mean=4.4, sigma=1.1), 8, 1800))

        # Weekly demand mean — log-normal, heavier for commodity parts
        base_mean = (
            rng.lognormal(mean=5.5, sigma=1.2)
            if family in ("Powertrain", "Chassis")
            else rng.lognormal(mean=3.5, sigma=1.3)
        )
        demand_mean = float(np.clip(base_mean, 5, 2000))

        # CV and derived std
        cv_lo, cv_hi = CV_PARAMS[pattern]
        cv = float(rng.uniform(cv_lo, cv_hi))
        demand_std = demand_mean * cv

        # Lead time
        lt_lo, lt_hi, lt_std = LT_PARAMS[family]
        lt_mean = float(rng.uniform(lt_lo, lt_hi))
        lt_std_val = lt_std

        # Review period (0 = (s,Q), >0 = (R,S))
        review_period = int(rng.choice([0, 0, 1, 2], p=[0.45, 0.05, 0.35, 0.15]))
        policy = "(s,Q)" if review_period == 0 else "(R,S)"

        # Order cost
        oc_lo, oc_hi = ORDER_COST_RANGE[family]
        order_cost_val = float(rng.uniform(oc_lo, oc_hi))
        holding_pct = HOLDING_PCT[family]

        # Annual demand
        annual_demand = demand_mean * WEEKS_PER_YEAR

        # Holding cost per unit per year
        h = unit_cost * holding_pct

        # EOQ
        q_star = eoq(annual_demand, order_cost_val, h)
        q_star = max(q_star, 1.0)

        # Z for target CSL
        z = z_from_csl(TARGET_CSL)

        # ── BASELINE (no ML — inflated bias + higher variability) ──
        base_dm = demand_mean * BASE_BIAS
        base_ds = demand_std * 1.20

        if policy == "(s,Q)":
            ss_base = safety_stock_sQ(z, base_dm, base_ds, lt_mean, lt_std_val)
            sx_base = sigma_x_sQ(base_dm, base_ds, lt_mean, lt_std_val)
        else:
            ss_base = safety_stock_RS(
                z, base_dm, base_ds, lt_mean, lt_std_val, review_period
            )
            sx_base = sigma_x_RS(base_dm, base_ds, lt_mean, lt_std_val, review_period)

        rop_base = reorder_point(base_dm, lt_mean, ss_base)
        cycle_demand_base = base_dm * (
            lt_mean if policy == "(s,Q)" else (lt_mean + review_period)
        )
        fr_base = fill_rate(ss_base, sx_base, max(cycle_demand_base, 1.0))

        # ── ML-IMPROVED (corrected bias, tighter σ) ──
        ml_dm = demand_mean  # bias corrected
        ml_ds = demand_std * ML_CV_FACTOR

        if policy == "(s,Q)":
            ss_ml = safety_stock_sQ(z, ml_dm, ml_ds, lt_mean, lt_std_val)
            sx_ml = sigma_x_sQ(ml_dm, ml_ds, lt_mean, lt_std_val)
        else:
            ss_ml = safety_stock_RS(z, ml_dm, ml_ds, lt_mean, lt_std_val, review_period)
            sx_ml = sigma_x_RS(ml_dm, ml_ds, lt_mean, lt_std_val, review_period)

        rop_ml = reorder_point(ml_dm, lt_mean, ss_ml)
        cycle_demand_ml = ml_dm * (
            lt_mean if policy == "(s,Q)" else (lt_mean + review_period)
        )
        fr_ml = fill_rate(ss_ml, sx_ml, max(cycle_demand_ml, 1.0))

        # ── Costs ──
        avg_inv_base = ss_base + q_star / 2.0
        avg_inv_ml = ss_ml + q_star / 2.0

        hold_base = annual_holding_cost(avg_inv_base, unit_cost, holding_pct)
        hold_ml = annual_holding_cost(avg_inv_ml, unit_cost, holding_pct)
        order_base = annual_ordering_cost(annual_demand, q_star, order_cost_val)
        order_ml = order_base  # EOQ doesn't change with ML (same annual demand)

        total_base = hold_base + order_base
        total_ml = hold_ml + order_ml
        annual_saving = total_base - total_ml

        ss_value_base = ss_base * unit_cost
        ss_value_ml = ss_ml * unit_cost

        rows.append(
            {
                "SKU": f"SKU-{i + 1:03d}",
                "Family": family,
                "Pattern": pattern,
                "Policy": policy,
                "CV": round(cv, 2),
                "Unit_Cost": round(unit_cost, 2),
                "LT_Weeks": round(lt_mean, 1),
                "Review_Period": review_period,
                "Weekly_Demand": round(demand_mean, 1),
                "EOQ": round(q_star, 0),
                # Baseline
                "SS_Base_Units": round(ss_base, 1),
                "SS_Base_Value": round(ss_value_base, 2),
                "ROP_Base": round(rop_base, 1),
                "Fill_Rate_Base": round(fr_base * 100, 1),
                "Hold_Cost_Base": round(hold_base, 2),
                "Order_Cost_Base": round(order_base, 2),
                "Total_Cost_Base": round(total_base, 2),
                # ML-Improved
                "SS_ML_Units": round(ss_ml, 1),
                "SS_ML_Value": round(ss_value_ml, 2),
                "ROP_ML": round(rop_ml, 1),
                "Fill_Rate_ML": round(fr_ml * 100, 1),
                "Hold_Cost_ML": round(hold_ml, 2),
                "Order_Cost_ML": round(order_ml, 2),
                "Total_Cost_ML": round(total_ml, 2),
                # Delta
                "SS_Delta_Pct": round((ss_ml - ss_base) / max(ss_base, 0.01) * 100, 1),
                "Annual_Saving": round(annual_saving, 2),
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values("Annual_Saving", ascending=False).reset_index(drop=True)
    return df


# ── Module-level dataset — computed once at import ───────────────────────────
PORTFOLIO_DF: pd.DataFrame = _generate_portfolio()


def get_portfolio(
    families: list[str] | None = None,
    patterns: list[str] | None = None,
) -> pd.DataFrame:
    """Return filtered portfolio dataframe."""
    df = PORTFOLIO_DF.copy()
    if families:
        df = df[df["Family"].isin(families)]
    if patterns:
        df = df[df["Pattern"].isin(patterns)]
    return df


def portfolio_summary(df: pd.DataFrame) -> dict:
    """Aggregate KPIs for the given portfolio slice."""
    return {
        "n_skus": len(df),
        "ss_value_base": df["SS_Base_Value"].sum(),
        "ss_value_ml": df["SS_ML_Value"].sum(),
        "total_cost_base": df["Total_Cost_Base"].sum(),
        "total_cost_ml": df["Total_Cost_ML"].sum(),
        "hold_cost_base": df["Hold_Cost_Base"].sum(),
        "hold_cost_ml": df["Hold_Cost_ML"].sum(),
        "order_cost_base": df["Order_Cost_Base"].sum(),
        "order_cost_ml": df["Order_Cost_ML"].sum(),
        "annual_saving": df["Annual_Saving"].sum(),
        "avg_fill_rate_base": df["Fill_Rate_Base"].mean(),
        "avg_fill_rate_ml": df["Fill_Rate_ML"].mean(),
        "ss_delta_pct": (df["SS_ML_Value"].sum() - df["SS_Base_Value"].sum())
        / max(df["SS_Base_Value"].sum(), 1)
        * 100,
    }
