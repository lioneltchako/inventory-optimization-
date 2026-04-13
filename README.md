## Inventory Policy Simulator
## DynaCraft / PACCAR — Senior Demand Planner

Interactive decision-support tool for inventory policy analysis across a
120-SKU heavy-duty truck parts portfolio. Quantifies the working-capital
impact of safety-stock right-sizing under (s,Q) and (R,S) policies.

> Built for a Senior Demand Planner role at DynaCraft (PACCAR division).
> Designed to feel like a tool a supply chain manager would open on a
> Monday morning — not an academic exercise.

**What it shows:**
- Portfolio-level opportunity mapping (demand variability vs. safety stock excess)
- Single-SKU 90-day stock trajectory simulation with policy comparison
- Spend-based criticality segmentation (Critical / Operational / Standard)
- Waterfall cost-reduction analysis with phased implementation roadmap
- Executive PDF export for leadership review

### Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Deploy to Streamlit Cloud
1. Push: `./push.sh "ready to deploy"`
2. Go to share.streamlit.io → New app → this repo → `app.py`

### Project structure
```
inventory-optimization-/
├── app.py                                ← entry point (st.navigation)
├── inventory_simulator/
│   ├── data/
│   │   └── generator.py                 ← 120-SKU synthetic portfolio
│   ├── logic/
│   │   ├── formulas.py                  ← core inventory math
│   │   ├── simulation.py                ← 90-day stock trajectory engine
│   │   └── export.py                    ← PDF report generation
│   ├── ui/
│   │   ├── components.py                ← shared Streamlit components
│   │   ├── overview.py                  ← portfolio KPIs + trade-off curve
│   │   ├── portfolio.py                 ← opportunity map + treemap
│   │   ├── sku_explorer.py              ← hero page: simulation + deep dive
│   │   ├── methodology.py               ← formulas, assumptions, limitations
│   │   └── business_case.py             ← executive summary + waterfall + PDF
│   └── styles/
│       └── theme.py                     ← COLOR_MAP + CSS (single source)
├── assets/
│   └── style.css                        ← static CSS supplement
├── tests/
│   └── test_formulas.py                 ← 14 smoke tests (pytest)
├── push.sh
└── requirements.txt
```

### Run smoke tests
```bash
pytest tests/ -v
```

14 tests covering: EOQ, sigma_x for (s,Q) and (R,S), safety stock ordering,
fill rate vs CSL, Normal Loss Function, reorder point, z/CSL round-trip,
cost calculations, and edge cases.

### Synthetic data statement
All parameters and KPIs are generated from synthetic PACCAR-like scenarios.
They reflect realistic heavy-duty truck parts distribution patterns but do
not represent actual DynaCraft or PACCAR operational data.
