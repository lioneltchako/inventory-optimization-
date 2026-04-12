"""
Smoke tests for inventory formulas.
Methodology: Vandeput (2020) "Inventory Optimization: Models and Simulations"

Run: pytest tests/ -v
"""

import math

from utils.formulas import (
    eoq,
    safety_stock_sQ,
    safety_stock_RS,
    fill_rate,
    csl_from_z,
)


def test_eoq_basic() -> None:
    """
    Q* = sqrt(2 × D × S / h)
    Q* = sqrt(2 × 300 × 44200 / 3) ≈ 2,973
    [Vandeput Ch. 2, eq. 2.2]
    """
    annual_demand = 44_200  # units/year
    order_cost = 300  # $ per order
    holding_cost_per_unit = 3.0  # $/unit/year  (unit_cost × holding_pct)

    q_star = eoq(annual_demand, order_cost, holding_cost_per_unit)

    expected = math.sqrt(2 * 300 * 44_200 / 3)  # ≈ 2972.7
    assert abs(q_star - expected) < 1.0, (
        f"EOQ mismatch: got {q_star:.1f}, expected {expected:.1f}"
    )


def test_ss_sQ_fixed_lt() -> None:
    """
    With σL = 0 the stochastic formula collapses to the textbook:
    SS = Z × σd × sqrt(L)
    [Vandeput Ch. 4 — baseline case before adding lead time variability]
    """
    z = 1.645  # ~95% CSL
    demand_mean = 100.0
    demand_std = 20.0
    lt_mean = 4.0
    lt_std = 0.0  # deterministic lead time

    ss = safety_stock_sQ(z, demand_mean, demand_std, lt_mean, lt_std)

    # σx = sqrt(4 × 20²) = sqrt(1600) = 40   → SS = 1.645 × 40 = 65.8
    expected = z * demand_std * math.sqrt(lt_mean)
    assert abs(ss - expected) < 0.01, (
        f"SS (fixed LT) mismatch: got {ss:.4f}, expected {expected:.4f}"
    )


def test_ss_sQ_stochastic_lt() -> None:
    """
    With both σd > 0 and σL > 0:
    σx = sqrt(μL × σd² + σL² × μd²)
    SS = Z × σx
    [Vandeput Ch. 6, eq. 6.4]
    """
    z = 1.645
    demand_mean = 100.0
    demand_std = 20.0
    lt_mean = 4.0
    lt_std = 1.0  # variable lead time

    ss_stochastic = safety_stock_sQ(z, demand_mean, demand_std, lt_mean, lt_std)
    ss_fixed = safety_stock_sQ(z, demand_mean, demand_std, lt_mean, 0.0)

    # Adding σL > 0 must increase safety stock
    assert ss_stochastic > ss_fixed, (
        f"Stochastic LT should raise SS: {ss_stochastic:.2f} <= {ss_fixed:.2f}"
    )

    # Verify formula directly: σx = sqrt(4×400 + 1×10000) = sqrt(11600) ≈ 107.7
    sigma_x_expected = math.sqrt(lt_mean * demand_std**2 + lt_std**2 * demand_mean**2)
    assert abs(ss_stochastic - z * sigma_x_expected) < 0.01, "σx formula mismatch"


def test_ss_RS_vs_sQ_same_lt() -> None:
    """
    For the same lead time, (R,S) requires more safety stock than (s,Q)
    because the risk period is (R + L) not just L.
    [Vandeput Ch. 6, eq. 6.5]
    """
    z = 1.645
    demand_mean = 100.0
    demand_std = 20.0
    lt_mean = 4.0
    lt_std = 0.5
    review_period = 2  # weeks

    ss_sQ = safety_stock_sQ(z, demand_mean, demand_std, lt_mean, lt_std)
    ss_RS = safety_stock_RS(z, demand_mean, demand_std, lt_mean, lt_std, review_period)

    assert ss_RS > ss_sQ, (
        f"(R,S) SS {ss_RS:.2f} should exceed (s,Q) SS {ss_sQ:.2f} "
        f"because review period adds blind-spot risk"
    )


def test_fill_rate_higher_than_csl() -> None:
    """
    For the same safety stock, fill rate β > CSL (in terms of probability).
    The Normal Loss Function ensures fill rate approaches 1 faster than CSL.
    [Vandeput Ch. 7, eq. 7.3]
    """
    z = 1.645  # 95% CSL
    demand_mean = 100.0
    demand_std = 20.0
    lt_mean = 4.0
    lt_std = 0.5

    from utils.formulas import sigma_x_sQ as sx_fn

    sigma_x = sx_fn(demand_mean, demand_std, lt_mean, lt_std)
    ss = z * sigma_x
    csl = csl_from_z(z)  # ≈ 0.95
    cycle_dem = demand_mean * lt_mean  # demand per cycle
    beta = fill_rate(ss, sigma_x, cycle_dem)  # fill rate

    assert beta > csl, (
        f"Fill rate ({beta:.4f}) should be > CSL ({csl:.4f}) "
        f"for the same safety stock level"
    )
    # Also sanity-check both are plausible
    assert 0.90 < csl < 1.0, f"CSL out of range: {csl}"
    assert 0.90 < beta <= 1.0, f"Fill rate out of range: {beta}"
