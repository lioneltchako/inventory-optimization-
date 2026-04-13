"""PDF executive-summary generator using reportlab."""

from __future__ import annotations

import io
from datetime import date

from reportlab.lib import colors as rl_colors  # type: ignore[import-untyped]
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.lib.styles import (  # type: ignore[import-untyped]
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import inch  # type: ignore[import-untyped]
from reportlab.platypus import (  # type: ignore[import-untyped]
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_NAVY = rl_colors.HexColor("#1B3A6B")
_ORANGE = rl_colors.HexColor("#E87722")
_LIGHT_BG = rl_colors.HexColor("#F7F9FC")
_GREY = rl_colors.HexColor("#6B7280")
_DARK = rl_colors.HexColor("#374151")


def build_executive_pdf(
    total_current_ss: float,
    total_optimal_ss: float,
    annual_saving: float,
    n_critical: int = 0,
    n_operational: int = 0,
    n_standard: int = 0,
) -> bytes:
    """Generate a one-page executive summary PDF and return the raw bytes.

    Args:
        total_current_ss: Current portfolio safety-stock value ($).
        total_optimal_ss: Optimised safety-stock value ($).
        annual_saving: Projected annual holding-cost saving ($).
        n_critical: Number of Critical-tier SKUs.
        n_operational: Number of Operational-tier SKUs.
        n_standard: Number of Standard-tier SKUs.

    Returns:
        PDF file contents as bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleS",
        parent=styles["Title"],
        fontSize=18,
        textColor=_NAVY,
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleS",
        parent=styles["Normal"],
        fontSize=9,
        textColor=_GREY,
        spaceAfter=16,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "HeadingS",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=_NAVY,
        spaceBefore=14,
        spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "BodyS",
        parent=styles["Normal"],
        fontSize=9,
        textColor=_DARK,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    disclaimer_style = ParagraphStyle(
        "DisclaimerS",
        parent=styles["Normal"],
        fontSize=7,
        textColor=_GREY,
        spaceAfter=0,
        alignment=TA_LEFT,
    )

    story = []

    # ── Header ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Inventory Optimisation — Executive Summary", title_style))
    story.append(
        Paragraph(
            f"DynaCraft / PACCAR Division &nbsp;·&nbsp; "
            f"Prepared {date.today().strftime('%B %d, %Y')}",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=2, color=_ORANGE, spaceAfter=12))

    # ── Key metrics table ─────────────────────────────────────────────────────
    story.append(Paragraph("Key Financial Impact", heading_style))

    ss_freed = total_current_ss - total_optimal_ss
    col_w = [2.3 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch]
    metrics_data = [
        ["Metric", "Current State", "Optimised", "Opportunity"],
        [
            "Total Safety Stock Value",
            f"${total_current_ss:,.0f}",
            f"${total_optimal_ss:,.0f}",
            f"-${ss_freed:,.0f}",
        ],
        [
            "Annual Holding-Cost Saving",
            "—",
            "—",
            f"${annual_saving:,.0f} / yr",
        ],
    ]

    tbl = Table(metrics_data, colWidths=col_w)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_LIGHT_BG, rl_colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, rl_colors.HexColor("#E5E7EB")),
                ("TEXTCOLOR", (-1, 1), (-1, 2), _ORANGE),
                ("FONTNAME", (-1, 1), (-1, 2), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(tbl)

    # ── Portfolio breakdown table ─────────────────────────────────────────────
    story.append(Paragraph("Portfolio Segmentation", heading_style))
    n_total = n_critical + n_operational + n_standard
    seg_data = [
        ["Tier", "SKU Count", "% of Portfolio", "Priority"],
        [
            "Critical",
            str(n_critical),
            f"{100 * n_critical / max(n_total, 1):.0f}%",
            "Immediate",
        ],
        [
            "Operational",
            str(n_operational),
            f"{100 * n_operational / max(n_total, 1):.0f}%",
            "Q2",
        ],
        [
            "Standard",
            str(n_standard),
            f"{100 * n_standard / max(n_total, 1):.0f}%",
            "Q3–Q4",
        ],
    ]
    seg_col_w = [2.0 * inch, 1.4 * inch, 1.4 * inch, 1.9 * inch]
    seg_tbl = Table(seg_data, colWidths=seg_col_w)
    seg_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_LIGHT_BG, rl_colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, rl_colors.HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(seg_tbl)

    # ── Recommendations ───────────────────────────────────────────────────────
    story.append(Paragraph("Recommended Actions", heading_style))
    recommendations = [
        "1. <b>Immediate (Q1):</b> Review the Critical SKU tier — these represent the "
        "highest-value optimisation opportunities and the greatest stockout risk.",
        "2. <b>Policy alignment (Q2):</b> Migrate high-variability SKUs to periodic-review "
        "(R,S) policies to reduce emergency-order frequency.",
        "3. <b>Data infrastructure (Q2–Q3):</b> Establish automated demand-signal feeds "
        "to enable continuous policy recalibration as market conditions evolve.",
        "4. <b>Full rollout (Q4):</b> Extend optimised policies to the Operational and "
        "Standard tiers to capture remaining holding-cost savings.",
    ]
    for rec in recommendations:
        story.append(Paragraph(rec, body_style))

    # ── Disclaimer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.25 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_GREY))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<i>All figures are derived from synthetic data modelled on realistic "
            "heavy-duty truck parts distribution patterns. Values do not represent "
            "actual PACCAR or DynaCraft operational data.</i>",
            disclaimer_style,
        )
    )

    doc.build(story)
    return buf.getvalue()
