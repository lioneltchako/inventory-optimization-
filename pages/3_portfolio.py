"""
Page 3 — Portfolio View
"How individual SKU results compound across the full 120-SKU portfolio"
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils.disclaimer import show_banner, show_footer
from utils.colors import PRIMARY, SUCCESS, WARNING, DANGER, NEUTRAL
from utils.portfolio_data import get_portfolio, portfolio_summary, PORTFOLIO_DF

st.set_page_config(page_title="Portfolio View | Inventory Simulator", layout="wide")

show_banner()

st.markdown("# Portfolio View")
st.markdown("### How individual SKU savings compound across the full catalogue")
st.divider()

# ── SIDEBAR CONTROLS ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Portfolio Filters")
    st.divider()

    forecast_toggle = st.radio(
        "Forecast mode (affects ALL SKUs)",
        ["ML-Improved", "Baseline"],
        index=0,
    )
    ml_active = forecast_toggle == "ML-Improved"

    family_options = ["All"] + sorted(PORTFOLIO_DF["Family"].unique().tolist())
    family_filter = st.multiselect(
        "Product family",
        options=sorted(PORTFOLIO_DF["Family"].unique().tolist()),
        default=sorted(PORTFOLIO_DF["Family"].unique().tolist()),
    )

    pattern_options = sorted(PORTFOLIO_DF["Pattern"].unique().tolist())
    pattern_filter = st.multiselect(
        "Demand pattern",
        options=pattern_options,
        default=pattern_options,
    )

# ── FILTER DATA ───────────────────────────────────────────────────────────────
df = get_portfolio(
    families=family_filter if family_filter else None,
    patterns=pattern_filter if pattern_filter else None,
)

if df.empty:
    st.error("No SKUs match current filters. Please adjust selections.")
    st.stop()

kpis = portfolio_summary(df)

ss_col = "SS_ML_Value" if ml_active else "SS_Base_Value"
ss_units = "SS_ML_Units" if ml_active else "SS_Base_Units"
fr_col = "Fill_Rate_ML" if ml_active else "Fill_Rate_Base"
hold_col = "Hold_Cost_ML" if ml_active else "Hold_Cost_Base"
total_col = "Total_Cost_ML" if ml_active else "Total_Cost_Base"
saving_val = kpis["annual_saving"] if ml_active else 0.0
ss_shown = df[ss_col].sum()
fr_shown = df[fr_col].mean()

# ── [1] KPI TILES ─────────────────────────────────────────────────────────────
mc1, mc2, mc3, mc4, mc5 = st.columns(5)

with mc1:
    st.metric("SKUs in scope", f"{kpis['n_skus']}")
with mc2:
    st.metric(
        "Baseline safety stock ($)",
        f"~${kpis['ss_value_base']:,.0f}",
        help="Total capital tied up in safety stock — baseline forecast",
    )
with mc3:
    delta_ss = kpis["ss_value_ml"] - kpis["ss_value_base"]
    st.metric(
        "Optimized safety stock ($)",
        f"~${kpis['ss_value_ml']:,.0f}",
        delta=f"{delta_ss:+,.0f} vs baseline",
        delta_color="inverse",
    )
with mc4:
    st.metric(
        "Annual saving ($)",
        f"~${kpis['annual_saving']:,.0f}",
        delta=f"{kpis['ss_delta_pct']:+.1f}% SS reduction",
        delta_color="inverse" if kpis["ss_delta_pct"] < 0 else "normal",
    )
with mc5:
    fr_delta = kpis["avg_fill_rate_ml"] - kpis["avg_fill_rate_base"]
    st.metric(
        "Weighted avg fill rate",
        f"~{fr_shown:.1f}%",
        delta=f"{fr_delta:+.1f}pp vs baseline",
        delta_color="normal",
    )

st.divider()

# ── [2] SCATTER — CV vs SS reduction ─────────────────────────────────────────
st.markdown(
    "### Where does ML help most? — Demand variability vs. safety stock reduction"
)
st.caption(
    "Bubble size = annual spend value (~). "
    "High CV (right side) = volatile or lumpy demand — where ML reduces σ the most."
)

# CHOICE: scatter with quadrant annotations tells the manager exactly which
# SKU groups to prioritise for ML rollout — more actionable than a plain scatter.
fig_scatter = px.scatter(
    df,
    x="CV",
    y="SS_Delta_Pct",
    size=df["SS_Base_Value"].clip(upper=df["SS_Base_Value"].quantile(0.95)),
    color="Family",
    hover_name="SKU",
    hover_data={"CV": ":.2f", "SS_Delta_Pct": ":.1f", "Annual_Saving": ":,.0f"},
    color_discrete_map={
        "Powertrain": PRIMARY,
        "Chassis": WARNING,
        "Electrical": SUCCESS,
        "Critical": DANGER,
    },
    labels={
        "CV": "Demand CV (variability)",
        "SS_Delta_Pct": "SS reduction vs baseline (%)",
    },
    title="SKU demand variability vs. safety stock reduction from ML forecast",
)

# Quadrant lines
med_cv = df["CV"].median()
med_ss = df["SS_Delta_Pct"].median()

fig_scatter.add_hline(y=med_ss, line_dash="dot", line_color=NEUTRAL, opacity=0.5)
fig_scatter.add_vline(x=med_cv, line_dash="dot", line_color=NEUTRAL, opacity=0.5)

quadrant_annotations = [
    dict(
        x=med_cv * 0.5,
        y=df["SS_Delta_Pct"].max() * 0.9,
        text="🎯 Quick wins<br>Stable, high ROI",
        showarrow=False,
        font=dict(color=SUCCESS, size=11),
        xanchor="center",
    ),
    dict(
        x=df["CV"].max() * 0.85,
        y=df["SS_Delta_Pct"].max() * 0.9,
        text="⚡ Buffer essential<br>Volatile, ML critical",
        showarrow=False,
        font=dict(color=DANGER, size=11),
        xanchor="center",
    ),
    dict(
        x=med_cv * 0.5,
        y=df["SS_Delta_Pct"].min() * 0.8,
        text="🔧 Low spend<br>Automate the policy",
        showarrow=False,
        font=dict(color=NEUTRAL, size=11),
        xanchor="center",
    ),
    dict(
        x=df["CV"].max() * 0.85,
        y=df["SS_Delta_Pct"].min() * 0.8,
        text="👀 Manual review<br>Lumpy, critical parts",
        showarrow=False,
        font=dict(color=WARNING, size=11),
        xanchor="center",
    ),
]
for ann in quadrant_annotations:
    fig_scatter.add_annotation(**ann)

fig_scatter.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    template="plotly_white",
    height=480,
)
st.plotly_chart(fig_scatter, use_container_width=True)
st.divider()

# ── [3] TWO CHARTS SIDE BY SIDE ───────────────────────────────────────────────
st.markdown("### Cost breakdown by family and top savings opportunities")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Annual cost by product family — baseline vs. optimized**")

    fam_agg = (
        df.groupby("Family")
        .agg(
            Hold_Base=("Hold_Cost_Base", "sum"),
            Hold_ML=("Hold_Cost_ML", "sum"),
            Order_Base=("Order_Cost_Base", "sum"),
            Order_ML=("Order_Cost_ML", "sum"),
        )
        .reset_index()
    )

    fig_fam = go.Figure()
    for fam, fc in [
        ("Powertrain", PRIMARY),
        ("Chassis", WARNING),
        ("Electrical", SUCCESS),
        ("Critical", DANGER),
    ]:
        row = fam_agg[fam_agg["Family"] == fam]
        if row.empty:
            continue
        fig_fam.add_trace(
            go.Bar(
                name=f"{fam} — Baseline",
                x=[f"{fam}<br>Baseline"],
                y=[row["Hold_Base"].values[0] + row["Order_Base"].values[0]],
                marker_color=NEUTRAL,
                showlegend=False,
            )
        )
        fig_fam.add_trace(
            go.Bar(
                name=f"{fam} — Optimized",
                x=[f"{fam}<br>Optimized"],
                y=[row["Hold_ML"].values[0] + row["Order_ML"].values[0]],
                marker_color=fc,
                showlegend=False,
            )
        )

    fig_fam.update_layout(
        barmode="group",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        template="plotly_white",
        yaxis_title="Annual cost ($)",
        height=380,
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig_fam, use_container_width=True)

with chart_col2:
    st.markdown("**Top 15 SKUs by annual saving ($)**")

    top15 = df.nlargest(15, "Annual_Saving")[["SKU", "Family", "Annual_Saving"]].copy()
    top15_sorted = top15.sort_values("Annual_Saving")

    color_map = {
        "Powertrain": PRIMARY,
        "Chassis": WARNING,
        "Electrical": SUCCESS,
        "Critical": DANGER,
    }
    bar_colors = [color_map.get(f, NEUTRAL) for f in top15_sorted["Family"]]

    fig_top = go.Figure(
        go.Bar(
            x=top15_sorted["Annual_Saving"],
            y=top15_sorted["SKU"],
            orientation="h",
            marker_color=bar_colors,
            text=[f"${v:,.0f}" for v in top15_sorted["Annual_Saving"]],
            textposition="outside",
        )
    )
    fig_top.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        template="plotly_white",
        xaxis_title="Annual saving ($)",
        height=380,
        margin=dict(l=80),
    )
    st.plotly_chart(fig_top, use_container_width=True)

st.divider()

# ── [4] SKU DATA TABLE ────────────────────────────────────────────────────────
st.markdown("### Full SKU table — sorted by annual saving")

display_cols = [
    "SKU",
    "Family",
    "Pattern",
    "Policy",
    "CV",
    "LT_Weeks",
    "SS_Base_Units",
    "SS_ML_Units",
    "SS_Delta_Pct",
    "Annual_Saving",
    "Fill_Rate_Base",
    "Fill_Rate_ML",
]
col_labels = {
    "SKU": "SKU",
    "Family": "Family",
    "Pattern": "Pattern",
    "Policy": "Policy",
    "CV": "CV",
    "LT_Weeks": "LT (wks)",
    "SS_Base_Units": "SS Baseline (units)",
    "SS_ML_Units": "SS Optimized (units)",
    "SS_Delta_Pct": "SS Δ%",
    "Annual_Saving": "Annual Saving ($)",
    "Fill_Rate_Base": "Fill Rate Base (%)",
    "Fill_Rate_ML": "Fill Rate ML (%)",
}

table_df = df[display_cols].rename(columns=col_labels).copy()


def style_table(s: pd.DataFrame) -> pd.DataFrame:
    """Highlight top 15 rows by saving in light green."""
    styles = pd.DataFrame("", index=s.index, columns=s.columns)
    top_idx = s.nlargest(min(15, len(s)), "Annual Saving ($)").index
    styles.loc[top_idx, :] = "background-color: #e8f7f0"
    return styles


styled = table_df.style.apply(style_table, axis=None).format(
    {
        "CV": "{:.2f}",
        "LT (wks)": "{:.1f}",
        "SS Δ%": "{:+.1f}%",
        "Annual Saving ($)": "${:,.0f}",
        "Fill Rate Base (%)": "{:.1f}%",
        "Fill Rate ML (%)": "{:.1f}%",
    }
)

st.dataframe(styled, use_container_width=True, height=420)

# ── CSV download ──────────────────────────────────────────────────────────────
csv_bytes = table_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇ Download filtered table (CSV)",
    data=csv_bytes,
    file_name="paccar_portfolio_optimizer.csv",
    mime="text/csv",
)

st.divider()

st.info(
    "→ **Next: Methodology** — see the formulas behind every number and "
    "understand why policy choice matters as much as forecast accuracy. "
    f"Today's top saving opportunity: ~${df['Annual_Saving'].max():,.0f}/year "
    f"on a single SKU."
)

show_footer(
    [
        "120 SKUs generated with numpy.random.seed(42)",
        "Formulas: Vandeput (2020) Ch. 5–6",
        "All values approximated (~)",
    ]
)
