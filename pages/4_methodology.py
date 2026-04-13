"""
Page 4 — Methodology
"The formulas behind the numbers — explained for supply chain practitioners"
Trust builder: shows rigorous understanding without academic lecturing.
"""

import math
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from scipy.stats import norm

from utils.disclaimer import show_banner, show_footer
from utils.colors import PRIMARY, SUCCESS, WARNING, DANGER
from utils.formulas import (
    safety_stock_sQ,
    safety_stock_RS,
    sigma_x_RS,
    fill_rate,
    z_from_csl,
)

st.set_page_config(page_title="Methodology | Inventory Simulator", layout="wide")

show_banner()

st.markdown("# Methodology")
st.markdown(
    "### The formulas behind the numbers — explained for supply chain practitioners"
)
st.caption(
    "This page is the trust builder. Every number in the demo comes from one of these formulas. "
    "All notation is paired with plain-language supply chain equivalents."
)
st.divider()

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "1 · Which policy?",
        "2 · Safety stock formula",
        "3 · Fill rate vs CSL",
        "4 · Step 2 preview",
    ]
)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — Which policy for which SKU?
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## Which inventory policy fits which SKU?")
    st.markdown(
        "Not all parts need the same policy. Using the wrong policy for a SKU "
        "is like wearing the wrong tool for the job — it wastes money or creates risk."
    )

    col_flow, col_table = st.columns([1, 1.4])

    with col_flow:
        st.markdown("### Decision guide")
        st.markdown(
            f"""
            <div style="font-family:monospace;background:#f8f9fa;padding:1.2rem;
                 border-radius:8px;line-height:2.2;font-size:0.95rem;">
            Can you monitor inventory <strong>continuously</strong>?<br>
            &nbsp;&nbsp;├── <strong style="color:{SUCCESS};">YES</strong> →
                Use <strong>(s,Q)</strong><br>
            &nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                Fixed order qty when inventory hits trigger level<br>
            &nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                Best for: expensive, critical, fast-moving parts<br>
            &nbsp;&nbsp;│<br>
            &nbsp;&nbsp;└── <strong style="color:{WARNING};">NO</strong> →
                Use <strong>(R,S)</strong><br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                Order up to S every R weeks<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                Best for: commodity, high-volume, batched ordering
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### PACCAR insight")
        st.info(
            "Use **(s,Q) continuous review** for expensive critical parts — "
            "Turbo Housing, Fuel Injectors — where you need to react immediately "
            "to any demand event.  \n\n"
            "Use **(R,S) periodic review** for commodity parts — Oil Filters, "
            "Brake Pads — where weekly batched ordering reduces transaction costs "
            "without meaningful service-level risk."
        )

    with col_table:
        st.markdown("### Policy comparison")
        comparison_data = {
            "Attribute": [
                "When to order",
                "How much to order",
                "Risk period covered",
                "Safety stock formula",
                "Best for (PACCAR)",
            ],
            "(s,Q) Continuous Review": [
                "When inventory position ≤ ROP (order trigger)",
                "Fixed Q = EOQ (optimal order qty)",
                "Lead time L only",
                "SS = Z × σx,  σx = √(μL·σd² + σL²·μd²)",
                "Turbo Housing, Fuel Injectors, Turbo Bearings",
            ],
            "(R,S) Periodic Review": [
                "Every R weeks (fixed schedule)",
                "Variable: up to order-up-to level S",
                "Review period R + lead time L",
                "SS = Z × σx,  σx = √((μL+R)·σd² + σL²·μd²)",
                "Oil Filters, Brake Pads, Wheel Bearings",
            ],
        }
        import pandas as pd

        comp_df = pd.DataFrame(comparison_data)
        st.dataframe(comp_df.set_index("Attribute"), use_container_width=True)

        st.warning(
            "**Key difference:** (R,S) requires more safety stock than (s,Q) "
            "because between review dates, you have a 'blind spot' — you can't "
            "react to demand drops until the next review. This is the review period R."
        )

    st.divider()
    st.markdown("### Side-by-side numbers — same part, two policies")
    st.caption(
        "Compare safety stock requirement when the same SKU is managed under each policy."
    )

    num_col1, num_col2, num_col3 = st.columns(3)
    with num_col1:
        ex_dm = st.slider("Weekly demand mean (units)", 50, 1000, 200, key="tab1_dm")
    with num_col2:
        ex_cv = st.slider("Demand CV", 0.10, 0.80, 0.30, key="tab1_cv")
    with num_col3:
        ex_lt = st.slider("Lead time (weeks)", 1, 14, 4, key="tab1_lt")

    ex_ds = ex_dm * ex_cv
    ex_lt_s = ex_lt * 0.15
    z_95 = z_from_csl(0.95)

    ss_sQ_ex = safety_stock_sQ(z_95, ex_dm, ex_ds, ex_lt, ex_lt_s)
    ss_RS1_ex = safety_stock_RS(z_95, ex_dm, ex_ds, ex_lt, ex_lt_s, 1)
    ss_RS2_ex = safety_stock_RS(z_95, ex_dm, ex_ds, ex_lt, ex_lt_s, 2)

    e1, e2, e3 = st.columns(3)
    with e1:
        st.metric(
            "(s,Q) Safety stock",
            f"{ss_sQ_ex:.0f} units",
            help="No review period penalty",
        )
    with e2:
        st.metric(
            "(R,S) R=1wk Safety stock",
            f"{ss_RS1_ex:.0f} units",
            delta=f"+{ss_RS1_ex - ss_sQ_ex:.0f} vs (s,Q)",
            delta_color="inverse",
        )
    with e3:
        st.metric(
            "(R,S) R=2wk Safety stock",
            f"{ss_RS2_ex:.0f} units",
            delta=f"+{ss_RS2_ex - ss_sQ_ex:.0f} vs (s,Q)",
            delta_color="inverse",
        )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — How is safety stock calculated?
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## How is safety stock calculated?")
    st.markdown(
        "We build the formula in three steps, adding one layer of real-world "
        "complexity at a time. Each step uses sliders so you can see the numbers move."
    )

    # ── Interactive sliders ──
    s2col1, s2col2, s2col3, s2col4 = st.columns(4)
    with s2col1:
        s2_dm = st.slider("Weekly demand mean", 20, 1000, 200, key="s2_dm")
    with s2col2:
        s2_cv = st.slider("Demand CV (σd/μd)", 0.05, 1.0, 0.25, key="s2_cv")
    with s2col3:
        s2_lt = st.slider("Lead time μL (weeks)", 1, 16, 5, key="s2_lt")
    with s2col4:
        s2_lt_s = st.slider("Lead time σL (weeks)", 0.0, 5.0, 1.0, key="s2_lt_s")

    s2_ds = s2_dm * s2_cv
    z_val = z_from_csl(0.95)
    rp_ex = 2  # for step 2 demo

    # ── Step 1 — Fixed LT, steady demand ──
    st.markdown("---")
    st.markdown("### Step 1 — Textbook formula (fixed lead time, no variability)")

    s1col, s1explain = st.columns([1, 1.3])
    with s1col:
        ss_step1 = z_val * s2_ds * math.sqrt(s2_lt)
        st.latex(r"SS = Z_\alpha \cdot \sigma_d \cdot \sqrt{L}")
        st.latex(
            rf"SS = {z_val:.3f} \cdot {s2_ds:.1f} \cdot \sqrt{{{s2_lt}}} "
            rf"= \mathbf{{{ss_step1:.0f} \text{{ units}}}}"
        )
    with s1explain:
        st.markdown(
            f"""
            <div style="background:#f0f4fa;border-left:4px solid {PRIMARY};
                 padding:1rem;border-radius:0 8px 8px 0;">
            <strong>Z</strong> = {z_val:.3f} — the protection factor for 95% CSL.
            Higher targets require exponentially more buffer stock.<br><br>
            <strong>σd</strong> = {s2_ds:.1f} units/week — how variable your weekly demand is.<br><br>
            <strong>√L</strong> = √{s2_lt} = {math.sqrt(s2_lt):.2f} —
            variability scales with the square root of the replenishment time.
            Longer lead times = more uncertainty = more buffer.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Step 2 — Add review period ──
    st.markdown("---")
    st.markdown("### Step 2 — Add ordering frequency (periodic review blind spot)")

    s2col_f, s2col_e = st.columns([1, 1.3])
    with s2col_f:
        ss_step2 = z_val * s2_ds * math.sqrt(s2_lt + rp_ex)
        st.latex(r"SS = Z_\alpha \cdot \sigma_d \cdot \sqrt{L + R}")
        st.latex(
            rf"SS = {z_val:.3f} \cdot {s2_ds:.1f} \cdot \sqrt{{{s2_lt} + {rp_ex}}} "
            rf"= \mathbf{{{ss_step2:.0f} \text{{ units}}}}"
        )
        st.metric(
            "Extra buffer for review period",
            f"+{ss_step2 - ss_step1:.0f} units",
            delta="vs Step 1",
            delta_color="inverse",
        )
    with s2col_e:
        st.markdown(
            f"""
            <div style="background:#fff9f0;border-left:4px solid {WARNING};
                 padding:1rem;border-radius:0 8px 8px 0;">
            Adding the <strong>review period R = {rp_ex} weeks</strong> extends the
            risk window. Between review dates, you cannot react to demand spikes.<br><br>
            This "blind spot" adds {rp_ex} weeks of uncertainty to your buffer requirement —
            costing an extra <strong>{ss_step2 - ss_step1:.0f} units</strong> of safety stock.<br><br>
            This is why (s,Q) continuous review is preferred for expensive parts —
            it eliminates the review period penalty entirely.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Step 3 — Full PACCAR formula with σL ──
    st.markdown("---")
    st.markdown(
        "### Step 3 — Full formula: add lead time variability σL (the PACCAR factor)"
    )

    sx_full = sigma_x_RS(s2_dm, s2_ds, s2_lt, s2_lt_s, rp_ex)
    ss_step3 = z_val * sx_full

    s3col_f, s3col_e = st.columns([1, 1.3])
    with s3col_f:
        st.latex(
            r"\sigma_x = \sqrt{(\mu_L + R) \cdot \sigma_d^2 + \sigma_L^2 \cdot \mu_d^2}"
        )
        st.latex(r"SS = Z_\alpha \cdot \sigma_x")
        st.latex(
            rf"\sigma_x = \sqrt{{({s2_lt} + {rp_ex}) \cdot {s2_ds:.1f}^2 "
            rf"+ {s2_lt_s:.1f}^2 \cdot {s2_dm:.1f}^2}} = {sx_full:.1f}"
        )
        st.latex(
            rf"SS = {z_val:.3f} \cdot {sx_full:.1f} = \mathbf{{{ss_step3:.0f} \text{{ units}}}}"
        )
    with s3col_e:
        lt_var_contribution = s2_lt_s**2 * s2_dm**2
        demand_var_contribution = (s2_lt + rp_ex) * s2_ds**2
        total_var = lt_var_contribution + demand_var_contribution
        lt_pct = lt_var_contribution / max(total_var, 0.01) * 100

        st.markdown(
            f"""
            <div style="background:#f0faf6;border-left:4px solid {SUCCESS};
                 padding:1rem;border-radius:0 8px 8px 0;">
            Now <strong>σL = {s2_lt_s:.1f} weeks</strong> (lead time variability)
            enters the formula as the second term.<br><br>
            Lead time variability contributes
            <strong>{lt_pct:.0f}%</strong> of total demand uncertainty σx².<br><br>
            For PACCAR's international supply chains, where parts ship from
            Asia with ±{s2_lt_s:.0f}-week delivery windows, this term can
            <em>dominate</em> the safety stock calculation.<br><br>
            Most traditional planners ignore σL entirely — this is the
            single biggest source of systematic under-stocking on long-LT parts.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Sensitivity chart — SS vs σL ──
    st.markdown("---")
    st.markdown("### Sensitivity: how lead time variability drives safety stock")
    lt_s_range = np.linspace(0, 4, 50)
    ss_range = [z_val * sigma_x_RS(s2_dm, s2_ds, s2_lt, ls, rp_ex) for ls in lt_s_range]

    fig_sens = go.Figure()
    fig_sens.add_trace(
        go.Scatter(
            x=lt_s_range,
            y=ss_range,
            line=dict(color=PRIMARY, width=2.5),
            fill="tozeroy",
            fillcolor="rgba(24, 95, 165, 0.1)",
            name="Safety stock requirement",
        )
    )
    fig_sens.add_vline(
        x=s2_lt_s,
        line_dash="dash",
        line_color=WARNING,
        annotation_text=f"Current σL = {s2_lt_s:.1f} wks → SS = {ss_step3:.0f}",
        annotation_position="top right",
        annotation_font_color=WARNING,
    )
    fig_sens.update_layout(
        title="Safety stock vs. lead time variability σL — same demand, R=2 weeks",
        xaxis_title="Lead time std dev σL (weeks)",
        yaxis_title="Safety stock (units)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        template="plotly_white",
        height=360,
    )
    st.plotly_chart(fig_sens, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — Fill rate vs CSL
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Fill rate vs. service level — what's the difference?")
    st.markdown(
        "These two metrics both sound like 'how well are we serving demand?' "
        "but they measure very different things — and confusing them leads to "
        "either costly over-stocking or surprising service failures."
    )

    # ── Interactive SS slider ──
    t3col1, t3col2, t3col3 = st.columns(3)
    with t3col1:
        t3_dm = st.slider("Weekly demand mean", 50, 500, 150, key="t3_dm")
    with t3col2:
        t3_cv = st.slider("Demand CV", 0.10, 0.80, 0.30, key="t3_cv")
    with t3col3:
        t3_lt = st.slider("Lead time (weeks)", 1, 12, 4, key="t3_lt")

    t3_ds = t3_dm * t3_cv
    t3_lt_s = t3_lt * 0.15
    t3_sx = sigma_x_RS(t3_dm, t3_ds, t3_lt, t3_lt_s, 1)
    t3_cd = t3_dm * (t3_lt + 1)  # cycle demand

    ss_values = np.linspace(0, t3_sx * 3.5, 200)
    z_values = ss_values / np.maximum(t3_sx, 1e-6)
    csl_curve = norm.cdf(z_values)
    fr_curve = np.array([fill_rate(ss, t3_sx, t3_cd) for ss in ss_values])

    fig_comp = go.Figure()
    fig_comp.add_trace(
        go.Scatter(
            x=ss_values,
            y=csl_curve * 100,
            name="Cycle Service Level (CSL)",
            line=dict(color=PRIMARY, width=2.5),
        )
    )
    fig_comp.add_trace(
        go.Scatter(
            x=ss_values,
            y=fr_curve * 100,
            name="Fill Rate (β)",
            line=dict(color=SUCCESS, width=2.5, dash="dash"),
        )
    )

    # Mark 95% CSL point
    ss_95 = z_from_csl(0.95) * t3_sx
    fr_at_95 = fill_rate(ss_95, t3_sx, t3_cd)

    fig_comp.add_vline(
        x=ss_95,
        line_dash="dot",
        line_color=WARNING,
        annotation_text=f"SS for 95% CSL = {ss_95:.0f} units",
        annotation_font_color=WARNING,
    )
    fig_comp.add_annotation(
        x=ss_95 * 1.1,
        y=fr_at_95 * 100,
        text=f"Fill rate at same SS: {fr_at_95 * 100:.1f}%",
        showarrow=True,
        arrowhead=2,
        font=dict(color=SUCCESS, size=11),
    )

    fig_comp.update_layout(
        title="CSL vs. Fill Rate — same safety stock, very different numbers",
        xaxis_title="Safety stock (units)",
        yaxis_title="Service metric (%)",
        yaxis_range=[60, 101],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # ── Two metric boxes ──
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(
            f"""
            <div style="background:#f0f4fa;border:2px solid {PRIMARY};border-radius:10px;
                 padding:1.5rem;text-align:center;">
            <h3 style="color:{PRIMARY};margin:0;">Cycle Service Level (CSL)</h3>
            <h4 style="color:{PRIMARY};">{norm.cdf(z_from_csl(0.95)) * 100:.1f}%</h4>
            <p style="color:#444;margin:0;">
            Probability that <strong>no stock-out occurs</strong>
            during a single replenishment cycle.<br><br>
            Think of it as: "How often do we get through a cycle
            without running out?"
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div style="background:#f0faf6;border:2px solid {SUCCESS};border-radius:10px;
                 padding:1.5rem;text-align:center;">
            <h3 style="color:{SUCCESS};margin:0;">Fill Rate (β)</h3>
            <h4 style="color:{SUCCESS};">{fr_at_95 * 100:.1f}%</h4>
            <p style="color:#444;margin:0;">
            Percentage of total demand <strong>served directly from stock</strong>
            — no backorders, no lost sales.<br><br>
            Think of it as: "What fraction of orders do we fill immediately?"
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.warning(
        f"**Key insight:** The same safety stock ({ss_95:.0f} units) achieves "
        f"**95.0% CSL** but **{fr_at_95 * 100:.1f}% fill rate**. "
        f"Most PACCAR planners track fill rate in their KPIs — but if your safety "
        f"stock formula targets CSL, you may be significantly over-stocking. "
        f"**Always match your formula to the metric you report.**"
    )

    st.markdown("### The Normal Loss Function — why fill rate stays high")
    st.latex(r"L(z) = \varphi(z) - z \cdot (1 - \Phi(z))")
    st.latex(r"\beta = 1 - \frac{\sigma_x}{d_c} \cdot L(z)")
    st.markdown(
        "The Normal Loss Function L(z) measures *expected units short per unit of σx*. "
        "Because L(z) shrinks very rapidly as z increases past 1.0, fill rate "
        "approaches 100% quickly. **Going from 95% → 99% fill rate requires far "
        "more safety stock than going from 80% → 95%.**"
    )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — Step 2 Preview
# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## Step 2 Preview: When formulas aren't enough")
    st.markdown(
        "The formula approach in this demo is rigorous and fast. "
        "But three real-world situations break its assumptions. "
        "Step 2 addresses all three."
    )

    lim1, lim2, lim3 = st.columns(3)

    with lim1:
        st.markdown(
            f"""
            <div style="border-left:5px solid {DANGER};background:#fef0f0;
                 padding:1.2rem;border-radius:0 10px 10px 0;height:260px;">
            <h4 style="color:{DANGER};margin-top:0;">⚠️ Limitation 1<br>Normal distribution</h4>
            <p>Formulas assume demand follows a Normal (bell curve) distribution.</p>
            <p>For <strong>lumpy / intermittent SKUs</strong> — Turbo Housing,
            Fuel Injectors — demand is zero most weeks and spikes unpredictably.</p>
            <p>The Normal assumption <em>systematically underestimates</em>
            safety stock for these critical parts.</p>
            <strong style="color:{DANGER};">Fix: KDE-based custom distribution (Step 2)</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with lim2:
        st.markdown(
            f"""
            <div style="border-left:5px solid {WARNING};background:#fff9f0;
                 padding:1.2rem;border-radius:0 10px 10px 0;height:260px;">
            <h4 style="color:{WARNING};margin-top:0;">⚠️ Limitation 2<br>No backlog dynamics</h4>
            <p>Formulas compute a <em>static</em> buffer. They can't simulate how
            unfilled demand accumulates as backlog, inflating future orders.</p>
            <p>In a production environment, a two-week stock-out on a critical
            fastener doesn't just delay 2 weeks — it ripples through the
            assembly schedule.</p>
            <strong style="color:{WARNING};">Fix: Monte Carlo simulation with backlog tracking (Step 2)</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with lim3:
        st.markdown(
            f"""
            <div style="border-left:5px solid {PRIMARY};background:#f0f4fa;
                 padding:1.2rem;border-radius:0 10px 10px 0;height:260px;">
            <h4 style="color:{PRIMARY};margin-top:0;">⚠️ Limitation 3<br>No joint optimization</h4>
            <p>Formulas treat the review period R as fixed input.
            But the optimal R depends on safety stock, which depends on R — a
            circular dependency only simulation can resolve.</p>
            <p>Step 2 searches both R and SS simultaneously to find
            the global cost minimum.</p>
            <strong style="color:{PRIMARY};">Fix: Bidirectional sim-opt (Vandeput Ch. 13, Method #2)</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("### Step 2 — planned architecture")

    st.markdown(
        f"""
        <div style="background:#f0faf6;border:2px solid {SUCCESS};border-radius:10px;
             padding:1.5rem;max-width:800px;">
        <h4 style="color:{SUCCESS};margin-top:0;">🔬 Simulation-Optimization Engine (Step 2)</h4>
        <table style="width:100%;border-collapse:collapse;">
          <tr style="border-bottom:1px solid #ddd;">
            <td style="padding:8px;"><strong>Demand modeling</strong></td>
            <td style="padding:8px;">KDE-based custom distributions per SKU
                                    (handles lumpy, intermittent, bimodal)</td>
          </tr>
          <tr style="border-bottom:1px solid #ddd;">
            <td style="padding:8px;"><strong>Lead time modeling</strong></td>
            <td style="padding:8px;">Empirical distribution from 3 years of
                                    ERP goods-receipt records</td>
          </tr>
          <tr style="border-bottom:1px solid #ddd;">
            <td style="padding:8px;"><strong>Simulation engine</strong></td>
            <td style="padding:8px;">10,000 × 52-week Monte Carlo paths per SKU,
                                    vectorized NumPy</td>
          </tr>
          <tr style="border-bottom:1px solid #ddd;">
            <td style="padding:8px;"><strong>Optimization method</strong></td>
            <td style="padding:8px;">Bidirectional safety stock search
                                    [Vandeput 2020, Ch. 13, Method 2]</td>
          </tr>
          <tr style="border-bottom:1px solid #ddd;">
            <td style="padding:8px;"><strong>Forecast integration</strong></td>
            <td style="padding:8px;">XGBoost bias-corrected demand forecasts
                                    replace historical mean</td>
          </tr>
          <tr>
            <td style="padding:8px;"><strong>Scale</strong></td>
            <td style="padding:8px;">Full 8,000-SKU PACCAR portfolio,
                                    parallelized per DC</td>
          </tr>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "→ **Next: Business Case** — the executive summary of what this "
        "delivers in dollars, suitable for a leadership conversation."
    )

show_footer(
    [
        "Formulas: Vandeput (2020) Chapters 4–8",
        "Fill rate model: Chapter 7, eq. 7.3",
        "Step 2 methodology: Chapter 13",
    ]
)
