"""Synthetic Phase 1 output generator for the Dynacraft demo.

Generates 50 SKUs across 3 categories with realistic demand patterns,
ML residuals (deliberately non-normal), and ERP metadata.
No ML models are instantiated — this simulates Phase 1 outputs.
"""

from __future__ import annotations

import numpy as np

from inventory_simulator.data.contracts import SKUForecastResult

CATEGORIES: list[str] = ["Electronics", "Mechanical", "Accessories"]
NUM_SKUS: int = 50
WEEKS_HISTORY: int = 104
NUM_RESIDUALS: int = 80
FORECAST_HORIZON_WEEKS: int = 26


def _log_uniform(rng: np.random.Generator, low: float, high: float) -> float:
    """Sample from a log-uniform distribution."""
    return float(np.exp(rng.uniform(np.log(low), np.log(high))))


def _generate_demand_history(
    rng: np.random.Generator,
    base: float,
    trend_rate: float,
    seasonality_amp: float,
    noise_sigma: float,
    is_intermittent: bool,
) -> np.ndarray:
    """Generate 104 weeks of weekly demand with trend, seasonality, noise."""
    weeks = np.arange(WEEKS_HISTORY, dtype=np.float64)
    trend = base * (1.0 + trend_rate) ** (weeks / 52.0)
    season = base * seasonality_amp * np.sin(2.0 * np.pi * weeks / 52.0)
    noise = rng.normal(0, base * noise_sigma, size=WEEKS_HISTORY)
    demand = trend + season + noise
    if is_intermittent:
        mask = rng.random(WEEKS_HISTORY) > 0.30
        demand = demand * mask
    return np.maximum(demand, 0.0)


def _generate_residuals(rng: np.random.Generator, sigma_base: float) -> np.ndarray:
    """Generate non-normal residuals (mixture of two Gaussians).

    70% from N(0, sigma1) and 30% from N(mu2, sigma2) where
    mu2 = 1.0*sigma1 and sigma2 = 2.5*sigma1.
    This creates visible right-skew (target avg skewness >= 0.5).
    """
    sigma1 = max(sigma_base, 0.01)
    n_main = int(NUM_RESIDUALS * 0.70)
    n_tail = NUM_RESIDUALS - n_main
    main_part = rng.normal(0, sigma1, n_main)
    tail_part = rng.normal(1.0 * sigma1, 2.5 * sigma1, n_tail)
    residuals = np.concatenate([main_part, tail_part])
    rng.shuffle(residuals)
    return residuals


def _generate_forecast(avg_weekly_demand: float, trend_rate: float) -> np.ndarray:
    """Generate daily forecast over the risk horizon."""
    weeks = np.arange(FORECAST_HORIZON_WEEKS, dtype=np.float64)
    weekly = avg_weekly_demand * (1.0 + trend_rate) ** (weeks / 52.0)
    daily = np.repeat(weekly / 7.0, 7)
    return daily


def generate_phase1_outputs(
    seed: int = 42,
) -> dict[str, SKUForecastResult]:
    """Generate synthetic Phase 1 outputs for 50 SKUs."""
    rng = np.random.default_rng(seed)
    results: dict[str, SKUForecastResult] = {}
    review_options = [1, 7, 14]
    all_skewness: list[float] = []

    for i in range(NUM_SKUS):
        sku_id = f"DYN-{i + 1:04d}"
        category = CATEGORIES[i % len(CATEGORIES)]
        base = _log_uniform(rng, 10.0, 500.0)
        trend_rate = rng.uniform(-0.02, 0.03)
        seasonality_amp = rng.uniform(0.05, 0.30)
        noise_sigma = rng.uniform(0.10, 0.25)
        is_intermittent = i < int(NUM_SKUS * 0.20)

        demand_history = _generate_demand_history(
            rng, base, trend_rate, seasonality_amp, noise_sigma, is_intermittent
        )
        avg_weekly = float(np.mean(demand_history))
        residuals = _generate_residuals(rng, avg_weekly * noise_sigma)
        forecast = _generate_forecast(avg_weekly, trend_rate)

        _append_skewness(residuals, all_skewness)

        results[sku_id] = SKUForecastResult(
            sku_id=sku_id,
            category=category,
            forecast=forecast,
            residuals=residuals,
            demand_history=demand_history,
            avg_weekly_demand=avg_weekly,
            model_mae=float(np.mean(np.abs(residuals))),
            model_bias=float(np.mean(residuals)),
            lead_time_days=int(rng.integers(7, 22)),
            review_period_days=review_options[int(rng.integers(0, 3))],
            unit_cost=_log_uniform(rng, 5.0, 500.0),
            holding_cost_rate=float(rng.uniform(0.20, 0.30)),
            stockout_cost_per_unit=0.0,
        )
        results[sku_id].stockout_cost_per_unit = results[sku_id].unit_cost * 2.0

    avg_skewness = float(np.mean(all_skewness))
    assert avg_skewness >= 0.5, f"Average skewness {avg_skewness:.2f} < 0.5"
    return results


def _append_skewness(residuals: np.ndarray, all_skewness: list[float]) -> None:
    """Compute and append skewness of residuals."""
    n = len(residuals)
    mean = float(np.mean(residuals))
    std = float(np.std(residuals))
    if std > 0:
        skew = float(np.sum(((residuals - mean) / std) ** 3)) / n
        all_skewness.append(skew)
