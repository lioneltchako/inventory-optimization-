"""Centralized color palette and CSS for the Inventory Policy Simulator.

All color values are defined here. UI modules must import from COLOR_MAP
and CRITICALITY_COLORS — never hardcode hex values in page modules.
"""

from __future__ import annotations

COLOR_MAP: dict[str, str] = {
    "primary": "#1B3A6B",  # PACCAR navy
    "accent": "#E87722",  # action orange
    "success": "#2E8B57",  # confirmation green
    "warning": "#F5A623",  # caution amber
    "danger": "#C0392B",  # alert red
    "background": "#F7F9FC",  # page background
    "card": "#FFFFFF",  # card surface
    "muted": "#6B7280",  # secondary text
}

CRITICALITY_COLORS: dict[str, str] = {
    "Critical": COLOR_MAP["danger"],
    "Operational": COLOR_MAP["warning"],
    "Standard": COLOR_MAP["success"],
}


def get_css() -> str:
    """Return the full custom CSS string for st.markdown injection."""
    primary = COLOR_MAP["primary"]
    accent = COLOR_MAP["accent"]
    bg = COLOR_MAP["background"]
    card = COLOR_MAP["card"]
    muted = COLOR_MAP["muted"]

    return f"""
    /* ── Sidebar ─────────────────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background-color: {primary} !important;
    }}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {{
        color: rgba(255,255,255,0.92) !important;
    }}
    [data-testid="stSidebar"] a {{
        color: white !important;
    }}
    [data-testid="stSidebarNav"] a[aria-selected="true"] {{
        background-color: rgba(232,119,34,0.25) !important;
        border-left: 3px solid {accent};
    }}
    [data-testid="stSidebarNav"] a:hover {{
        background-color: rgba(255,255,255,0.1) !important;
    }}

    /* ── Primary button ──────────────────────────────────────── */
    .stButton > button {{
        background-color: {accent};
        border: none;
        color: white;
        font-weight: 700;
        padding: 0.55rem 1.5rem;
        border-radius: 6px;
        transition: background-color 0.15s ease;
    }}
    .stButton > button:hover {{
        background-color: #d06618;
        color: white;
    }}

    /* ── KPI metric cards ────────────────────────────────────── */
    [data-testid="stMetric"] {{
        background-color: {card};
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    [data-testid="stMetricLabel"] > div {{
        color: {muted};
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    [data-testid="stMetricValue"] > div {{
        color: {primary};
        font-size: 1.75rem;
        font-weight: 700;
    }}

    /* ── Page background ─────────────────────────────────────── */
    .stApp {{
        background-color: {bg};
    }}
    .block-container {{
        padding-top: 1.5rem;
    }}

    /* ── Hero banner ─────────────────────────────────────────── */
    .hero-banner {{
        background: linear-gradient(135deg, {primary} 0%, #254e98 100%);
        color: white;
        padding: 2rem 2.4rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border-left: 5px solid {accent};
    }}
    .hero-banner h2 {{
        color: white !important;
        font-size: 1.65rem;
        font-weight: 700;
        margin: 0 0 0.4rem 0;
        line-height: 1.3;
    }}
    .hero-banner p {{
        color: rgba(255,255,255,0.82);
        font-size: 0.95rem;
        margin: 0;
    }}
    .hero-accent {{
        color: {accent};
        font-weight: 800;
    }}

    /* ── Insight card ────────────────────────────────────────── */
    .insight-card {{
        background-color: {card};
        border-left: 4px solid {accent};
        border-radius: 6px;
        padding: 0.9rem 1.3rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }}

    /* ── Criticality badges ──────────────────────────────────── */
    .badge-critical {{
        background: {COLOR_MAP["danger"]}22;
        color: {COLOR_MAP["danger"]};
        border: 1px solid {COLOR_MAP["danger"]}44;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    .badge-operational {{
        background: {COLOR_MAP["warning"]}22;
        color: {COLOR_MAP["warning"]};
        border: 1px solid {COLOR_MAP["warning"]}44;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    .badge-standard {{
        background: {COLOR_MAP["success"]}22;
        color: {COLOR_MAP["success"]};
        border: 1px solid {COLOR_MAP["success"]}44;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }}

    /* ── Section headings ────────────────────────────────────── */
    h2, h3 {{
        color: {primary};
    }}

    /* ── Divider ─────────────────────────────────────────────── */
    hr {{
        border-color: #E5E7EB;
        margin: 1rem 0;
    }}

    /* ── DataFrame styling ───────────────────────────────────── */
    [data-testid="stDataFrame"] thead tr th {{
        background-color: {primary} !important;
        color: white !important;
        font-weight: 600;
    }}
    """
