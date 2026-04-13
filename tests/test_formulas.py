"""Smoke tests for inventory_simulator.logic.formulas.

Each test verifies a key formula result against an analytically-derived
expected value.
"""

from __future__ import annotations

import math


from inventory_simulator.logic.formulas import (
    annual_holding_cost,
    annual_ordering_cost,
    csl_from_z,
    eoq,
    fill_rate,
    normal_loss,
    reorder_point,
    safety_stock_RS,
    safety_stock_sQ,
    sigma_x_RS,
    sigma_x_sQ,
    z_from_csl,
)


# ── EOQ ───────────────────────────────────────────────────────────────────────


def test_eoq_basic() -> None:
    """Q* = sqrt(2 * D * S / h)."""
    result = eoq(annual_demand=300, order_cost=44_200, holding_cost_per_unit=3.0)
    expected = math.sqrt(2 * 300 * 44_200 / 3)
    assert abs(result - expected) < 0.5, f"EOQ mismatch: {result:.1f} vs {expected:.1f}"


def test_eoq_degenerate_returns_one() -> None:
    """Zero or negative inputs should return the safe fallback of 1.0."""
    assert eoq(0, 10, 10) == 1.0
    assert eoq(100, 0, 10) == 1.0
    assert eoq(100, 10, 0) == 1.0


# ── sigma_x ───────────────────────────────────────────────────────────────────


def test_sigma_x_sQ_fixed_lead_time() -> None:
    """With zero lead-time std dev, sigma_x = sigma_d * sqrt(mu_L)."""
    mu_d, sigma_d, mu_L = 10.0, 4.0, 9.0
    result = sigma_x_sQ(mu_d, sigma_d, mu_L, lt_std=0.0)
    expected = sigma_d * math.sqrt(mu_L)  # = 4 * 3 = 12
    assert abs(result - expected) < 0.01


def test_sigma_x_sQ_stochastic_lt() -> None:
    """sigma_x = sqrt(mu_L * sigma_d^2 + sigma_L^2 * mu_d^2)."""
    mu_d, sigma_d = 5.0, 2.0
    mu_L, sigma_L = 4.0, 1.5
    result = sigma_x_sQ(mu_d, sigma_d, mu_L, sigma_L)
    expected = math.sqrt(mu_L * sigma_d**2 + sigma_L**2 * mu_d**2)
    assert abs(result - expected) < 1e-9


def test_sigma_x_RS_longer_than_sQ() -> None:
    """(R,S) sigma_x must exceed (s,Q) sigma_x for the same SKU and positive R."""
    mu_d, sigma_d, mu_L, sigma_L = 8.0, 3.0, 7.0, 2.0
    review_period = 7
    sx_sQ = sigma_x_sQ(mu_d, sigma_d, mu_L, sigma_L)
    sx_RS = sigma_x_RS(mu_d, sigma_d, mu_L, sigma_L, review_period)
    assert sx_RS > sx_sQ


# ── Safety stock ordering ─────────────────────────────────────────────────────


def test_ss_RS_exceeds_ss_sQ() -> None:
    """With identical parameters, (R,S) SS > (s,Q) SS for positive review period."""
    args = dict(
        z=1.645,
        demand_mean=6.0,
        demand_std=2.5,
        lt_mean=10.0,
        lt_std=2.0,
    )
    ss_sq = safety_stock_sQ(**args)
    ss_rs = safety_stock_RS(**args, review_period=7)
    assert ss_rs > ss_sq


# ── Fill rate ─────────────────────────────────────────────────────────────────


def test_fill_rate_exceeds_csl() -> None:
    """Fill rate (beta) must be >= CSL for the same safety stock level."""
    sigma_x = 15.0
    q = 80.0
    z = 1.645  # ~95% CSL
    ss = z * sigma_x
    csl = csl_from_z(z)
    beta = fill_rate(ss, sigma_x, q)
    assert beta >= csl, f"Fill rate {beta:.4f} should be >= CSL {csl:.4f}"


def test_fill_rate_clamps_to_one() -> None:
    """Very large safety stock should return fill rate <= 1.0."""
    assert fill_rate(10_000, 1.0, 50.0) <= 1.0


def test_fill_rate_degenerate_sigma() -> None:
    """Zero sigma_x should return perfect fill rate."""
    assert fill_rate(0.0, 0.0, 50.0) == 1.0


# ── Normal loss function ──────────────────────────────────────────────────────


def test_normal_loss_at_zero() -> None:
    """L(0) should equal the standard Normal PDF at 0: 1/sqrt(2*pi)."""
    result = normal_loss(0.0)
    expected = 1.0 / math.sqrt(2 * math.pi)
    assert abs(result - expected) < 1e-6


# ── Reorder point ─────────────────────────────────────────────────────────────


def test_reorder_point_basic() -> None:
    """ROP = mu_d * mu_L + SS."""
    result = reorder_point(demand_mean=5.0, lt_mean=10.0, safety_stock=20.0)
    assert abs(result - 70.0) < 1e-9


# ── z / CSL round-trip ────────────────────────────────────────────────────────


def test_z_csl_round_trip() -> None:
    """z_from_csl and csl_from_z should be mutual inverses."""
    for csl in (0.90, 0.95, 0.97, 0.99):
        z = z_from_csl(csl)
        recovered = csl_from_z(z)
        assert abs(recovered - csl) < 1e-6, f"Round-trip failed for CSL={csl}"


# ── Cost functions ────────────────────────────────────────────────────────────


def test_annual_holding_cost() -> None:
    """Holding cost = avg_inventory * unit_cost * holding_pct."""
    result = annual_holding_cost(avg_inventory=100.0, unit_cost=50.0, holding_pct=0.25)
    assert abs(result - 1250.0) < 1e-9


def test_annual_ordering_cost() -> None:
    """Ordering cost = (D / Q) * order_cost."""
    result = annual_ordering_cost(annual_demand=365.0, order_qty=73.0, order_cost=100.0)
    expected = (365.0 / 73.0) * 100.0
    assert abs(result - expected) < 1e-6
