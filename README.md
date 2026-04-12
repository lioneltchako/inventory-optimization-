## Inventory Policy Simulator
## DynaCraft / PACCAR — Senior Demand Planner Demo

Interactive Streamlit demo explaining inventory optimization methodology
and quantifying the impact of ML forecast quality on safety stock and cost.

> Built for a Senior Demand Planner interview at DynaCraft (PACCAR division).
> Combines supply chain methodology (Vandeput, 2020) with data-driven
> business impact analysis. Step 1 of a two-phase project.

**What it shows:**
- How policy choice (s,Q vs R,S) affects safety stock and cost
- How ML forecast quality directly reduces safety stock needs
- Portfolio-level impact across 120 synthetic PACCAR-like SKUs

### Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Deploy to Streamlit Cloud (share the URL before the interview)
1. Push: `./push.sh "ready to deploy"`
2. Go to https://share.streamlit.io → New app → this repo → `app.py`

Done. Share the URL with the hiring manager.

### Project structure
```
inventory_demo/
├── app.py                    ← navigation shell + sidebar
├── pages/
│   ├── 1_overview.py         ← "The Problem & The Tool"
│   ├── 2_sku_explorer.py     ← single-SKU deep-dive (hero page)
│   ├── 3_portfolio.py        ← 120-SKU portfolio impact
│   ├── 4_methodology.py      ← formula explainer (trust builder)
│   └── 5_business_case.py    ← executive summary + PDF export
├── utils/
│   ├── colors.py             ← shared color constants
│   ├── formulas.py           ← inventory math (Vandeput models)
│   ├── scenarios.py          ← 6 pre-built PACCAR SKU profiles
│   ├── portfolio_data.py     ← 120-SKU synthetic dataset
│   └── disclaimer.py        ← shared banner functions
├── assets/
│   └── style.css
├── tests/
│   └── test_formulas.py      ← 5 smoke tests (pytest)
├── push.sh
└── requirements.txt
```

### Run smoke tests
```bash
pytest tests/ -v
```

All 5 tests verify the core inventory math:
- EOQ calculation [Vandeput Ch. 2]
- Safety stock with fixed lead time [Ch. 4]
- Safety stock with stochastic lead time [Ch. 6, eq. 6.4]
- (R,S) vs (s,Q) safety stock ordering [Ch. 6, eq. 6.5]
- Fill rate > CSL for same safety stock [Ch. 7]

### Step 2 (planned)
Full simulation-optimization engine:
- Monte Carlo simulation · KDE demand modeling
- Bidirectional sim-opt (Vandeput Ch. 13, Method #2)
- ML forecast integration · 8,000 SKU scope
- XGBoost bias-corrected demand forecasts

### Methodology
Vandeput, N. (2020). *Inventory Optimization: Models and Simulations*.
De Gruyter. DOI: 10.1515/9783110673944

### Synthetic data statement
All parameters and KPIs are generated from synthetic PACCAR-like scenarios.
They reflect real supply chain behavior patterns but do not represent actual
DynaCraft or PACCAR data. Approximated values are labeled with ~.
