"""
Page 1 — Overview: "The Problem & The Tool"
Why inventory optimization matters at PACCAR, and what this simulator does.
"""

import streamlit as st
from utils.disclaimer import show_banner, show_footer
from utils.colors import PRIMARY, SUCCESS, WARNING, DANGER

st.set_page_config(page_title="Overview | Inventory Simulator", layout="wide")

show_banner()

st.markdown("# The Problem & The Tool")
st.markdown("### Why inventory optimization matters at DynaCraft / PACCAR")
st.divider()

# ── SECTION 1 — The cost of getting inventory wrong ──────────────────────────
st.markdown("## The cost of getting inventory wrong")

col_stats, col_modes = st.columns([1, 1.3])

with col_stats:
    st.metric(
        label="Active SKUs — DynaCraft portfolio scope",
        value="~8,000",
        help="Dynacraft division active parts across multiple distribution centers",
    )
    st.metric(
        label="Typical inventory carrying cost",
        value="~25% of revenue",
        help="Industry benchmark: includes capital cost, storage, obsolescence, insurance",
    )
    st.metric(
        label="Estimated cost of one stock-out on a critical part",
        value="~$500K / event",
        delta="-production line stops",
        delta_color="inverse",
        help="Includes emergency freight, line-down penalties, expediting costs (~)",
    )

with col_modes:
    st.markdown("#### The two failure modes in inventory")

    st.markdown(
        f"""
        <div style="border-left:4px solid {WARNING};background:#fff9f0;
             padding:1rem;border-radius:0 8px 8px 0;margin-bottom:1rem;">
        <strong style="color:{WARNING};">📦 Too much stock</strong><br>
        Working capital is locked up in warehouses that can't earn a return.
        As trucks evolve, older parts become obsolete — a slow write-down
        that quietly erodes margin. PACCAR's 8,000-SKU breadth makes this
        risk especially large.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="border-left:4px solid {DANGER};background:#fef0f0;
             padding:1rem;border-radius:0 8px 8px 0;margin-bottom:1rem;">
        <strong style="color:{DANGER};">⚠️ Too little stock</strong><br>
        A production line waits for one missing fuel injector.
        Emergency air freight, premium labor costs, and customer penalties
        can exceed $500K in a single event — many times the cost of
        carrying a few extra units.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="border-left:4px solid {PRIMARY};background:#f0f4fa;
             padding:1rem;border-radius:0 8px 8px 0;">
        <strong style="color:{PRIMARY};">🎯 The optimizer's job</strong><br>
        This simulator shows how <strong>inventory policy choices</strong>
        directly control which failure mode you fall into —
        and by how much.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── SECTION 2 — Before / After ────────────────────────────────────────────────
st.markdown("## What this tool does — before vs. after")

col_before, col_after = st.columns(2)

with col_before:
    st.markdown(
        f"""
        <div style="border:2px solid {WARNING};border-radius:10px;padding:1.2rem;">
        <h4 style="color:{WARNING};margin-top:0;">⏮ Before — Common practice</h4>
        <ul style="margin:0;padding-left:1.2rem;line-height:2;">
          <li>Fixed days-of-cover rules applied uniformly</li>
          <li>Safety stock set manually — "gut feel" or spreadsheet</li>
          <li>Same policy for all 8,000 SKUs regardless of behavior</li>
          <li>Forecast bias silently inflates safety stock estimates</li>
          <li>Lead time variability (σL) ignored</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_after:
    st.markdown(
        f"""
        <div style="border:2px solid {SUCCESS};border-radius:10px;padding:1.2rem;">
        <h4 style="color:{SUCCESS};margin-top:0;">✅ After — This simulator</h4>
        <ul style="margin:0;padding-left:1.2rem;line-height:2;">
          <li>Formula-driven safety stock — policy matched to SKU behavior</li>
          <li>Demand variability (σd) AND lead time variability (σL) both modeled</li>
          <li>(s,Q) continuous review for critical / expensive parts</li>
          <li>(R,S) periodic review for commodity parts with batched ordering</li>
          <li>ML forecast quality directly reduces safety stock needs</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── SECTION 3 — Two-step plan ─────────────────────────────────────────────────
st.markdown("## The two-step plan")

col_s1, col_s2 = st.columns(2)

with col_s1:
    st.markdown(
        f"""
        <div style="border-left:5px solid {PRIMARY};background:#f0f4fa;
             padding:1.2rem 1.5rem;border-radius:0 10px 10px 0;">
        <h4 style="color:{PRIMARY};margin-top:0;">Step 1 — This demo</h4>
        <p><strong>Formula-based simulator</strong></p>
        <ul style="padding-left:1.2rem;line-height:1.8;">
          <li>6 pre-built PACCAR SKU profiles</li>
          <li>120-SKU synthetic portfolio</li>
          <li>Policy comparison: (s,Q) vs (R,S)</li>
          <li>Forecast quality impact on safety stock</li>
          <li>Vandeput (2020) methodology, Chapters 1–8</li>
        </ul>
        <em style="color:{PRIMARY};">→ Shows the methodology, quantifies the opportunity</em>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_s2:
    st.markdown(
        f"""
        <div style="border-left:5px solid {SUCCESS};background:#f0faf6;
             padding:1.2rem 1.5rem;border-radius:0 10px 10px 0;">
        <h4 style="color:{SUCCESS};margin-top:0;">Step 2 — Planned</h4>
        <p><strong>ML-powered simulation-optimization engine</strong></p>
        <ul style="padding-left:1.2rem;line-height:1.8;">
          <li>Full 8,000-SKU PACCAR portfolio</li>
          <li>Monte Carlo demand simulation (KDE / custom distributions)</li>
          <li>Bidirectional safety stock search (Vandeput Ch. 13)</li>
          <li>XGBoost forecast integration — bias-corrected demand</li>
          <li>Simultaneous policy parameter optimization</li>
        </ul>
        <em style="color:{SUCCESS};">→ Actionable recommendations ready for ERP integration</em>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

st.info(
    "→ **Next: SKU Explorer** — pick a specific PACCAR part, choose a policy, "
    "and see exactly how forecast quality and policy choice combine to determine "
    "your safety stock and annual costs."
)

show_footer(
    [
        "Methodology: Vandeput (2020) Inventory Optimization, Chapters 1–8",
        "Costs are synthetic PACCAR-like estimates (~)",
    ]
)
