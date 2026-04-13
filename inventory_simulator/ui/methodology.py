"""Methodology page — formula cards, assumptions, and model limitations."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import norm  # type: ignore[import-untyped]

from inventory_simulator.styles.theme import COLOR_MAP
from inventory_simulator.ui.components import render_disclaimer, render_hero_banner

# ── Hero banner ───────────────────────────────────────────────────────────────

render_hero_banner(
    headline="Methodology — How the Numbers Are Calculated",
    subtext=(
        "Formulas grounded in standard supply chain operations research. "
        "Every number in this tool is traceable to one of the equations below."
    ),
)

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(
    ["Policy Decision Guide", "Core Formulas", "CSL vs Fill Rate", "Model Limits"]
)

# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Which Policy Is Right for Your SKU?")

    col_sQ, col_RS = st.columns(2, gap="large")

    with col_sQ:
        st.markdown(
            f"""
            <div style='background:{COLOR_MAP["primary"]}; color:white;
                        padding:1.2rem 1.4rem; border-radius:8px;'>
                <h4 style='color:white;margin:0 0 0.6rem 0;'>(s, Q) Continuous Review</h4>
                <p style='color:rgba(255,255,255,0.88);margin:0;font-size:0.9rem;'>
                Monitor inventory after every transaction. Place a fixed order of <b>Q</b>
                units whenever stock falls to or below the reorder point <b>s</b>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            **Best for:**
            - High-value, high-impact parts (Critical tier)
            - Stable demand with short lead times
            - Parts where stockouts carry high penalty costs
            - Systems with real-time inventory visibility

            **Key parameters:**
            | Parameter | Meaning |
            |-----------|---------|
            | s (ROP) | Trigger level for replenishment |
            | Q (EOQ) | Fixed order quantity |
            | SS | Safety stock below ROP |
            """
        )

    with col_RS:
        st.markdown(
            f"""
            <div style='background:{COLOR_MAP["accent"]}; color:white;
                        padding:1.2rem 1.4rem; border-radius:8px;'>
                <h4 style='color:white;margin:0 0 0.6rem 0;'>(R, S) Periodic Review</h4>
                <p style='color:rgba(255,255,255,0.88);margin:0;font-size:0.9rem;'>
                Review inventory every <b>R</b> days. Order enough to bring stock up
                to the order-up-to level <b>S</b> — order quantity varies each cycle.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            **Best for:**
            - Operational/Standard tier with moderate demand
            - Multiple items ordered from the same supplier (joint replenishment)
            - High-variability parts where demand is lumpy or seasonal
            - Environments with periodic counting or batch ordering

            **Key parameters:**
            | Parameter | Meaning |
            |-----------|---------|
            | R | Review interval (days) |
            | S | Order-up-to level |
            | SS | Safety stock for R+L exposure window |
            """
        )

    st.divider()
    st.markdown("### Policy Comparison Summary")

    comparison_data = {
        "Attribute": [
            "Monitoring frequency",
            "Order quantity",
            "Safety stock exposure window",
            "Reaction speed",
            "Admin overhead",
            "Typical holding cost",
        ],
        "(s,Q) Continuous Review": [
            "After every transaction",
            "Fixed (EOQ)",
            "Lead time (L)",
            "Immediate",
            "Higher (requires real-time system)",
            "Lower (shorter exposure)",
        ],
        "(R,S) Periodic Review": [
            "Every R days",
            "Variable (S − current stock)",
            "Lead time + review period (L + R)",
            "Delayed (next review cycle)",
            "Lower (batch reviews)",
            "Higher (longer exposure)",
        ],
    }
    st.dataframe(comparison_data, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Core Inventory Formulas")

    # EOQ
    st.markdown("#### 1. Economic Order Quantity (EOQ)")
    st.latex(r"Q^* = \sqrt{\frac{2 \cdot D \cdot S_o}{h}}")
    st.markdown(
        "Minimises the sum of annual ordering cost and holding cost. "
        "D = annual demand; Sₒ = fixed order cost; h = annual holding cost per unit."
    )

    st.divider()

    # Compound variance
    st.markdown("#### 2. Demand Variability Over Lead Time")
    col_left, col_right = st.columns(2, gap="large")
    with col_left:
        st.markdown("**(s,Q) policy — exposure = lead time L**")
        st.latex(r"\sigma_x = \sqrt{\mu_L \cdot \sigma_d^2 + \sigma_L^2 \cdot \mu_d^2}")
        st.caption(
            "μ_L = mean lead time · σ_d = daily demand std dev · "
            "σ_L = lead time std dev · μ_d = mean daily demand"
        )
    with col_right:
        st.markdown("**(R,S) policy — exposure = L + R**")
        st.latex(
            r"\sigma_x = \sqrt{(\mu_L + R) \cdot \sigma_d^2 + \sigma_L^2 \cdot \mu_d^2}"
        )
        st.caption("R = review interval (days)")

    st.divider()

    # Safety stock
    st.markdown("#### 3. Safety Stock")
    st.latex(r"SS = z_\alpha \cdot \sigma_x")
    st.markdown(
        "z_α is the Normal z-score corresponding to the target Cycle Service Level (CSL). "
        "For 97% CSL, z_α ≈ 1.881."
    )

    st.divider()

    # ROP and order-up-to
    st.markdown("#### 4. Reorder Point and Order-Up-To Level")
    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        st.markdown("**(s,Q) Reorder point:**")
        st.latex(r"s = \mu_d \cdot \mu_L + SS")
    with col_b:
        st.markdown("**(R,S) Order-up-to level:**")
        st.latex(r"S = \mu_d \cdot (\mu_L + R) + SS")

    st.divider()

    # Fill rate
    st.markdown("#### 5. Fill Rate (Type II Service Level)")
    st.latex(r"\beta = 1 - \frac{\sigma_x}{Q} \cdot L(z)")
    st.markdown("Where L(z) is the Standard Normal Loss Function:")
    st.latex(r"L(z) = \varphi(z) - z \cdot [1 - \Phi(z)]")
    st.caption(
        "φ = standard Normal PDF · Φ = standard Normal CDF · "
        "β measures the fraction of demand met without a backorder"
    )

    # Live interactive slider
    st.divider()
    st.markdown("#### Interactive Example")
    ex_csl = st.slider("Set CSL →", 0.85, 0.999, 0.97, step=0.005, format="%.3f")
    ex_sigma = st.slider("σ_x (demand variability over LT)", 1.0, 80.0, 15.0, step=0.5)
    ex_q = st.slider("Order quantity Q", 10.0, 500.0, 80.0, step=5.0)

    ex_z = float(norm.ppf(ex_csl))
    ex_ss = ex_z * ex_sigma
    lz = float(norm.pdf(ex_z) - ex_z * (1.0 - norm.cdf(ex_z)))
    ex_fr = max(0.0, min(1.0, 1.0 - (ex_sigma / ex_q) * lz))

    res_a, res_b, res_c = st.columns(3)
    with res_a:
        st.metric("z-score", f"{ex_z:.3f}")
    with res_b:
        st.metric("Safety Stock", f"{ex_ss:.1f} units")
    with res_c:
        st.metric("Fill Rate", f"{ex_fr:.3%}")


# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### CSL vs Fill Rate — Why They Differ")
    st.markdown(
        "**Cycle Service Level (CSL)** measures the probability of no stockout per replenishment cycle. "
        "**Fill rate (β)** measures the fraction of demand filled from available stock. "
        "For the same safety stock, fill rate is always ≥ CSL."
    )

    csl_arr = np.linspace(0.80, 0.999, 80)
    z_arr = norm.ppf(csl_arr)

    # For a typical SKU
    sigma_demo = 20.0
    q_demo = 100.0
    lz_arr = norm.pdf(z_arr) - z_arr * (1.0 - norm.cdf(z_arr))
    fr_arr = np.clip(1.0 - (sigma_demo / q_demo) * lz_arr, 0.0, 1.0)

    fig_cf = go.Figure()
    fig_cf.add_trace(
        go.Scatter(
            x=csl_arr * 100,
            y=csl_arr * 100,
            mode="lines",
            name="CSL (= x-axis reference)",
            line={"color": COLOR_MAP["primary"], "dash": "dot", "width": 1.5},
        )
    )
    fig_cf.add_trace(
        go.Scatter(
            x=csl_arr * 100,
            y=fr_arr * 100,
            mode="lines",
            name="Fill Rate β",
            line={"color": COLOR_MAP["accent"], "width": 2.5},
            hovertemplate="CSL: %{x:.1f}%<br>Fill Rate: %{y:.2f}%<extra></extra>",
        )
    )
    fig_cf.update_layout(
        xaxis_title="Cycle Service Level (%)",
        yaxis_title="Service Measure (%)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"t": 20, "b": 50, "l": 60, "r": 20},
        height=360,
        legend={"orientation": "h", "y": -0.22},
        xaxis={"gridcolor": "#F0F0F0"},
        yaxis={"gridcolor": "#F0F0F0"},
    )
    st.plotly_chart(fig_cf, use_container_width=True)
    st.caption(
        f"Example: σ_x = {sigma_demo} units, Q = {q_demo} units. "
        "The gap between fill rate and CSL narrows as variability decreases "
        "or order quantity increases."
    )


# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### What This Model Can and Cannot Do")

    st.markdown(
        f"""
        <div style='background:{COLOR_MAP["card"]};border:1px solid #E5E7EB;
                    border-radius:8px;padding:1.2rem 1.4rem;'>
            <h4 style='color:{COLOR_MAP["primary"]};margin:0 0 0.8rem 0;'>
                ✅ What this tool does well
            </h4>
            <ul style='margin:0;color:{COLOR_MAP["muted"]};'>
                <li>Quantifies the cost impact of demand variability on safety stock</li>
                <li>Compares continuous-review vs periodic-review policies on a common basis</li>
                <li>Identifies the highest-value SKUs for policy review</li>
                <li>Demonstrates how service level targets translate to working capital</li>
                <li>Provides a consistent, formula-based baseline for all 120 SKUs</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(" ")

    st.markdown(
        f"""
        <div style='background:#FEF2F2;border:1px solid {COLOR_MAP["danger"]}33;
                    border-radius:8px;padding:1.2rem 1.4rem;'>
            <h4 style='color:{COLOR_MAP["danger"]};margin:0 0 0.8rem 0;'>
                ⚠️ Known limitations — be honest with stakeholders
            </h4>
            <ul style='margin:0;color:{COLOR_MAP["muted"]};'>
                <li><b>Assumes stationary demand:</b> Seasonal patterns, promotions, or
                    structural shifts are not modelled.</li>
                <li><b>Single-echelon:</b> No multi-tier supply chain or warehouse network effects.</li>
                <li><b>Independent SKUs:</b> Supplier consolidation, joint-replenishment economics,
                    and substitution effects are excluded.</li>
                <li><b>Normal distribution:</b> Lumpy or intermittent demand (Poisson, Gamma)
                    requires different distributional assumptions.</li>
                <li><b>Synthetic data:</b> Parameter values are generated from realistic ranges —
                    actual results will depend on real demand data quality and ERP accuracy.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Assumptions Table")

    assumptions = {
        "Assumption": [
            "Demand distribution",
            "Lead time distribution",
            "Holding cost fraction",
            "Order cost",
            "Target CSL",
            "Criticality segmentation",
            "Backorder treatment",
        ],
        "Value / Model": [
            "Normal (μ_d, σ_d)",
            "Normal (μ_L, σ_L), independent of demand",
            "25% of unit cost per year",
            "$85 fixed per replenishment",
            "97% (configurable in SKU Explorer)",
            "Top 20% spend → Critical; next 50% → Operational; bottom 30% → Standard",
            "Lost sales (not backordered) in simulation",
        ],
        "Sensitivity": [
            "High — non-Normal demand needs Gamma or Poisson SS formula",
            "Moderate — longer σ_L increases SS significantly",
            "Low — linear effect on holding cost",
            "Low — affects EOQ, not SS",
            "High — moving from 95% to 99% roughly doubles SS",
            "Moderate — threshold choice affects tier membership",
            "Low — for planning purposes, both approaches converge at low stockout rates",
        ],
    }
    st.dataframe(assumptions, use_container_width=True, hide_index=True)

st.divider()
render_disclaimer()
