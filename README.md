# Dynacraft Inventory Simulator — Phase 2

**ML-forecast-error-based inventory policy optimization for manufacturing.**

This app is the **Inventory Policy & Cost Optimization Layer** (Phase 2). It takes Phase 1's ML demand forecasts and residuals as inputs, then computes safety stock, reorder points, order quantities, cost tradeoffs, and scenario analysis.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run inventory_simulator/app.py
```

## Architecture

```
inventory_simulator/
├── app.py                  # Entry point, sidebar, session state
├── theme.py                # Centralized colors & Plotly theming
├── data/
│   ├── contracts.py        # Data contracts (SKUForecastResult, PolicyResult)
│   ├── generator.py        # Synthetic Phase 1 output generator (50 SKUs)
│   └── precompute.py       # Cached policy computation at startup
├── models/
│   ├── inventory_policy.py # SS, ROP, EOQ formulas
│   └── cost_engine.py      # Total annual cost model
├── components/
│   ├── cards.py            # Metric card widgets
│   ├── tables.py           # Portfolio table & scenario columns
│   └── charts.py           # Plotly chart library
└── pages/
    ├── 01_portfolio.py     # Portfolio health dashboard
    ├── 02_sku_deep_dive.py # Interactive SKU analysis
    ├── 03_scenario.py      # Scenario comparison (A/B/C)
    ├── 04_frontier.py      # Cost vs service level frontier
    └── 05_next_steps.py    # Roadmap & methodology
```

## Key Insight

Safety stock is sized using **ML forecast residuals**, not raw demand variability. This avoids double-counting trend and seasonality that the model already explains, producing leaner inventory without sacrificing service levels.

## Pages

1. **Portfolio Health** — Overview of all 50 SKUs with ML vs classical safety stock comparison
2. **SKU Deep Dive** — Interactive sliders for service level, lead time, and demand scenarios
3. **Scenario Comparison** — Side-by-side A/B/C scenario analysis
4. **Cost vs Service Level** — Frontier curve showing the exact cost of each service level
5. **Next Steps** — Implementation roadmap and methodology explainers

## Phase 1 Connection

Phase 1 (separate app) delivers ML demand forecasting with validated XGBoost vs baseline:
- ~7% MAE reduction, ~10% RMSE reduction
- Bias nearly eliminated (from approx. -10% to approx. -1%)

Phase 2 consumes those forecast residuals to compute inventory policies.
