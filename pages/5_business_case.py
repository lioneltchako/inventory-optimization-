"""
Page 5 — Business Case
"The bottom line — what this delivers for DynaCraft / PACCAR"
Print-friendly executive summary with PDF export.
"""

import io
import datetime
import streamlit as st
import pandas as pd

from utils.disclaimer import show_banner, show_footer
from utils.colors import PRIMARY, SUCCESS, NEUTRAL
from utils.portfolio_data import portfolio_summary, PORTFOLIO_DF

st.set_page_config(page_title="Business Case | Inventory Simulator", layout="wide")

show_banner()

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="text-align:center;max-width:900px;margin:0 auto;">
    <h1 style="color:{PRIMARY};">Inventory Policy Simulator</h1>
    <h3 style="color:#444;">DynaCraft / PACCAR — Senior Demand Planner Demo</h3>
    <p style="color:#666;">
    Impact of optimized inventory policies across a 120-SKU synthetic portfolio<br>
    <strong>Step 1 of 2 — Formula-based estimates (~)</strong> ·
    {datetime.date.today().strftime("%B %d, %Y")}
    </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ── COMPUTE KPIS ──────────────────────────────────────────────────────────────
kpis = portfolio_summary(PORTFOLIO_DF)

total_ss_base = kpis["ss_value_base"]
total_ss_ml = kpis["ss_value_ml"]
ss_saving = total_ss_base - total_ss_ml
ss_delta_pct = kpis["ss_delta_pct"]

hold_base = kpis["hold_cost_base"]
hold_ml = kpis["hold_cost_ml"]
order_base = kpis["order_cost_base"]
order_ml = kpis["order_cost_ml"]
total_base = kpis["total_cost_base"]
total_ml = kpis["total_cost_ml"]
annual_saving = kpis["annual_saving"]

fr_base = kpis["avg_fill_rate_base"]
fr_ml = kpis["avg_fill_rate_ml"]
fr_delta = fr_ml - fr_base

# CSL is fixed at 95% for portfolio
csl_base = 95.0
csl_ml = 95.0

n_skus = kpis["n_skus"]

# ── SUMMARY TABLE ─────────────────────────────────────────────────────────────
st.markdown("### Summary — 120-SKU synthetic portfolio impact")

summary_data = {
    "Metric": [
        "Total safety stock value ($)",
        "Annual holding cost ($)",
        "Annual ordering cost ($)",
        "Total annual inventory cost ($)",
        "Average fill rate (%)",
        "Cycle service level (target CSL)",
    ],
    "Baseline": [
        f"~${total_ss_base:,.0f}",
        f"~${hold_base:,.0f}",
        f"~${order_base:,.0f}",
        f"~${total_base:,.0f}",
        f"~{fr_base:.1f}%",
        f"~{csl_base:.1f}%",
    ],
    "ML + Optimized": [
        f"~${total_ss_ml:,.0f}",
        f"~${hold_ml:,.0f}",
        f"~${order_ml:,.0f}",
        f"~${total_ml:,.0f}",
        f"~{fr_ml:.1f}%",
        f"~{csl_ml:.1f}%",
    ],
    "Δ (improvement)": [
        f"−${ss_saving:,.0f} ({ss_delta_pct:.1f}%)",
        f"−${hold_base - hold_ml:,.0f}",
        f"−${order_base - order_ml:,.0f}",
        f"−${annual_saving:,.0f}",
        f"+{fr_delta:.1f} pp",
        "unchanged",
    ],
}

summary_df = pd.DataFrame(summary_data)


# Style: highlight the Delta column
def style_summary(df: pd.DataFrame) -> pd.DataFrame:
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    styles["Δ (improvement)"] = f"color:{SUCCESS}; font-weight:bold;"
    styles.iloc[-1, -1] = f"color:{NEUTRAL}; font-weight:normal;"
    return styles


styled_summary = summary_df.style.apply(style_summary, axis=None)
st.dataframe(styled_summary, use_container_width=True, hide_index=True)
st.divider()

# ── THREE INSIGHT BOXES ───────────────────────────────────────────────────────
st.markdown("### Key business impacts")

box1, box2, box3 = st.columns(3)

# Rough benchmark: DC operating cost ~$2M/year for a mid-size PACCAR DC
dc_operating_cost_weekly = 2_000_000 / 52

