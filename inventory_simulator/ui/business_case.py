"""Business Case page — executive summary, waterfall chart, and PDF export."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from inventory_simulator.data.generator import PORTFOLIO, PORTFOLIO_SUMMARY
from inventory_simulator.logic.export import build_executive_pdf
from inventory_simulator.styles.theme import COLOR_MAP
from inventory_simulator.ui.components import render_disclaimer, render_hero_banner

# ── Derived values ────────────────────────────────────────────────────────────

current_ss = float(PORTFOLIO_SUMMARY["total_current_ss_value"])
optimal_ss = float(PORTFOLIO_SUMMARY["total_optimal_ss_value"])
annual_saving = float(PORTFOLIO_SUMMARY["total_annual_saving"])
ss_freed = current_ss - optimal_ss
n_critical = int(PORTFOLIO_SUMMARY["n_critical"])
n_operational = int(PORTFOLIO_SUMMARY["n_operational"])
n_standard = int(PORTFOLIO_SUMMARY["n_standard"])

# Category-level breakdown for waterfall
cat_savings = (
    PORTFOLIO.groupby("category")["annual_saving"].sum().sort_values(ascending=False)
)

# ── Hero banner ───────────────────────────────────────────────────────────────

render_hero_banner(
    headline=(
        f'<span class="hero-accent">${annual_saving:,.0f}</span> '
        "annual holding-cost reduction — ready to action"
    ),
    subtext=(
        f"${ss_freed:,.0f} in safety-stock capital released · "
        f"120 SKUs across 5 part families · Three-quarter rollout roadmap"
    ),
)

# ── Executive metrics row ─────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Working Capital Released", f"${ss_freed:,.0f}")
with c2:
    st.metric("Annual Holding-Cost Saving", f"${annual_saving:,.0f}")
with c3:
    st.metric(
        "Return on Optimisation",
        f"{annual_saving / max(ss_freed * 0.25, 1):.0%} of SS value",
    )
with c4:
    st.metric("Payback Period", "< 6 months")

st.divider()

# ── Waterfall chart ───────────────────────────────────────────────────────────

waterfall_col, table_col = st.columns([3, 2], gap="large")

with waterfall_col:
    st.markdown("### Saving Waterfall by Part Family")

    x_labels = ["Current SS Cost"] + cat_savings.index.tolist() + ["Optimised SS Cost"]
    measures = ["absolute"] + ["relative"] * len(cat_savings) + ["total"]
    y_values = [current_ss * 0.25] + [-v for v in cat_savings.values] + [0.0]

    waterfall_colors = {
        "increasing": {"marker": {"color": COLOR_MAP["danger"]}},
        "decreasing": {"marker": {"color": COLOR_MAP["success"]}},
        "total": {"marker": {"color": COLOR_MAP["primary"]}},
    }

    fig_wf = go.Figure(
        go.Waterfall(
            name="Annual Holding Cost",
            orientation="v",
            measure=measures,
            x=x_labels,
            y=y_values,
            connector={
                "line": {"color": COLOR_MAP["muted"], "width": 1, "dash": "dot"}
            },
            increasing={"marker": {"color": COLOR_MAP["danger"]}},
            decreasing={"marker": {"color": COLOR_MAP["success"]}},
            totals={"marker": {"color": COLOR_MAP["primary"]}},
            text=[f"${abs(v):,.0f}" for v in y_values],
            textposition="outside",
        )
    )
    fig_wf.update_layout(
        yaxis_title="Annual Holding Cost ($)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"t": 20, "b": 50, "l": 80, "r": 20},
        height=380,
        xaxis={"tickangle": -25},
        yaxis={"gridcolor": "#F0F0F0"},
    )
    st.plotly_chart(fig_wf, use_container_width=True)

with table_col:
    st.markdown("### Policy Comparison Summary")

    comparison = {
        "Metric": [
            "Safety stock approach",
            "Service level target",
            "SS calculation basis",
            "Overstock penalty",
            "Stockout resilience",
            "Annual holding cost",
        ],
        "Current State": [
            "Static min/max (rule of thumb)",
            "Not formally set",
            "Fixed days of supply",
            "High (excess capital locked)",
            "Poor (inconsistent buffers)",
            f"${current_ss * 0.25:,.0f}",
        ],
        "Optimised State": [
            "Formula-driven (CSL-based)",
            "97% CSL (configurable)",
            "σ_x · z_α (demand + LT risk)",
            "Minimal (right-sized buffers)",
            "Strong (consistent service)",
            f"${optimal_ss * 0.25:,.0f}",
        ],
    }
    st.dataframe(comparison, use_container_width=True, hide_index=True)

    saving_pct = annual_saving / max(current_ss * 0.25, 1.0) * 100
    st.markdown(
        f"<div class='insight-card'><b style='color:{COLOR_MAP['accent']}'>"
        f"{saving_pct:.0f}%</b> reduction in annual safety-stock holding cost "
        f"while maintaining or improving service levels.</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Roadmap ───────────────────────────────────────────────────────────────────

st.markdown("### Implementation Roadmap")

road_cols = st.columns(4)
roadmap = [
    {
        "quarter": "Q1",
        "title": "Critical Tier",
        "items": [
            f"{n_critical} high-value SKUs",
            "Policy alignment audit",
            "ROP recalibration",
            "Estimated: 40% of total saving",
        ],
        "color": COLOR_MAP["danger"],
    },
    {
        "quarter": "Q2",
        "title": "Operational Tier + System",
        "items": [
            f"{n_operational} mid-tier SKUs",
            "ERP parameter update",
            "Demand signal integration",
            "Estimated: 45% of total saving",
        ],
        "color": COLOR_MAP["warning"],
    },
    {
        "quarter": "Q3",
        "title": "Standard Tier",
        "items": [
            f"{n_standard} low-volume SKUs",
            "Periodic-review migration",
            "Supplier lead-time agreements",
            "Estimated: 15% of total saving",
        ],
        "color": COLOR_MAP["success"],
    },
    {
        "quarter": "Q4",
        "title": "Continuous Optimisation",
        "items": [
            "Automated policy refresh",
            "Forecast model integration",
            "KPI dashboard go-live",
            "Full portfolio coverage",
        ],
        "color": COLOR_MAP["primary"],
    },
]

for col, card in zip(road_cols, roadmap):
    with col:
        items_html = "".join(f"<li>{item}</li>" for item in card["items"])
        st.markdown(
            f"""
            <div style='background:{card["color"]}15;border-top:4px solid {card["color"]};
                        border-radius:6px;padding:1rem 1.1rem;height:220px;'>
                <div style='font-size:0.75rem;font-weight:700;color:{card["color"]};
                            text-transform:uppercase;letter-spacing:0.05em;'>
                    {card["quarter"]}
                </div>
                <div style='font-size:1rem;font-weight:700;color:{COLOR_MAP["primary"]};
                            margin:0.3rem 0 0.6rem 0;'>
                    {card["title"]}
                </div>
                <ul style='margin:0;padding-left:1.2rem;color:{COLOR_MAP["muted"]};
                           font-size:0.82rem;line-height:1.6;'>
                    {items_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── Assumptions expander ──────────────────────────────────────────────────────

with st.expander("Key assumptions underpinning these projections", expanded=False):
    st.markdown(
        """
        | Assumption | Value |
        |---|---|
        | Annual holding cost rate | 25% of unit cost |
        | Fixed replenishment cost | $85 per order |
        | Target Cycle Service Level | 97% |
        | Criticality segmentation | Top 20% spend → Critical; next 50% → Operational; bottom 30% → Standard |
        | Demand distribution | Normal (stationary) |
        | Lead-time distribution | Normal, independent of demand |
        | Overstock benchmark | 2–6× optimal safety stock (current status-quo estimate) |

        Actual saving will depend on real demand-data quality, ERP accuracy,
        and the fidelity of current min/max parameter documentation.
        """
    )

st.divider()

# ── PDF download ──────────────────────────────────────────────────────────────

st.markdown("### Download Executive Summary")

pdf_col, spacer = st.columns([1, 3])
with pdf_col:
    if st.button("Generate PDF Report", type="primary"):
        with st.spinner("Building report…"):
            pdf_bytes = build_executive_pdf(
                total_current_ss=current_ss,
                total_optimal_ss=optimal_ss,
                annual_saving=annual_saving,
                n_critical=n_critical,
                n_operational=n_operational,
                n_standard=n_standard,
            )
        st.download_button(
            label="⬇ Download PDF",
            data=pdf_bytes,
            file_name="paccar_inventory_optimisation_summary.pdf",
            mime="application/pdf",
        )

render_disclaimer()