with box1:
    weeks_equiv = (
        ss_saving / dc_operating_cost_weekly if dc_operating_cost_weekly > 0 else 0
    )
    st.markdown(
        f"""
        <div style="background:#f0faf6;border:2px solid {SUCCESS};border-radius:10px;
             padding:1.5rem;text-align:center;height:220px;">
        <h3 style="color:{SUCCESS};margin:0 0 0.5rem;">💰 Safety Stock Capital Freed</h3>
        <h2 style="color:{SUCCESS};margin:0;">~${ss_saving:,.0f}</h2>
        <p style="color:#444;margin:0.5rem 0 0;">{ss_delta_pct:.1f}% of baseline safety stock</p>
        <hr style="border-color:#1D9E75;opacity:0.3;">
        <p style="color:#555;margin:0;font-size:0.9rem;">
        Equivalent to ~{weeks_equiv:.1f} weeks of DC operating costs
        (benchmark: $2M/year DC)
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with box2:
    st.markdown(
        f"""
        <div style="background:#f0f4fa;border:2px solid {PRIMARY};border-radius:10px;
             padding:1.5rem;text-align:center;height:220px;">
        <h3 style="color:{PRIMARY};margin:0 0 0.5rem;">📉 Annual Cost Reduction</h3>
        <h2 style="color:{PRIMARY};margin:0;">~${annual_saving:,.0f}</h2>
        <p style="color:#444;margin:0.5rem 0 0;">Holding + ordering cost improvement</p>
        <hr style="border-color:#185FA5;opacity:0.3;">
        <p style="color:#555;margin:0;font-size:0.9rem;">
        Across {n_skus} SKUs with formula-optimized policies.<br>
        Fill rate improves +{fr_delta:.1f} pp with the same service target.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with box3:
    # Step 2 teaser: estimate additional 15-25% on residual SS
    step2_low = total_ss_ml * 0.15
    step2_high = total_ss_ml * 0.25
    st.markdown(
        f"""
        <div style="background:#e8f7f4;border:2px solid {SUCCESS};border-radius:10px;
             padding:1.5rem;text-align:center;height:220px;">
        <h3 style="color:{SUCCESS};margin:0 0 0.5rem;">🚀 Step 2 Potential</h3>
        <h2 style="color:{SUCCESS};margin:0;">+~${step2_low:,.0f}–${step2_high:,.0f}</h2>
        <p style="color:#444;margin:0.5rem 0 0;">Estimated additional reduction</p>
        <hr style="border-color:#1D9E75;opacity:0.3;">
        <p style="color:#555;margin:0;font-size:0.9rem;">
        Full 8,000-SKU Monte Carlo simulation-optimization<br>
        (Vandeput Ch. 13) — additional −15–25% on residual safety stock
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── ASSUMPTIONS ───────────────────────────────────────────────────────────────
with st.expander("Assumptions and methodology notes", expanded=False):
    st.markdown(
        f"""
        | Parameter | Value | Basis |
        |-----------|-------|-------|
        | Portfolio size | {n_skus} SKUs | Synthetic PACCAR-like (~) |
        | Target CSL | 95% | Standard benchmark |
        | Baseline forecast bias | +10% demand overestimate | Typical without ML (~) |
        | Baseline demand σ inflation | +20% | Without bias correction (~) |
        | ML demand σ reduction | −20% | Post-ML forecast improvement (~) |
        | Holding cost rate | 25–30% p.a. | Industry benchmark (~) |
        | Order cost | $200–$2,500 | By family (~) |
        | Unit cost range | $8–$1,800 | Log-normal, seed=42 (~) |
        | Safety stock formula | Vandeput (2020) eq. 6.4–6.5 | |
        | Fill rate formula | Vandeput (2020) eq. 7.3 | |

        **All KPIs labeled ~ are approximated from synthetic parameters.**
        Real results require actual demand data, ERP integration, and
        calibrated holding/ordering costs.
        """
    )

st.divider()

# ── PDF EXPORT ────────────────────────────────────────────────────────────────
st.markdown("### Download executive one-pager")


def generate_pdf() -> bytes:
    """Generate a clean single-page PDF with key findings."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.lib import colors as rl_colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.lib.enums import TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Color constants for PDF
        BLUE = rl_colors.HexColor("#185FA5")
        TEAL = rl_colors.HexColor("#1D9E75")
        GRAY = rl_colors.HexColor("#888780")
        LGRAY = rl_colors.HexColor("#f8f9fa")
        BLACK = rl_colors.black

        styles_h1 = ParagraphStyle(
            "H1",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=BLUE,
            alignment=TA_CENTER,
            spaceAfter=4,
        )
        styles_h2 = ParagraphStyle(
            "H2",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=BLUE,
            alignment=TA_CENTER,
            spaceAfter=2,
        )
        styles_sub = ParagraphStyle(
            "Sub",
            fontName="Helvetica",
            fontSize=10,
            textColor=GRAY,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        styles_body = ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=10,
            textColor=BLACK,
            spaceAfter=6,
        )
        styles_label = ParagraphStyle(
            "Label",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=TEAL,
            spaceAfter=2,
        )

        story = []

        # Header
        story.append(Paragraph("Inventory Policy Simulator", styles_h1))
        story.append(
            Paragraph("DynaCraft / PACCAR — Senior Demand Planner Demo", styles_h2)
        )
        story.append(
            Paragraph(
                f"Step 1 of 2 · Formula-based estimates (~) · "
                f"{datetime.date.today().strftime('%B %d, %Y')}",
                styles_sub,
            )
        )

        # Summary table
        table_data = [
            ["Metric", "Baseline", "ML + Optimized", "Δ (improvement)"],
            [
                "Total safety stock ($)",
                f"~${total_ss_base:,.0f}",
                f"~${total_ss_ml:,.0f}",
                f"−${ss_saving:,.0f} ({ss_delta_pct:.1f}%)",
            ],
            [
                "Annual holding cost ($)",
                f"~${hold_base:,.0f}",
                f"~${hold_ml:,.0f}",
                f"−${hold_base - hold_ml:,.0f}",
            ],
            [
                "Annual ordering cost ($)",
                f"~${order_base:,.0f}",
                f"~${order_ml:,.0f}",
                f"−${order_base - order_ml:,.0f}",
            ],
            [
                "Total annual cost ($)",
                f"~${total_base:,.0f}",
                f"~${total_ml:,.0f}",
                f"−${annual_saving:,.0f}",
            ],
            [
                "Average fill rate",
                f"~{fr_base:.1f}%",
                f"~{fr_ml:.1f}%",
                f"+{fr_delta:.1f} pp",
            ],
        ]

        col_widths = [2.5 * inch, 1.3 * inch, 1.3 * inch, 1.8 * inch]
        tbl = Table(table_data, colWidths=col_widths)
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                    ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LGRAY, rl_colors.white]),
                    ("TEXTCOLOR", (3, 1), (3, -2), TEAL),
                    ("FONTNAME", (3, 1), (3, -2), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, GRAY),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(tbl)
        story.append(Spacer(1, 0.25 * inch))

        # Key insights
        insights = [
            (
                "Safety stock capital freed",
                f"~${ss_saving:,.0f} ({ss_delta_pct:.1f}% reduction)",
                f"Equivalent to ~{ss_saving / dc_operating_cost_weekly:.1f} weeks DC operating costs",
            ),
            (
                "Annual cost reduction",
                f"~${annual_saving:,.0f} / year",
                f"Across {n_skus} SKUs with optimized policies",
            ),
            (
                "Step 2 potential (planned)",
                "−15–25% additional on residual SS",
                "Full 8,000-SKU Monte Carlo sim-opt (Vandeput Ch. 13)",
            ),
        ]

        insight_rows = [
            [
                Paragraph(t, styles_label),
                Paragraph(
                    v,
                    ParagraphStyle(
                        "V", fontName="Helvetica-Bold", fontSize=11, textColor=BLUE
                    ),
                ),
                Paragraph(d, styles_body),
            ]
            for t, v, d in insights
        ]

        itbl = Table(insight_rows, colWidths=[2.3 * inch, 2.0 * inch, 2.6 * inch])
        itbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), rl_colors.HexColor("#f0faf6")),
                    ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.HexColor("#1D9E75")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(itbl)
        story.append(Spacer(1, 0.25 * inch))

        # Footer
        footer_text = (
            "All KPIs approximated (~) from synthetic PACCAR-like parameters. "
            "Methodology: Vandeput (2020) Inventory Optimization: Models and Simulations. "
            "Step 2 requires real demand data and ERP integration."
        )
        story.append(
            Paragraph(
                footer_text,
                ParagraphStyle(
                    "Footer",
                    fontName="Helvetica",
                    fontSize=8,
                    textColor=GRAY,
                    alignment=TA_CENTER,
                ),
            )
        )

        doc.build(story)
        return buffer.getvalue()

    except ImportError:
        return b""


pdf_bytes = generate_pdf()

if pdf_bytes:
    st.download_button(
        label="⬇ Download one-pager (PDF)",
        data=pdf_bytes,
        file_name=f"paccar_inventory_optimizer_step1_{datetime.date.today().isoformat()}.pdf",
        mime="application/pdf",
    )
else:
    st.info("PDF export requires reportlab. Install with: `pip install reportlab`")

st.divider()

st.info(
    "**This demo (Step 1)** uses direct formula calculations from Vandeput (2020). "
    "**Step 2** will replace these with full Monte Carlo simulation-optimization "
    "(Vandeput Ch. 13) applied to real demand data — handling lumpy demand, "
    "stochastic lead times, and simultaneous policy parameter optimization "
    "across the full 8,000-SKU PACCAR portfolio."
)

show_footer(
    [
        "All KPIs approximated (~) from synthetic PACCAR-like parameters",
        "Methodology: Vandeput (2020)",
        "Step 2 requires real demand data and ERP integration to produce actionable results",
    ]
)
