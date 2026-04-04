"""
Analytic — Smart insights for small business
A data-driven tool for small business owners.
Turns raw transaction data into a complete business strategy.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import hashlib
import os
try:
    from groq import Groq as _GroqClient
    _GROQ_AVAILABLE = True
except Exception:
    _GroqClient = None
    _GROQ_AVAILABLE = False
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
try:
    from prophet import Prophet as _Prophet
    _PROPHET_AVAILABLE = True
except Exception:
    _PROPHET_AVAILABLE = False

try:
    from statsforecast import StatsForecast as _StatsForecast
    from statsforecast.models import AutoARIMA as _AutoARIMA, AutoETS as _AutoETS
    _STATSFORECAST_AVAILABLE = True
except Exception:
    _STATSFORECAST_AVAILABLE = False

try:
    from mlxtend.frequent_patterns import apriori as _apriori, association_rules as _assoc_rules
    from mlxtend.preprocessing import TransactionEncoder as _TransactionEncoder
    _MLXTEND_AVAILABLE = True
except Exception:
    _MLXTEND_AVAILABLE = False
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Analytic", page_icon="📊", layout="wide")

# =============================================================================
# CUSTOM THEME — Professional Business
# #f0f4f8 light background | #1e3a5f navy sidebar | #2563eb accent blue | #93c5fd light blue
# #e2e8f0 light gray | #1a202c dark text
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Raleway:wght@300;400;500;600;700&display=swap');

html, body {
    font-family: 'Raleway', sans-serif;
    background-color: #f0f4f8;
    color: #1e3a5f;
}
.stApp { background-color: #f0f4f8; }

/* ── Sidebar — navy blue ── */
[data-testid="stSidebar"] {
    background-color: #1e3a5f;
    border-right: none;
}
[data-testid="stSidebar"] * {
    color: #f0f4f8 !important;
    font-family: 'Raleway', sans-serif !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: #f0f4f8 !important;
    letter-spacing: 0.04em;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: #93c5fd !important;
}
[data-testid="stSidebar"] .stSuccess {
    background-color: #1a202c !important;
    border: none !important;
    color: #93c5fd !important;
    font-size: 0.85rem !important;
}
[data-testid="stSidebar"] .stWarning {
    background-color: #1a202c !important;
    border: none !important;
    color: #f0f4f8 !important;
}

/* ── Headings ── */
h1 {
    font-family: 'Cormorant', serif !important;
    font-weight: 500 !important;
    font-size: 3.8rem !important;
    color: #1e3a5f !important;
    letter-spacing: 0.08em;
    line-height: 1.0;
    text-transform: uppercase;
}
h2 {
    font-family: 'Cormorant', serif !important;
    font-weight: 500 !important;
    font-size: 2.1rem !important;
    color: #1e3a5f !important;
    border-bottom: 2px solid #93c5fd;
    padding-bottom: 0.5rem;
    margin-top: 1.5rem !important;
    margin-bottom: 0.8rem !important;
    letter-spacing: 0.05em;
}
h3 {
    font-family: 'Raleway', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.75rem !important;
    color: #2563eb !important;
    text-transform: uppercase;
    letter-spacing: 0.2em;
}

/* ── Body text ── */
p { color: #1e3a5f; font-size: 1rem; line-height: 1.8; font-weight: 400; }
li { color: #1e3a5f; font-size: 1rem; line-height: 1.9; }

/* ── Captions ── */
[data-testid="stCaptionContainer"] p {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: #2563eb !important;
    opacity: 1 !important;
}

/* ── Metrics — warm tan cards ── */
[data-testid="stMetricValue"] {
    font-family: 'Cormorant', serif !important;
    font-size: 2.8rem !important;
    font-weight: 500 !important;
    color: #1e3a5f !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: #2563eb !important;
}
[data-testid="metric-container"] {
    background-color: #e2e8f0;
    border: 1px solid #93c5fd;
    border-radius: 12px;
    padding: 1.4rem !important;
}

/* ── Buttons — accent blue ── */
.stButton > button {
    background-color: #1e3a5f;
    border: none;
    color: #f0f4f8 !important;
    font-family: 'Raleway', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    border-radius: 4px;
    padding: 0.6rem 1.4rem;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background-color: #2563eb;
    color: #f0f4f8 !important;
    transform: translateY(-1px);
}

/* ── Selects & inputs ── */
[data-testid="stSelectbox"] > div > div {
    background-color: #fdf7f0 !important;
    border: 1px solid #93c5fd !important;
    color: #1e3a5f !important;
    border-radius: 6px;
    font-size: 0.95rem !important;
}
textarea {
    background-color: #fdf7f0 !important;
    border: 1px solid #93c5fd !important;
    color: #1e3a5f !important;
    font-family: 'Raleway', sans-serif !important;
    font-size: 0.95rem !important;
    border-radius: 6px !important;
}
[data-testid="stFileUploader"] {
    background-color: #fdf7f0;
    border: 2px dashed #93c5fd;
    border-radius: 12px;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background-color: #fdf7f0;
    border: 1px solid #93c5fd !important;
    border-radius: 12px;
    margin-bottom: 1rem;
}
[data-testid="stExpander"] summary {
    color: #1e3a5f !important;
    font-family: 'Raleway', sans-serif;
    font-size: 1rem !important;
    font-weight: 600 !important;
    padding: 1rem !important;
    letter-spacing: 0.02em;
}
[data-testid="stExpander"] summary:hover {
    color: #2563eb !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    background-color: #fdf7f0;
    border-left: 4px solid #2563eb;
    border-radius: 6px;
    color: #1e3a5f !important;
    font-size: 0.95rem;
}
[data-testid="stAlert"] * { color: #1e3a5f !important; }

/* ── Chat ── */
[data-testid="stChatMessage"] {
    background-color: #fdf7f0;
    border: 1px solid #93c5fd;
    border-radius: 12px;
    margin-bottom: 1rem;
}
[data-testid="stChatInput"] textarea {
    background-color: #fdf7f0 !important;
    border: 2px solid #2563eb !important;
    color: #1e3a5f !important;
    border-radius: 6px !important;
    font-size: 1rem !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #93c5fd;
    border-radius: 8px;
    overflow: hidden;
}

/* ── Divider ── */
hr { border-color: #93c5fd !important; border-width: 1px !important; }

/* ── Slider ── */
[data-testid="stSlider"] * { color: #1e3a5f !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #f0f4f8; }
::-webkit-scrollbar-thumb { background: #93c5fd; border-radius: 4px; }

/* ── Markdown text ── */
[data-testid="stMarkdownContainer"] p { color: #1e3a5f !important; font-size: 1rem !important; }
[data-testid="stMarkdownContainer"] li { color: #1e3a5f !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { display: none; }
footer { display: none; }
[data-testid="stToolbar"] { display: none; }
.stDeployButton { display: none; }

/* ── Main content top padding fix (header hidden) ── */
.block-container {
    padding-top: 2rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: 1400px;
}

/* ── Sidebar: hide default radio bullets, style as nav links ── */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    display: block;
    width: 100%;
    padding: 0.65rem 1.2rem !important;
    border-radius: 8px;
    margin: 2px 0;
    cursor: pointer;
    transition: background 0.15s ease;
    font-size: 0.92rem !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background-color: rgba(255,255,255,0.1) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child,
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
    display: none !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] {
    background-color: rgba(37,99,235,0.35) !important;
    border-left: 3px solid #93c5fd;
    padding-left: calc(1.2rem - 3px) !important;
    font-weight: 700 !important;
}

/* ── Sidebar brand area ── */
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

/* ── Card shadow on metric containers ── */
[data-testid="metric-container"] {
    box-shadow: 0 2px 12px rgba(30,58,95,0.10);
    transition: box-shadow 0.2s ease;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 4px 20px rgba(30,58,95,0.18);
}

/* ── Expanders: card shadow ── */
[data-testid="stExpander"] {
    box-shadow: 0 1px 8px rgba(30,58,95,0.08);
}

/* ── Download button in sidebar ── */
[data-testid="stSidebar"] .stDownloadButton > button {
    background-color: rgba(37,99,235,0.2) !important;
    border: 1px solid #93c5fd !important;
    color: #f0f4f8 !important;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    border-radius: 6px;
    width: 100%;
    margin-top: 0.5rem;
}
[data-testid="stSidebar"] .stDownloadButton > button:hover {
    background-color: rgba(37,99,235,0.45) !important;
}

/* ── Sidebar divider ── */
[data-testid="stSidebar"] hr {
    border-color: rgba(147,197,253,0.3) !important;
    margin: 1rem 0;
}

/* ── Selectbox dropdown polish ── */
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background-color: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(147,197,253,0.4) !important;
    color: #f0f4f8 !important;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# PLOTLY GLOBAL TEMPLATE — match charts to the app's navy/blue design system
# =============================================================================
import plotly.io as pio

_ANALYTIC_COLORS = [
    "#2563eb",  # accent blue
    "#1e3a5f",  # navy
    "#93c5fd",  # light blue
    "#3b82f6",  # medium blue
    "#60a5fa",  # sky blue
    "#1d4ed8",  # deep blue
    "#7dd3fc",  # pale blue
    "#0ea5e9",  # cyan blue
    "#6366f1",  # indigo
    "#818cf8",  # light indigo
]

_analytic_template = go.layout.Template()
_analytic_template.layout = go.Layout(
    font=dict(family="Raleway, sans-serif", color="#1e3a5f", size=13),
    title=dict(
        font=dict(family="Cormorant, serif", size=22, color="#1e3a5f", weight="normal"),
        x=0.0, xanchor="left",
        pad=dict(l=0, t=8, b=12),
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    colorway=_ANALYTIC_COLORS,
    xaxis=dict(
        gridcolor="rgba(147,197,253,0.15)",
        gridwidth=1,
        griddash="dot",
        linecolor="rgba(147,197,253,0.4)",
        linewidth=1,
        zerolinecolor="rgba(147,197,253,0.3)",
        zerolinewidth=1,
        title=dict(font=dict(size=11, color="#64748b", weight="bold"),
                   standoff=14),
        tickfont=dict(size=10, color="#64748b"),
        showgrid=True,
    ),
    yaxis=dict(
        gridcolor="rgba(147,197,253,0.15)",
        gridwidth=1,
        griddash="dot",
        linecolor="rgba(0,0,0,0)",
        linewidth=0,
        zerolinecolor="rgba(147,197,253,0.3)",
        zerolinewidth=1,
        title=dict(font=dict(size=11, color="#64748b", weight="bold"),
                   standoff=14),
        tickfont=dict(size=10, color="#64748b"),
        showgrid=True,
        side="left",
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(0,0,0,0)",
        borderwidth=0,
        font=dict(size=11, color="#475569"),
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="left", x=0,
        itemsizing="constant",
        tracegroupgap=4,
    ),
    hoverlabel=dict(
        bgcolor="#1e293b",
        font_color="#f8fafc",
        font_size=12,
        font_family="Raleway, sans-serif",
        bordercolor="rgba(0,0,0,0)",
        namelength=-1,
    ),
    margin=dict(l=48, r=16, t=64, b=48),
    bargap=0.25,
    bargroupgap=0.08,
    hovermode="x unified",
    transition=dict(duration=400, easing="cubic-in-out"),
)

# Bar defaults — rounded look with subtle shadow border
_analytic_template.data.bar = [
    go.Bar(marker=dict(
        cornerradius=6,
        line=dict(width=0),
    ))
]
# Scatter defaults — crisp markers with white halo
_analytic_template.data.scatter = [
    go.Scatter(marker=dict(size=7, line=dict(width=2, color="rgba(255,255,255,0.9)")))
]

pio.templates["analytic"] = _analytic_template
pio.templates.default = "analytic"

# =============================================================================
# PROMPT SANITIZATION — strip newlines and limit length on untrusted CSV values
# =============================================================================

def _sanitize_for_prompt(value: str, max_len: int = 120) -> str:
    """Remove characters that could break prompt structure and cap length."""
    cleaned = str(value).replace("\n", " ").replace("\r", " ").replace("\x00", "")
    return cleaned[:max_len]


# =============================================================================
# INDUSTRY TEMPLATES — pre-configure metric visibility by business type
# =============================================================================

_INDUSTRY_TEMPLATES: dict = {
    "(none)": {
        "label": "(none)",
        "primary_metrics": [],
        "surface_first":   [],
        "collapse_first":  [],
        "action_center_emphasis": [],
        "ai_hint": "",
    },
    "Restaurant / Bar": {
        "label": "Restaurant / Bar",
        "primary_metrics":  ["revenue", "avg_order_value"],
        "surface_first":    ["declining_products"],
        "collapse_first":   ["forecast", "basket"],
        "action_center_emphasis": ["declining", "wow"],
        "ai_hint": (
            "Focus on table turn rate, check average, and service period performance. "
            "Flag items with food cost > 35%. Use 'covers', 'check average', 'comp' language."
        ),
    },
    "Retail": {
        "label": "Retail",
        "primary_metrics":  ["revenue", "units_sold", "sell_through"],
        "surface_first":    ["best_sellers", "low_activity", "pricing"],
        "collapse_first":   [],
        "action_center_emphasis": ["low_activity", "pricing", "bundle"],
        "ai_hint": (
            "Focus on sell-through rate, slow-moving inventory, and margin per SKU. "
            "Use 'units sold', 'markdown', 'SKU', 'footfall' language."
        ),
    },
    "Café / Coffee Shop": {
        "label": "Café / Coffee Shop",
        "primary_metrics":  ["revenue", "avg_order_value", "top_product"],
        "surface_first":    ["best_sellers", "rising_stars"],
        "collapse_first":   ["forecast"],
        "action_center_emphasis": ["rising", "bundle", "pricing"],
        "ai_hint": (
            "Focus on loyalty, morning rush, and add-on upsells. "
            "Benchmark ticket at $6–9 drink-only. Use 'covers', 'upsell', 'regulars' language."
        ),
    },
    "E-commerce": {
        "label": "E-commerce",
        "primary_metrics":  ["revenue", "avg_order_value", "units_sold"],
        "surface_first":    ["best_sellers", "basket", "pricing"],
        "collapse_first":   [],
        "action_center_emphasis": ["bundle", "pricing", "rising"],
        "ai_hint": (
            "Focus on basket size, repeat purchase rates, and conversion by product. "
            "Use 'AOV', 'SKU', 'add-to-cart', 'bundle' language."
        ),
    },
    "Services": {
        "label": "Services",
        "primary_metrics":  ["revenue", "avg_order_value"],
        "surface_first":    ["best_sellers"],
        "collapse_first":   ["basket", "forecast"],
        "action_center_emphasis": ["pricing", "rising"],
        "ai_hint": (
            "Focus on service utilization, appointment density, and upsell per visit. "
            "Use 'appointments', 'utilization', 'add-on service' language."
        ),
    },
}


def _infer_industry_template(df: pd.DataFrame, raw_cols: list[str] | None = None) -> str | None:
    """Return the most likely _INDUSTRY_TEMPLATES key from product names, or None."""
    if "product" not in df.columns or df.empty:
        return None

    products = df["product"].dropna().astype(str).str.lower().unique().tolist()
    if not products:
        return None

    _KEYWORDS: dict[str, list[str]] = {
        "Café / Coffee Shop": [
            "espresso", "latte", "cappuccino", "americano", "flat white",
            "cold brew", "drip", "cortado", "matcha", "chai",
            "croissant", "muffin", "scone", "bagel",
        ],
        "Restaurant / Bar": [
            "burger", "pizza", "pasta", "steak", "wings", "nachos",
            "cocktail", "beer", "wine", "draft", "entrée", "appetizer",
            "fries", "tacos", "sushi", "ramen",
        ],
        "Retail": [
            "shirt", "pants", "jacket", "dress", "shoe", "hat", "bag",
            "wallet", "hoodie", "jeans", "tee", "blouse", "scarf", "belt",
            "cap", "hardware", "tool", "wrench", "bolt", "lumber",
        ],
        "Services": [
            "haircut", "trim", "color", "massage", "facial", "manicure",
            "pedicure", "consult", "session", "lesson", "class",
            "appointment", "fitting", "repair", "service",
        ],
    }

    scores: dict[str, int] = {}
    for category, keywords in _KEYWORDS.items():
        scores[category] = sum(1 for p in products if any(kw in p for kw in keywords))

    # E-commerce: requires sku/order_id column AND majority of products look like SKU codes
    _raw_cols_lower = [c.lower() for c in (raw_cols or [])]
    _has_sku_col = any("sku" in c or c == "order_id" for c in _raw_cols_lower)
    if _has_sku_col:
        _sku_pat = re.compile(r"^[a-z0-9]{4,12}$")
        _no_space = sum(1 for p in products if " " not in p and _sku_pat.match(p))
        scores["E-commerce"] = _no_space if len(products) > 0 and _no_space / len(products) >= 0.5 else 0
    else:
        scores["E-commerce"] = 0

    qualified = {cat: cnt for cat, cnt in scores.items() if cnt >= 2}
    if not qualified:
        return None

    top = max(qualified.values())
    winners = [cat for cat, cnt in qualified.items() if cnt == top]
    return winners[0] if len(winners) == 1 else None


def _tpl_expanded(section_key: str) -> bool:
    """Return True if this section should be expanded for the active industry template."""
    tpl_name = st.session_state.get("industry_template", "(none)")
    if not tpl_name or tpl_name == "(none)":
        return False
    tpl = _INDUSTRY_TEMPLATES.get(tpl_name)
    if tpl is None:
        return False
    if section_key in tpl["surface_first"]:
        return True
    if section_key in tpl["collapse_first"]:
        return False
    return False


# =============================================================================
# GROQ CLIENT HELPER — single source of truth for AI config
# =============================================================================

def _get_groq_client():
    """
    Returns a configured Groq client or None if unavailable.
    Single function used by ALL AI features in the app —
    change the model name here to update everywhere at once.
    """
    import os
    if not _GROQ_AVAILABLE:
        return None
    api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        return _GroqClient(api_key=api_key)
    except Exception:
        return None


import time

def _groq_generate(client, prompt, retries=1):
    """Call Groq with automatic retry on rate limit (429)."""
    # Normalise prompt → list of OpenAI-style message dicts
    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        # Convert from parts format if needed
        messages = []
        for m in prompt:
            role = "assistant" if m.get("role") == "model" else m.get("role", "user")
            parts = m.get("parts", [m.get("content", "")])
            content = parts[0] if isinstance(parts, list) else parts
            messages.append({"role": role, "content": content})

    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.4,
                max_tokens=1000,
            )
            # Safety: handle empty choices, missing message, or None content
            if not resp.choices:
                class _Empty:
                    text = ""
                return _Empty()
            msg = resp.choices[0].message
            raw_text = getattr(msg, "content", None) or ""
            class _Resp:
                text = raw_text
            return _Resp()
        except Exception as e:
            if "429" in str(e) and attempt < retries:
                st.toast("AI is warming up — retrying in 5 seconds...", icon="⏳")
                time.sleep(5)
                continue
            raise


# =============================================================================
# DEMO DATASET — Coffee Shop (6 months, 2 locations, 18 products)
# =============================================================================

def _generate_demo_df() -> pd.DataFrame:
    """Generate a realistic coffee-shop demo with timestamps, 2 locations, 18 products."""
    rng = np.random.default_rng(42)

    # (name, avg_price, demand_weight, cost_pct)  — cost_pct = fraction of price that is COGS
    products_data = [
        ("Espresso",            3.50, 0.13, 0.28),   # high-margin drink
        ("Americano",           4.00, 0.11, 0.30),
        ("Latte",               5.50, 0.16, 0.35),
        ("Cappuccino",          5.00, 0.12, 0.35),
        ("Cold Brew",           5.50, 0.07, 0.38),
        ("Flat White",          5.50, 0.05, 0.35),
        ("Macchiato",           4.50, 0.04, 0.33),
        ("Mocha",               6.00, 0.04, 0.40),
        ("Hot Chocolate",       4.50, 0.03, 0.38),
        ("Green Tea",           3.50, 0.02, 0.28),
        ("Croissant",           3.50, 0.07, 0.45),   # food — higher cost
        ("Blueberry Muffin",    3.00, 0.05, 0.42),
        ("Avocado Toast",       9.00, 0.03, 0.52),
        ("Granola Bowl",        7.50, 0.02, 0.48),
        ("BLT Sandwich",        8.50, 0.02, 0.55),
        ("Cheesecake Slice",    6.00, 0.01, 0.40),
        ("Brownie",             3.50, 0.015, 0.38),
        ("Bagel & Cream Cheese",5.00, 0.015, 0.45),
    ]
    names     = [p[0] for p in products_data]
    prices    = np.array([p[1] for p in products_data])
    weights   = np.array([p[2] for p in products_data])
    cost_pcts = np.array([p[3] for p in products_data])
    weights = weights / weights.sum()

    locations   = ["Main Street", "Downtown"]
    loc_weights = [0.60, 0.40]

    n = 1400
    end   = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(months=6)

    # Random calendar days, then assign business-hours timestamps
    total_days = (end - start).days
    rand_days  = rng.integers(0, total_days + 1, size=n)
    hours      = rng.integers(7, 21, size=n)          # 7 am – 8 pm
    minutes    = rng.integers(0, 60, size=n)

    timestamps = [
        start + pd.Timedelta(days=int(d), hours=int(h), minutes=int(m))
        for d, h, m in zip(rand_days, hours, minutes)
    ]

    pidx   = rng.choice(len(names), size=n, p=weights)
    lidx   = rng.choice(len(locations), size=n, p=loc_weights)
    qtys   = rng.integers(1, 4, size=n)
    # ±5 % price jitter to give the price-intelligence page realistic spread
    jitter = 1 + rng.uniform(-0.05, 0.05, size=n)

    # Generate order IDs — simulate realistic basket sizes
    # ~60% single item, ~30% two items, ~10% three items
    order_ids = []
    order_counter = 1
    i = 0
    while i < n:
        roll = rng.random()
        if roll < 0.60:
            size = 1
        elif roll < 0.90:
            size = 2
        else:
            size = 3
        size = min(size, n - i)
        order_id = f"ORD-{order_counter:04d}"
        order_ids.extend([order_id] * size)
        order_counter += 1
        i += size

    rows = [
        {
            "order_id":   order_ids[i],
            "product":    names[pidx[i]],
            "quantity":   int(qtys[i]),
            "unit_price": round(float(prices[pidx[i]] * jitter[i]), 2),
            "revenue":    round(float(prices[pidx[i]] * jitter[i] * qtys[i]), 2),
            "cost":       round(float(prices[pidx[i]] * cost_pcts[pidx[i]] * qtys[i]), 2),
            "date":       timestamps[i],
            "location":   locations[lidx[i]],
        }
        for i in range(n)
    ]

    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


# =============================================================================
# DEMO DATASET — Retail Store (6 months, 1 location, 20 products)
# =============================================================================

def _generate_retail_demo_df() -> pd.DataFrame:
    """Generate a realistic retail-store demo with timestamps, 1 location, 20 products."""
    rng = np.random.default_rng(99)

    # (name, avg_price, demand_weight, cost_pct)
    products_data = [
        ("Classic T-Shirt",       24.99, 0.12, 0.45),
        ("Denim Jeans",           59.99, 0.09, 0.50),
        ("Running Sneakers",      89.99, 0.06, 0.52),
        ("Canvas Tote Bag",       19.99, 0.08, 0.40),
        ("Scented Candle",        14.99, 0.07, 0.35),
        ("Ceramic Mug",           12.99, 0.06, 0.38),
        ("Notebook Set (3-pack)", 9.99,  0.05, 0.42),
        ("Stainless Water Bottle",29.99, 0.05, 0.48),
        ("Sunglasses",            34.99, 0.04, 0.44),
        ("Phone Case",            15.99, 0.06, 0.32),
        ("Baseball Cap",          19.99, 0.05, 0.40),
        ("Wool Scarf",            29.99, 0.03, 0.46),
        ("Leather Wallet",        39.99, 0.04, 0.50),
        ("Desk Lamp",             44.99, 0.03, 0.55),
        ("Yoga Mat",              34.99, 0.03, 0.48),
        ("Bluetooth Speaker",     49.99, 0.03, 0.55),
        ("Lip Balm (3-pack)",     7.99,  0.04, 0.30),
        ("Hand Cream",            11.99, 0.03, 0.35),
        ("Greeting Cards (5-pk)", 8.99,  0.02, 0.28),
        ("Keychain",              6.99,  0.02, 0.25),
    ]
    names     = [p[0] for p in products_data]
    prices    = np.array([p[1] for p in products_data])
    weights   = np.array([p[2] for p in products_data])
    cost_pcts = np.array([p[3] for p in products_data])
    weights = weights / weights.sum()

    location = "Main Street"

    n = 1200
    end   = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(months=6)

    total_days = (end - start).days
    rand_days  = rng.integers(0, total_days + 1, size=n)
    hours      = rng.integers(9, 20, size=n)          # 9 am – 7 pm
    minutes    = rng.integers(0, 60, size=n)

    timestamps = [
        start + pd.Timedelta(days=int(d), hours=int(h), minutes=int(m))
        for d, h, m in zip(rand_days, hours, minutes)
    ]

    pidx   = rng.choice(len(names), size=n, p=weights)
    qtys   = rng.integers(1, 3, size=n)
    jitter = 1 + rng.uniform(-0.03, 0.03, size=n)

    # Order IDs — ~55% single, ~35% two items, ~10% three items
    order_ids: list[str] = []
    order_counter = 1
    i = 0
    while i < n:
        roll = rng.random()
        if roll < 0.55:
            size = 1
        elif roll < 0.90:
            size = 2
        else:
            size = 3
        size = min(size, n - i)
        order_id = f"RET-{order_counter:04d}"
        order_ids.extend([order_id] * size)
        order_counter += 1
        i += size

    rows = [
        {
            "order_id":   order_ids[i],
            "product":    names[pidx[i]],
            "quantity":   int(qtys[i]),
            "unit_price": round(float(prices[pidx[i]] * jitter[i]), 2),
            "revenue":    round(float(prices[pidx[i]] * jitter[i] * qtys[i]), 2),
            "cost":       round(float(prices[pidx[i]] * cost_pcts[pidx[i]] * qtys[i]), 2),
            "date":       timestamps[i],
            "location":   location,
        }
        for i in range(n)
    ]

    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


# =============================================================================
# CURRENCY HELPER
# =============================================================================

def _cur() -> str:
    """Return the active currency symbol from session state (default $)."""
    return st.session_state.get("currency_sym", "$")


def _has_dates(df: pd.DataFrame) -> bool:
    """True if the date column is datetime-typed AND has at least one non-null value."""
    return pd.api.types.is_datetime64_any_dtype(df["date"]) and df["date"].notna().any()


def _build_data_confidence_badge(df: pd.DataFrame) -> str:
    """Return a short plain-English data quality statement for display under AI answers."""
    n_rows = len(df)
    if n_rows == 0:
        return "*Based on 0 transactions*"

    has_dates = _has_dates(df)

    if has_dates:
        span_days = (df["date"].max() - df["date"].min()).days
        weeks = round(span_days / 7)
        if weeks < 1:
            time_part = f"{span_days} day{'s' if span_days != 1 else ''} of data"
        elif weeks < 8:
            time_part = f"{weeks} week{'s' if weeks != 1 else ''} of data"
        else:
            months = round(span_days / 30)
            time_part = f"{months} month{'s' if months != 1 else ''} of data"
    else:
        time_part = "snapshot data (no dates)"

    n_products = df["product"].nunique()

    return (
        f"*Based on {n_rows:,} transactions · {n_products} products · {time_part}*"
    )


def _confidence_label(n: int) -> str:
    """Return a data quality indicator based on transaction count."""
    if n < 15:
        level = "Need more data"
    elif n < 100:
        level = "Worth testing"
    else:
        level = "Strong signal — act on this"
    return f"Based on your last {n:,} sales — {level}"


def _confidence_tier(tier: str) -> tuple:
    """Return (label, emoji) for a signal confidence tier.

    tier: 'high' | 'directional' | 'insufficient'
    - 'high'         → data-estimated with strong statistical fit
    - 'directional'  → heuristic or moderate-fit estimate; useful for decisions, not budgeting
    - 'insufficient' → too little data to produce a meaningful signal
    """
    return {
        "high":         ("Strong signal — act on this", "🟢"),
        "directional":  ("Worth testing",               "🟡"),
        "insufficient": ("Need more data",              "🔴"),
    }.get(tier, ("Worth testing", "🟡"))


# =============================================================================
# RECOMMENDATION SAFETY RULES — Minimum evidence thresholds
# =============================================================================

# Centralized thresholds. Raise these conservatively: false recommendations
# cost trust; missed opportunities cost only revenue, which can be recovered.
_MIN_TXN_FOR_TREND    = 14   # minimum daily observations needed for trend insights
_MIN_TXN_FOR_CLUSTER  = 20   # minimum total transactions before clustering is reported
_MIN_TXN_FOR_PRICING  = 10   # minimum per-product transactions for any pricing signal
_MIN_TXN_FOR_ANOMALY  = 14   # minimum days of daily revenue for anomaly detection
_MIN_DATE_SPAN_DAYS   = 14   # minimum calendar span for time-based analyses

# Percentile split for demand/price tier classification in pricing recommendations.
# 35th/65th creates three balanced bands (low / mid / high) without extreme sensitivity.
_QUANTILE_LOW        = 0.35
_QUANTILE_HIGH       = 0.65

# MAD-based anomaly detection threshold.
# 2.5 (vs 2.0 for plain Z-score) compensates for MAD's tighter scale factor (1.4826),
# keeping the false-positive rate to roughly 1 % under a normal distribution.
_MAD_ANOMALY_Z       = 2.5

# Fallback price-elasticity when no product-level OLS estimate is available and the
# cluster category is unknown — sits between loyal-buyer (≈0.4) and price-sensitive (≈0.8).
_DEFAULT_ELASTICITY  = 0.65

# Minimum transactions per product in each period for period-comparison noise filtering.
# Keeps noisy single-sale products out of the risers/fallers lists.
_MIN_PRODUCT_TXN_FOR_PERIOD = 3


def _recommendation_safety_check(df: pd.DataFrame) -> dict:
    """Evaluate dataset quality and return safety flags for each analysis module.

    Returns a dict of {module_name: (safe: bool, reason: str)}.
    Modules should check their flag before emitting strong recommendations.
    """
    n_txn = len(df)
    has_dates = _has_dates(df)
    n_days = df["date"].dt.date.nunique() if has_dates else 0
    date_span = (df["date"].max() - df["date"].min()).days if has_dates and n_txn > 0 else 0
    n_products = df["product"].nunique()
    has_variance = df.groupby("product")["revenue"].std().fillna(0).gt(0).any()

    checks = {
        "trend": (
            has_dates and n_days >= _MIN_TXN_FOR_TREND and date_span >= _MIN_DATE_SPAN_DAYS,
            f"need {_MIN_TXN_FOR_TREND}+ days of data (have {n_days})" if not has_dates or n_days < _MIN_TXN_FOR_TREND
            else f"need {_MIN_DATE_SPAN_DAYS}+ day span (have {date_span})"
        ),
        "anomaly": (
            has_dates and n_days >= _MIN_TXN_FOR_ANOMALY,
            f"need {_MIN_TXN_FOR_ANOMALY}+ daily observations (have {n_days})"
        ),
        "clustering": (
            n_products >= 4 and n_txn >= _MIN_TXN_FOR_CLUSTER,
            f"need 4+ products and {_MIN_TXN_FOR_CLUSTER}+ transactions"
        ),
        "pricing": (
            n_txn >= _MIN_TXN_FOR_PRICING and has_variance,
            "need price variation and sufficient transaction volume per product"
        ),
        "basket": (
            has_dates and n_txn >= 50,
            "need dates and 50+ transactions for basket analysis"
        ),
    }
    return checks


# =============================================================================
# DATA LOADING & COLUMN DETECTION (Dataset-agnostic for any small business)
# =============================================================================

# Broad candidate lists to match diverse POS/export formats
PRODUCT_CANDIDATES = [
    "product", "item", "product_name", "item_name", "sku", "description",
    "beverage", "drink", "menu_item", "line_item", "product_desc", "item_desc",
    "article", "service",
    # common POS / ERP exports
    "product_code", "item_code", "item_number", "part_number", "product_title",
    "title", "label", "variant", "option",
    # Shopify: "Lineitem name" — "lineitem" is fused so we match it directly
    "lineitem_name", "lineitem name", "lineitem",
    # Lightspeed R / Vend: "Description" (also covers generic retail exports)
    "item_description", "product_description",
    # TouchBistro: "Menu Item Name"
    "menu_item_name",
    # Aloha / MICROS POS: "Menu Item", "Menu Item Name"
    "menu item", "menu item name",
    # NCR Silver / Heartland: "Item Name"  (also covers generic "item name")
    "item name",
    # Revel POS: "Product Name"
    "product name",
    # Vend (Lightspeed X): "Product Name" already covered; also "Variant Name"
    "variant_name", "variant name",
    # Clover / iZettle: "Item" already covered
    # WooCommerce: "Product Name" already covered
    # "category" removed — picks up Category ("Beverages") instead of product name
    # "name" and "goods" removed — match too broadly against customer_name, cost_of_goods, etc.
]
QTY_CANDIDATES = [
    "quantity", "qty", "units", "pieces", "volume",
    "qty_sold", "units_sold", "quantity_sold", "sold", "items_sold",
    # Aloha / NCR: "Item Count", "Num Items"
    "item_count", "item count", "num_items", "num items",
    # Heartland: "Units Ordered"
    "units_ordered", "units ordered",
    # iZettle / SumUp: "Items"
    "items",
    # "count" removed — substring of "account"/"discount"; "num" removed — too ambiguous
]
REVENUE_CANDIDATES = [
    "revenue", "extended_price", "line_total",
    "subtotal", "price_total", "gross_sales", "revenue_total", "sale_amount",
    "extended", "line_amount", "net_sales", "net_amount", "sale_total",
    "total_price", "total_revenue", "net_revenue",
    "invoice_total", "line_value", "amount_paid", "total_amount",
    # Toast exports: "Net Amount", "Gross Amount"
    "gross_amount",
    # Square exports: "Net Sales"  (already covered by net_sales)
    # Lightspeed: "Net Total", "Total Retail Price"
    "net_total", "total_retail_price",
    # WooCommerce/generic: "Order Total Amount"
    "order_total_amount",
    # Aloha / MICROS: "Item Total", "Check Amount", "Net Sales"
    "item_total", "item total", "check_amount", "check amount",
    # Heartland: "Transaction Amount", "Sale Amount"
    "transaction_amount", "transaction amount",
    # TouchBistro: "Ticket Total", "Net Total"
    "ticket_total", "ticket total",
    # NCR Silver: "Sales Amount", "Total Sales"
    "sales_amount", "sales amount", "total_sales", "total sales",
    # Revel POS: "Final Price"
    "final_price", "final price",
    # iZettle / SumUp: "Price"  — excluded (too ambiguous, matches unit_price)
    # "gross" removed — matches "Gross Profit", "Gross Margin" (accounting columns, not revenue)
    # "sales" removed — matches "Sales Tax" column (cand_words {"sales"} ⊆ {"sales","tax"})
    # "total" removed — matches "total_discount", "total_tax"; "value" → "value_added_tax"
    # "payment" removed — matches "payment_method"
]
UNIT_PRICE_CANDIDATES = [
    "unit_price", "unit price", "unitprice", "price_per_unit",
    "selling_price", "sale_price", "retail_price", "list_price", "price",
    "unit_rate", "each_price",
    # Vend / Lightspeed X: "Price"  (already covered by "price")
    # NCR Silver: "Item Price"
    "item_price", "item price",
    # "rate" removed — matches tax_rate, discount_rate, exchange_rate
]
DATE_CANDIDATES = [
    "date", "timestamp", "datetime", "order_date", "transaction_date",
    "sale_date", "created_at", "order_time", "transaction_time",
    "invoice_date", "purchase_date", "sold_at", "completed_at",
    # Toast POS: "Business Date"
    "business_date", "business date",
    # Lightspeed R: "Receipt Date"
    "receipt_date", "receipt date",
    # TouchBistro: "Created Date", "Closed Date"
    "created_date", "created date", "closed_date", "closed date",
    # Aloha / MICROS: "Check Date"
    "check_date", "check date",
    # Shopify: "Closed At"  (already covered by closed_at); also "Paid At"
    "paid_at", "paid at",
    # NCR Silver: "Date Time"
    "date_time", "date time",
    # Heartland: "Date/Time" (slash makes detection hard; match via "date" candidate above)
    # Clover: "Payment Date"
    "payment_date", "payment date",
    # "time" removed — matches lead_time, response_time
    # "created" removed — matches created_by
]
LOCATION_CANDIDATES = [
    "location", "store", "outlet", "branch", "place", "site", "shop", "venue",
    "store_name", "store name", "warehouse", "region", "territory",
    # Aloha / Toast: "Restaurant", "Revenue Center"
    "restaurant", "revenue_center", "revenue center",
    # TouchBistro: "Dining Room"
    "dining_room", "dining room",
    # Lightspeed: "Register", "Location Name"
    "register", "location_name", "location name",
    # Revel: "Establishment"
    "establishment",
]
COST_CANDIDATES = [
    "cost", "cogs", "unit_cost", "cost_price", "cost_of_goods", "purchase_price",
    "buying_price", "wholesale", "cost_per_unit", "item_cost", "direct_cost",
    "variable_cost", "product_cost",
    # Lightspeed / Vend: "Cost of Goods"
    "cost of goods",
    # generic: "COGS Amount"
    "cogs_amount", "cogs amount",
]
# Transaction / order ID candidates — used for market basket analysis when available.
# Supported POS systems: Square ("Transaction ID"), Shopify ("Order ID"),
# Toast ("Check ID"), Clover ("Order ID"), Lightspeed ("Order Number"),
# Revel ("Order ID"), TouchBistro ("Check #"), Aloha ("Check Number"),
# NCR Silver ("Order Number"), Heartland ("Transaction ID"), iZettle ("Payment ID").
TRANSACTION_CANDIDATES = [
    "transaction_id", "transaction id", "order_id", "order id",
    "check_id", "check id", "check_number", "check number", "check#",
    "check_num", "check_no",
    "order_number", "order number", "receipt_id", "receipt id",
    "invoice_id", "invoice id", "ticket_id", "ticket id",
    "sale_id", "sale id", "visit_id", "visit id",
    # TouchBistro: "Ticket Number"
    "ticket_number", "ticket number", "ticket_num", "ticket num",
    # Revel: "POS ID", "Order ID" (already covered)
    "pos_id", "pos id",
    # Aloha: "Check #" → normalized to "check num" by _normalize_col_name
    "check num",
    # Aloha: "Tab ID"
    "tab_id", "tab id",
    # iZettle / SumUp: "Payment ID", "Transaction Reference"
    "payment_id", "payment id", "transaction_reference", "transaction reference",
    # NCR Silver: "Transaction Number"
    "transaction_number", "transaction number",
]
# Product-name values that are accounting/POS summary rows, not real products.
# Matched case-insensitively as exact strings after stripping whitespace.
AGGREGATE_ROW_NAMES = {
    "total", "subtotal", "sub-total", "sub total",
    "grand total", "grand-total",
    "tax", "sales tax", "vat", "gst", "hst",
    "discount", "discount total",
    "shipping", "shipping & handling", "shipping and handling",
    "freight", "delivery",
    "tip", "gratuity",
    "refund", "return",
    "adjustment", "misc", "miscellaneous",
    "service charge", "service fee",
    "surcharge", "fee",
}


def _normalize_col_name(s: str) -> str:
    """Normalize a column name for word-set matching.

    Converts slashes, hashes, dots, and hyphens to spaces so that
    'Date/Time' → 'date time', 'Check #' → 'check num', 'Net-Sales' → 'net sales'.
    """
    s = s.lower().strip()
    s = s.replace("/", " ").replace("\\", " ")
    s = s.replace("#", " num ").replace("№", " num ")
    s = s.replace("-", " ").replace(".", " ")
    # Collapse multiple spaces
    return " ".join(s.split())


def _find_col(df: pd.DataFrame, candidates: list) -> str | None:
    """Find first column whose name (lowercase) contains any candidate.

    Normalizes spaces ↔ underscores and handles POS-specific separators
    (slash, hash, hyphen, dot) so columns like 'Date/Time' match 'date',
    'Check #' matches 'check_number', and 'Net-Sales' matches 'net_sales'.
    """
    cols_lower = {c.lower().strip(): c for c in df.columns if isinstance(c, str)}
    # Pre-compute normalized form for each column (slash/hash/etc → space)
    cols_normalized = {k: _normalize_col_name(k) for k in cols_lower}
    for cand in candidates:
        cand_norm = cand.replace("_", " ")          # underscore → space variant
        for k, v in cols_lower.items():
            k_norm = k.replace(" ", "_")            # space → underscore variant of column
            k_clean = cols_normalized[k]            # slash/hash/hyphen normalized form
            # Tokenize into word sets for whole-word matching in both directions
            cand_words = set(cand_norm.split())
            k_words = set(k.split())
            k_norm_words = set(k_norm.split("_"))
            k_clean_words = set(k_clean.split())
            if (
                # Forward: candidate words must all be whole words in the column name
                cand_words.issubset(k_words)
                or cand_words.issubset(k_norm_words)
                or cand_words.issubset(k_clean_words)
                # Reverse: column name words must all be whole words in the candidate.
                # Require ≥2 column words so single-word columns ("sales", "price",
                # "date") don't spuriously match every candidate that contains that
                # word (e.g. "sales" would otherwise match both "gross_sales" and
                # "net_sales" — whichever candidate comes first wins).
                or (len(k) >= 4 and len(k_words) >= 2 and k_words.issubset(cand_words))
                or (len(k_norm) >= 4 and len(k_norm_words) >= 2 and k_norm_words.issubset(cand_words))
                or (len(k_clean) >= 4 and len(k_clean_words) >= 2 and k_clean_words.issubset(cand_words))
            ):
                return v
    return None


def _detect_columns(df: pd.DataFrame) -> dict:
    """Auto-detect columns for product, quantity, revenue/unit_price, date, location, cost, transaction_id."""
    product_col = _find_col(df, PRODUCT_CANDIDATES)
    if product_col is None:
        # Special case: column named exactly "Name" (Square, Lightspeed exports) — but
        # only when no customer-name column exists that could be confused with it.
        name_col = next((c for c in df.columns if c.strip().lower() == "name"), None)
        if name_col and not any("customer" in c.lower() or "client" in c.lower() for c in df.columns):
            product_col = name_col
    mapping = {
        "product": product_col or (df.columns[0] if len(df.columns) > 0 else None),
        "quantity": _find_col(df, QTY_CANDIDATES),
        "revenue": _find_col(df, REVENUE_CANDIDATES),
        "unit_price": _find_col(df, UNIT_PRICE_CANDIDATES),
        "date": _find_col(df, DATE_CANDIDATES),
        "location": _find_col(df, LOCATION_CANDIDATES),
        "cost": _find_col(df, COST_CANDIDATES),
        "transaction_id": _find_col(df, TRANSACTION_CANDIDATES),
    }
    # Avoid using same column for revenue and unit_price
    if mapping["revenue"] and mapping["unit_price"] and mapping["revenue"] == mapping["unit_price"]:
        mapping["revenue"] = None
    # Avoid cost shadowing unit_price or revenue
    if mapping["cost"] and mapping["cost"] in (mapping["revenue"], mapping["unit_price"]):
        mapping["cost"] = None
    return mapping


_NON_NUMERIC_STRINGS = frozenset(
    ["n/a", "#n/a", "#value!", "#ref!", "#div/0!", "#name?", "#null!", "#num!", "na", "nan", "none", "null", "-", ""]
)

def _parse_numeric(series: pd.Series) -> pd.Series:
    """Parse numeric values, stripping currency symbols, commas, and accounting parentheses.

    Handles:
    - Common currency symbols: $, €, £, ₹, ¥, ₩, ₱, ₺, ₿, kr, CHF, R$, etc.
    - Accounting format: (1,234.56) → -1234.56
    - European format: 1.234,56 → 1234.56 (detected when comma is last separator)
    - Unicode minus and non-breaking spaces
    """
    _CURRENCY_PREFIXES = frozenset(["$", "€", "£", "₹", "¥", "₩", "₱", "₺", "₿", "฿",
                                     "R$", "A$", "C$", "NZ$", "HK$", "S$", "kr", "CHF", "Fr"])

    def clean(x):
        if pd.isna(x):
            return np.nan
        s = str(x).strip()
        if s.lower() in _NON_NUMERIC_STRINGS:
            return np.nan
        # Accounting format: (1,234.56) → -1234.56
        negative = s.startswith("(") and s.endswith(")")
        s = s.replace("(", "").replace(")", "")
        # Unicode minus (U+2212) → ASCII minus
        s = s.replace("\u2212", "-")
        # Non-breaking and regular spaces as thousands separators
        s = s.replace("\u00a0", "").replace(" ", "")
        # Strip multi-char currency prefixes before single-char ones
        for sym in ("R$", "A$", "C$", "NZ$", "HK$", "S$", "kr", "CHF", "Fr"):
            s = s.replace(sym, "")
        # Strip single-char currency symbols and percent
        s = s.replace("$", "").replace("€", "").replace("£", "").replace("₹", "") \
             .replace("¥", "").replace("₩", "").replace("₱", "").replace("₺", "") \
             .replace("₿", "").replace("฿", "").replace("%", "")
        # Detect European format: 1.234,56 (period=thousands, comma=decimal)
        # Heuristic: if there's a comma after the last period, it's European format
        if "," in s and "." in s:
            last_comma = s.rfind(",")
            last_period = s.rfind(".")
            if last_comma > last_period:
                # European: "1.234,56" → "1234.56"
                s = s.replace(".", "").replace(",", ".")
            else:
                # US/standard: "1,234.56" → "1234.56"
                s = s.replace(",", "")
        elif "," in s:
            # Only commas present — ambiguous between thousands separator ("1,000") and
            # European decimal separator ("1,5" or "1,50").
            # Heuristic:
            #   • Exactly 3 digits after comma → thousands separator ("1,000" → 1000)
            #   • 1 digit after comma          → European decimal    ("1,5"   → 1.5)
            #   • 2 digits after comma         → ambiguous ("1,00" could be 1.00 or a
            #     truncated thousands form); treated as European decimal because a
            #     3-digit thousands group would be the far more common encoding and
            #     would have exactly 3 digits. Users with US-format "1,00" data should
            #     ensure values use standard 3-digit grouping (e.g. "1,000").
            parts = s.split(",")
            if len(parts) == 2 and len(parts[1]) == 3:
                s = s.replace(",", "")           # thousands separator: "1,000" → "1000"
            elif len(parts) == 2 and len(parts[1]) <= 2:
                s = parts[0] + "." + parts[1]   # European decimal: "1,5" or "1,50" → "1.5"/"1.50"
            else:
                s = s.replace(",", "")           # multiple commas → strip all (thousands)
        try:
            val = float(s)
            return -val if negative else val
        except ValueError:
            return np.nan
    return series.apply(clean)


@st.cache_data(ttl=600)
def _excel_sheet_names(file_bytes: bytes, file_name: str) -> list[str]:
    """Return sheet names for an Excel file."""
    buf = io.BytesIO(file_bytes)
    try:
        engine = "openpyxl" if file_name.lower().endswith(".xlsx") else None
        xl = pd.ExcelFile(buf, engine=engine)
        return xl.sheet_names
    except Exception:
        return []


@st.cache_data(ttl=600)
def _load_raw_cached(file_bytes: bytes, file_name: str, sheet_name: str | None = None) -> pd.DataFrame | None:
    """Cached file loader — avoids re-reading when switching pages."""
    buf = io.BytesIO(file_bytes)
    name = (file_name or "").lower()
    try:
        if name.endswith(".xlsx"):
            return pd.read_excel(buf, engine="openpyxl", sheet_name=sheet_name or 0)
        if name.endswith(".xls"):
            try:
                return pd.read_excel(buf, sheet_name=sheet_name or 0)
            except ImportError:
                st.error("This file format (.xls) isn't supported in the current setup. Try saving your file as .xlsx or .csv and uploading again.")
                return None
        # Try common encodings and separators (handles European POS semicolon exports)
        for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
            for sep in (",", ";", "\t"):
                try:
                    buf.seek(0)
                    df_try = pd.read_csv(buf, encoding=enc, sep=sep)
                    # Accept if we got at least 2 columns (single column = wrong separator)
                    if len(df_try.columns) >= 2:
                        return df_try
                except Exception:
                    continue
        return None
    except Exception:
        return None


def load_raw_file(uploaded_file) -> pd.DataFrame | None:
    """Load CSV or Excel file into a DataFrame."""
    try:
        raw = uploaded_file.getvalue()
    except Exception:
        raw = uploaded_file.read()
    fname = uploaded_file.name or ""
    sheet_name = None
    if fname.lower().endswith((".xlsx", ".xls")):
        sheets = _excel_sheet_names(raw, fname)
        if len(sheets) > 1:
            sheet_name = st.selectbox(
                "This workbook has multiple sheets — select one to load:",
                sheets,
                key="excel_sheet_selector",
            )
    df = _load_raw_cached(raw, fname, sheet_name)
    if df is None:
        st.error("We couldn't read this file. Try saving it as .csv and uploading again.")
        return None
    if df.empty:
        st.error("The file is empty.")
        return None
    return df


def _prepare_data_impl(raw_df: pd.DataFrame, mapping_override: dict | None) -> tuple[pd.DataFrame | None, str | None]:
    """Inner logic for data prep. Returns (df, None) on success, (None, error_msg) on failure."""
    auto_mapping = _detect_columns(raw_df)
    mapping = {**auto_mapping, **(mapping_override or {})}  # user override takes precedence

    product_col = mapping.get("product")
    if not product_col or product_col not in raw_df.columns:
        return None, "Select a **Product** column (e.g. item name, SKU) in the sidebar."

    needed = {"product": raw_df[product_col].astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)}

    # Quantity (optional, default 1)
    qty_col = mapping.get("quantity")
    if qty_col and qty_col in raw_df.columns:
        needed["quantity"] = _parse_numeric(raw_df[qty_col]).fillna(1).clip(lower=0)
    else:
        needed["quantity"] = pd.Series(1, index=raw_df.index)

    # Revenue: direct column, or unit_price × quantity
    rev_col = mapping.get("revenue")
    up_col = mapping.get("unit_price")
    if rev_col and rev_col in raw_df.columns:
        needed["revenue"] = _parse_numeric(raw_df[rev_col]).fillna(0)
    elif up_col and up_col in raw_df.columns:
        unit_price = _parse_numeric(raw_df[up_col]).fillna(0)
        needed["revenue"] = unit_price * needed["quantity"]
    else:
        return None, "Select either a **Revenue/Total** column or a **Unit price** column in the sidebar."

    # Date (optional)
    _date_dayfirst_detected = False
    date_col = mapping.get("date")
    if date_col and date_col in raw_df.columns:
        raw_date_series = raw_df[date_col]
        # Try standard parse first (month-first for US formats, ISO, etc.)
        _parsed_mf = pd.to_datetime(raw_date_series, errors="coerce", dayfirst=False)
        # Try day-first parse (European dd/mm/yyyy)
        _parsed_df = pd.to_datetime(raw_date_series, errors="coerce", dayfirst=True)

        # Count how many dates parse successfully with each strategy
        n_mf = _parsed_mf.notna().sum()
        n_df = _parsed_df.notna().sum()

        # Check if the two interpretations disagree on any row
        both_valid = _parsed_mf.notna() & _parsed_df.notna()
        n_disagree = (both_valid & (_parsed_mf != _parsed_df)).sum()

        if n_disagree > 0 and n_df > n_mf:
            # Day-first parsed more dates — likely European format
            _parsed = _parsed_df
            _date_dayfirst_detected = True
        elif n_disagree > 0 and n_mf >= n_df:
            # Ambiguous but month-first parsed at least as many — keep month-first
            _parsed = _parsed_mf
        else:
            # No disagreement or only one parse worked — use whichever got more
            _parsed = _parsed_mf if n_mf >= n_df else _parsed_df

        # If the column has mixed-tz or tz-aware strings, normalize to UTC then strip.
        if getattr(_parsed.dt, "tz", None) is not None:
            _parsed = _parsed.dt.tz_convert("UTC").dt.tz_localize(None)
        needed["date"] = _parsed
    else:
        needed["date"] = pd.Series(pd.NaT, index=raw_df.index)

    # Filter future dates — data entry errors or scheduled transactions
    if date_col and needed["date"].notna().any():
        _tomorrow = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)
        _future_mask = needed["date"] > _tomorrow
        _n_future = _future_mask.sum()
        if _n_future > 0:
            needed["date"] = needed["date"].where(~_future_mask, pd.NaT)
            st.session_state["_future_dates_stripped"] = int(_n_future)

    # Location (optional)
    loc_col = mapping.get("location")
    if loc_col and loc_col in raw_df.columns:
        needed["location"] = raw_df[loc_col].astype(str)
    else:
        needed["location"] = pd.Series("All", index=raw_df.index)

    # Cost (optional — enables profit/margin analysis)
    cost_col = mapping.get("cost")
    if cost_col and cost_col in raw_df.columns:
        needed["cost"] = _parse_numeric(raw_df[cost_col]).fillna(np.nan).clip(lower=0)
    else:
        needed["cost"] = pd.Series(np.nan, index=raw_df.index)

    # Transaction ID (optional — improves market basket accuracy when available)
    txn_col = mapping.get("transaction_id")
    if txn_col and txn_col in raw_df.columns:
        needed["transaction_id"] = raw_df[txn_col].astype(str).str.strip()
    else:
        needed["transaction_id"] = pd.Series(None, index=raw_df.index, dtype=object)

    out = pd.DataFrame(needed)
    n_date_dropped = 0
    n_parsed = 0
    if date_col:
        n_parsed = out["date"].notna().sum()
        if n_parsed > 0:
            n_date_dropped = out["date"].isna().sum()
            out = out[out["date"].notna()]
        else:
            # Date column was detected but nothing parsed — don't filter, just warn via attr
            out["date"] = pd.NaT
    n_before = len(out)
    _BAD_PRODUCTS = {
        "nan", "none", "null", "n/a", "#n/a", "#value!", "#ref!", "#div/0!",
        "#name?", "#null!", "#num!", "undefined", "-", "na",
    }
    out = out[~out["product"].str.strip().str.lower().isin(_BAD_PRODUCTS)]
    out = out[out["product"].str.strip().str.len() > 0]
    n_no_product = n_before - len(out)
    n_before2 = len(out)
    out = out[~out["product"].str.strip().str.lower().isin(AGGREGATE_ROW_NAMES)]
    n_aggregate = n_before2 - len(out)
    n_before2 = len(out)
    out = out[out["revenue"].notna() & np.isfinite(out["revenue"]) & (out["revenue"] > 0)]
    n_no_revenue = n_before2 - len(out)
    if out.empty:
        parts = ["No valid rows after filtering."]
        if date_col and n_parsed == 0:
            parts.append(f"Date column **'{date_col}'** was detected but 0 values could be parsed — check the date format in your file.")
        if n_no_product:
            parts.append(f"{n_no_product} rows had empty/null product names.")
        if n_aggregate:
            parts.append(f"{n_aggregate} summary/aggregate rows (Total, Tax, etc.) were excluded.")
        if n_no_revenue:
            parts.append(f"{n_no_revenue} rows had zero or negative revenue/price values.")
        return None, " ".join(parts)
    warning_parts = []
    _n_future_stripped = st.session_state.pop("_future_dates_stripped", 0)
    if _n_future_stripped > 0:
        warning_parts.append(
            f"{_n_future_stripped} row(s) had dates in the future and were excluded. "
            "Check your data for entry errors or scheduled transactions."
        )
    if _date_dayfirst_detected:
        warning_parts.append(
            f"Dates in column '{date_col}' appear to use dd/mm/yyyy format. "
            f"We're interpreting them as day-first (European). "
            f"If your dates are mm/dd/yyyy (US), re-map the date column in the sidebar."
        )
    if n_date_dropped > 0:
        warning_parts.append(f"{n_date_dropped} rows had unparseable dates and were excluded — check the date format in column '{date_col}'.")
    if n_no_product:
        warning_parts.append(f"{n_no_product} rows with empty/null product names were excluded.")
    if n_aggregate:
        warning_parts.append(f"{n_aggregate} summary rows (Total, Tax, Shipping, etc.) were excluded.")
    if n_no_revenue:
        warning_parts.append(f"{n_no_revenue} rows with zero or negative revenue were excluded (refunds, comps, or free items).")
    # Warn when a bare "price" column (common POS line-total label) was multiplied by
    # quantity — this double-counts revenue on multi-unit rows.
    _AMBIGUOUS_UNIT_PRICE_NAMES = {"price", "item_price", "item price"}
    if (
        up_col and not rev_col
        and up_col.lower().strip() in _AMBIGUOUS_UNIT_PRICE_NAMES
        and qty_col and (out["quantity"] != 1).any()
    ):
        warning_parts.append(
            f"\u26a0\ufe0f Column **\u2018{up_col}\u2019** was used as *unit price* and multiplied by quantity. "
            f"In Square, Shopify, and Toast exports \u2018{up_col}\u2019 is often the **line total** (already qty \xd7 price), "
            f"which would inflate revenue. If totals look too high, map the Revenue column manually in the sidebar."
        )
    return out, " ".join(warning_parts) if warning_parts else None


@st.cache_data(
    ttl=600,
    hash_funcs={pd.DataFrame: lambda df: pd.util.hash_pandas_object(df, index=True).sum()},
)
def _prepare_cached(raw_df: pd.DataFrame, mapping_tuple: tuple) -> tuple[pd.DataFrame | None, str | None]:
    """Cached data preparation."""
    mapping = dict(mapping_tuple) if mapping_tuple else None
    return _prepare_data_impl(raw_df, mapping)


def prepare_data(raw_df: pd.DataFrame, mapping_override: dict | None = None) -> pd.DataFrame | None:
    """Prepare raw DataFrame for analysis. Uses cache for fast navigation."""
    mapping_tuple = tuple(sorted((mapping_override or {}).items()))
    result, msg = _prepare_cached(raw_df, mapping_tuple)
    if result is None and msg:
        st.error(msg)
        with st.expander("🔍 Data preview — check your column mapping"):
            st.caption("Columns in your file:")
            st.code(", ".join(raw_df.columns.tolist()))
            st.dataframe(raw_df.head(5), use_container_width=True)
    elif result is not None and msg:
        st.warning(msg)
    return result


# =============================================================================
# AI BRIEF — Proactive executive summary on data load
# =============================================================================

def _generate_ai_brief(data_context: str) -> dict:
    """
    Generate 3 priorities + 1 risk + 1 opportunity from business data.
    Cached in session_state by MD5 hash of context.
    Returns dict with keys: actions (list), risk (str), opportunity (str).
    On error returns {"error": reason}.
    """
    ctx_hash = hashlib.md5(data_context.encode()).hexdigest()[:12]
    cache_key = f"ai_brief_{ctx_hash}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    model = _get_groq_client()
    if model is None:
        result = {"error": "api_key"}
        st.session_state[cache_key] = result
        return result

    system_context = (
        "You are a sharp small business advisor reviewing real sales data. "
        "Your only job is to give specific, actionable recommendations. "
        "RULES:\n"
        "1. Never give generic advice. Every recommendation must reference "
        "a specific product name AND a specific number from the data.\n"
        "2. Start every ACTION with a verb (Raise, Promote, Cut, Bundle, etc.).\n"
        "3. Keep each point to 1-2 sentences maximum.\n"
        "4. Plain English only — no jargon, no technical terms."
    )

    prompt = (
        f"{system_context}\n\n"
        f"{data_context}\n\n"
        "Based ONLY on the numbers above, respond EXACTLY in this format "
        "(no intro, no extra text):\n"
        "ACTION 1: [verb-first action — must name a real product AND cite a specific number]\n"
        "ACTION 2: [verb-first action — must name a real product AND cite a specific number]\n"
        "ACTION 3: [verb-first action — must name a real product AND cite a specific number]\n"
        "RISK: [one sentence naming the specific product or metric at risk, with a number]\n"
        "OPPORTUNITY: [one sentence — name the product and the estimated dollar opportunity]"
    )

    result: dict = {"actions": [], "risk": "", "opportunity": ""}
    try:
        response = _groq_generate(model, prompt)
        raw_text = response.text.strip()
        for line in raw_text.splitlines():
            line = line.strip()
            for tag in ("ACTION 1:", "ACTION 2:", "ACTION 3:"):
                if line.upper().startswith(tag):
                    result["actions"].append(line[len(tag):].strip())
            if line.upper().startswith("RISK:"):
                result["risk"] = line[5:].strip()
            if line.upper().startswith("OPPORTUNITY:"):
                result["opportunity"] = line[12:].strip()

        # If parsing found nothing useful, try to salvage by treating the whole
        # response as a single action (the model may have ignored the format)
        if not result["actions"] and raw_text:
            # Split into sentences and take up to 3 as actions
            sentences = [s.strip() for s in raw_text.replace("\n", " ").split(".") if len(s.strip()) > 20]
            result["actions"] = sentences[:3] if sentences else []
            if not result["actions"]:
                result["error"] = "ai_format_error"
    except Exception as exc:
        result = {"error": "AI summary is temporarily unavailable. Your data analysis still works normally."}

    st.session_state[cache_key] = result
    return result


def _validate_brief_specificity(actions: list, df: pd.DataFrame) -> list:
    """Check each AI Brief action for specificity. Returns annotated list."""
    product_names = set(df["product"].str.lower().unique())
    validated = []
    for action in actions:
        action_lower = action.lower()
        has_product = any(p in action_lower for p in product_names)
        has_number = bool(re.search(r'\$[\d,]+|\d{2,}', action))
        if has_product and has_number:
            validated.append(action)
        elif has_product or has_number:
            validated.append(action)  # partially specific — keep without warning
        else:
            validated.append(f"{action} *(tip: verify this references your actual products)*")
    return validated


# =============================================================================
# PRODUCT SPARKLINE HELPER
# =============================================================================

def _product_sparkline(df: pd.DataFrame, product: str) -> "go.Figure | None":
    """Mini weekly-revenue line chart for a single product (no axes, no margins)."""
    if not _has_dates(df):
        return None
    prod_df = df[df["product"] == product].copy()
    prod_df["week"] = prod_df["date"].dt.to_period("W").dt.start_time
    weekly = prod_df.groupby("week")["revenue"].sum().reset_index()
    if len(weekly) < 2:
        return None
    fig = go.Figure(go.Scatter(
        x=weekly["week"], y=weekly["revenue"],
        mode="lines",
        line=dict(color="#2563eb", width=2, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(37,99,235,0.06)",
        hovertemplate=_cur() + "%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        height=110,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x",
    )
    return fig


# =============================================================================
# EXPORT HELPER
# =============================================================================

def _build_export_df(df: pd.DataFrame, product_clusters) -> pd.DataFrame:
    """Merge product aggregates + cluster labels into a downloadable CSV."""
    agg = (
        df.groupby("product")
        .agg(quantity=("quantity", "sum"), revenue=("revenue", "sum"),
             transactions=("revenue", "count"))
        .reset_index()
    )
    agg["avg_price"]       = agg["revenue"]      / agg["quantity"].replace(0, float("nan"))
    agg["avg_order_value"] = agg["revenue"]      / agg["transactions"].clip(lower=1)
    if product_clusters is not None:
        cat_map        = product_clusters.set_index("product")["category"].to_dict()
        agg["category"] = agg["product"].map(cat_map).fillna("Uncategorized")
    return agg.sort_values("revenue", ascending=False)


# =============================================================================
# 1. REVENUE AGGREGATION — Overview Dashboard
# =============================================================================

def _render_ai_brief_expander(
    df: pd.DataFrame,
    product_clusters,
    *,
    button_key: str,
) -> None:
    """Shared AI Business Brief expander used by Overview and Action Center."""
    # Silently skip if no API key — never show config instructions to a client
    api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        return

    with st.expander("🤖 Your top 3 priorities this week", expanded=True):
        data_ctx = _build_data_context(df, product_clusters)
        profile_ctx = _build_profile_context()
        if profile_ctx:
            data_ctx = f"{profile_ctx}\n\nBUSINESS DATA:\n{data_ctx}"
        brief_cache_key = f"ai_brief_{hashlib.md5(data_ctx.encode()).hexdigest()[:12]}"
        brief = st.session_state.get(brief_cache_key)
        if brief is None:
            with st.spinner("Generating your business brief..."):
                brief = _generate_ai_brief(data_ctx)
                st.session_state[brief_cache_key] = brief

        if brief and "error" in brief:
            st.warning("AI summary is temporarily unavailable — your recommendations are unaffected.")
        elif brief:
            if brief.get("actions"):
                validated_actions = _validate_brief_specificity(brief["actions"], df)
                st.markdown("**This week's top priorities:**")
                for i, action in enumerate(validated_actions, 1):
                    st.success(f"**#{i}** {action}")
            if brief.get("risk"):
                st.warning(f"**⚠️ Watch out:** {brief['risk']}")
            if brief.get("opportunity"):
                st.info(f"**💡 Opportunity:** {brief['opportunity']}")
            st.caption(_build_data_confidence_badge(df))


def _suggest_anomaly_label(date_str: str, direction: str, z_score: float, top_product: str) -> str:
    """Return a short plain-English auto-label for an anomaly (max 60 chars)."""
    try:
        date = pd.Timestamp(date_str)
        month, day = date.month, date.day
        weekday = date.day_name()

        def _tp(template: str) -> str:
            if top_product:
                result = template.replace("{top_product}", top_product)
            else:
                result = (
                    template
                    .replace("{top_product} spike — ", "Spike — ")
                    .replace(" — {top_product}", "")
                    .replace("{top_product} ", "")
                    .replace("{top_product}", "")
                )
            return result[:60]

        def _easter_sunday(year: int) -> pd.Timestamp:
            a = year % 19
            b = year // 100
            c = year % 100
            d = b // 4
            e = b % 4
            f = (b + 8) // 25
            g = (b - f + 1) // 3
            h = (19 * a + b - d - g + 15) % 30
            i = c // 4
            k = c % 4
            l = (32 + 2 * e + 2 * i - h - k) % 7
            m = (a + 11 * h + 22 * l) // 451
            month_e = (h + l - 7 * m + 114) // 31
            day_e = ((h + l - 7 * m + 114) % 31) + 1
            return pd.Timestamp(year, month_e, day_e)

        def _nth_weekday(year: int, mnth: int, weekday_n: int, n: int) -> pd.Timestamp:
            import calendar
            first_day, _ = calendar.monthrange(year, mnth)
            first_wd = (weekday_n - first_day) % 7
            day_n = first_wd + 1 + (n - 1) * 7
            return pd.Timestamp(year, mnth, day_n)

        def _last_thursday(year: int, mnth: int) -> pd.Timestamp:
            import calendar
            _, num_days = calendar.monthrange(year, mnth)
            for d in range(num_days, 0, -1):
                if pd.Timestamp(year, mnth, d).day_name() == "Thursday":
                    return pd.Timestamp(year, mnth, d)
            return pd.Timestamp(year, mnth, 1)

        if direction == "spike":
            if month == 2 and day == 14:
                return _tp("{top_product} spike — Valentine's Day effect?")
            if month == 12 and day in (24, 25):
                return "Holiday rush — Christmas effect?"
            if (month == 12 and day == 31) or (month == 1 and day == 1):
                return "New Year's spike?"
            if month == 11:
                last_thu = _last_thursday(date.year, 11)
                black_fri = last_thu + pd.Timedelta(days=1)
                if date.date() in (last_thu.date(), black_fri.date()):
                    return "Thanksgiving / Black Friday effect?"
            if month == 10 and day == 31:
                return "Halloween spike?"
            if month in (3, 4):
                easter = _easter_sunday(date.year)
                if abs((date - easter).days) <= 3:
                    return "Easter effect?"
            if month == 5:
                mothers = _nth_weekday(date.year, 5, 6, 2)
                if date.date() == mothers.date():
                    return "Mother's Day spike?"
            if month == 6:
                fathers = _nth_weekday(date.year, 6, 6, 3)
                if date.date() == fathers.date():
                    return "Father's Day spike?"
            if weekday in ("Friday", "Saturday"):
                return _tp("Weekend spike — {top_product}?")
            if z_score > 4:
                return "Major spike — special event or promotion?"
            return "Above-normal day — promotion or event?"
        else:
            if weekday == "Monday":
                return "Monday dip — normal for your pattern?"
            if month == 1 and 1 <= day <= 7:
                return "Post-holiday slowdown?"
            if z_score > 4:
                return "Major dip — closure or supply issue?"
            return "Quiet day — check for a pattern?"
    except Exception:
        return "Unusual day — worth investigating?"


def _log_anomalies(df: pd.DataFrame, anomalies: list, upload_label: str = "") -> int:
    """Write new anomaly entries into st.session_state.anomaly_log. Returns count added."""
    if "date" not in df.columns:
        return 0
    existing_ids = {e["id"] for e in st.session_state.anomaly_log}
    daily_rev = df.groupby(df["date"].dt.date)["revenue"].sum()
    median_daily = float(daily_rev.median()) if not daily_rev.empty else 0.0

    newly_added = 0
    for a in anomalies:
        entry_id = hashlib.md5(f"{a['date']}{a['direction']}".encode()).hexdigest()[:8]
        if entry_id in existing_ids:
            continue
        top_product = ""
        try:
            day_mask = df["date"].dt.date == pd.Timestamp(a["date"]).date()
            if day_mask.any():
                top_product = df[day_mask].groupby("product")["revenue"].sum().idxmax()
        except Exception:
            top_product = ""
        pct_above = 0.0
        if median_daily != 0:
            pct_above = ((a["revenue"] - median_daily) / median_daily) * 100
        auto_label = _suggest_anomaly_label(a["date"], a["direction"], a["z_score"], top_product)
        try:
            date_label = pd.Timestamp(a["date"]).strftime("%b %-d, %Y")
        except ValueError:
            date_label = pd.Timestamp(a["date"]).strftime("%b %d, %Y").replace(" 0", " ")
        entry = {
            "id":           entry_id,
            "date":         a["date"],
            "date_label":   date_label,
            "direction":    a["direction"],
            "revenue":      float(a["revenue"]),
            "z_score":      float(a["z_score"]),
            "pct_above":    float(pct_above),
            "top_product":  str(top_product),
            "note":         "",
            "auto_label":   auto_label,
            "logged_at":    pd.Timestamp.now().isoformat(),
            "upload_label": upload_label,
        }
        st.session_state.anomaly_log.append(entry)
        existing_ids.add(entry_id)
        newly_added += 1

    st.session_state.anomaly_log.sort(key=lambda e: e["date"], reverse=True)
    if len(st.session_state.anomaly_log) > 200:
        st.session_state.anomaly_log = st.session_state.anomaly_log[:200]
    return newly_added


def _save_anomaly_note(entry_id: str, widget_key: str) -> None:
    new_note = st.session_state.get(widget_key, "")
    for entry in st.session_state.anomaly_log:
        if entry["id"] == entry_id:
            entry["note"] = new_note.strip()
            break


def _build_anomaly_csv() -> str:
    import csv
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "date", "direction", "auto_label", "revenue",
        "pct_above_normal", "z_score", "top_product",
        "note", "upload_label", "logged_at",
    ])
    for e in st.session_state.anomaly_log:
        writer.writerow([
            e["date"],
            e["direction"].capitalize(),
            e["auto_label"],
            f"{e['revenue']:.2f}",
            f"{e['pct_above']:+.1f}%",
            f"{e['z_score']:.2f}",
            e["top_product"],
            e.get("note", ""),
            e.get("upload_label", ""),
            e.get("logged_at", ""),
        ])
    return out.getvalue()


def _render_trend_anomaly_section(df: pd.DataFrame) -> None:
    """Render trend direction and anomaly expander for the Overview page."""
    insights = _detect_overview_insights(df)
    if not insights["has_dates"]:
        return
    st.markdown("---")
    st.subheader("How is your business trending?")

    trend_icon = {"upward": "📈", "downward": "📉", "flat": "➡️"}.get(insights["trend"], "➡️")
    for txt in insights["insights"]:
        st.info(f"{trend_icon} {txt}")

    if insights["anomalies"]:
        _log_anomalies(df, insights["anomalies"])
        with st.expander(f"⚡ {len(insights['anomalies'])} unusual day(s) in your sales history — click to review"):
            st.caption(
                "These days had unusually high or low sales compared to your normal pattern. "
                "Each one includes a suggested action — check your records before drawing conclusions."
            )
            for a in insights["anomalies"]:
                icon = "🔺" if a["direction"] == "spike" else "🔻"
                st.write(f"{icon} **{a['date']}** — {_cur()}{a['revenue']:,.2f}")
                z = a["z_score"]
                if a["direction"] == "spike":
                    action_tip = (
                        "Major spike — likely a special event, promotion, or bulk order. "
                        "Check your records for that date. If replicable, schedule it again."
                    ) if z > 3 else (
                        "Above-average day. Check if it falls on a recurring day of week or time of month — "
                        "if so, build a standing promotion for that window."
                    )
                else:
                    action_tip = (
                        "Unusually low day — likely a closure, holiday, or supply issue. "
                        "If unplanned, build a contingency: backup supplier or extended hours on adjacent days."
                    ) if z > 3 else (
                        "Quiet day. Check if this pattern repeats weekly — "
                        "if so, run a targeted promotion on that day (e.g. limited-time discount, bonus offer)."
                    )
                st.info(f"→ **Suggested action:** {action_tip}")

    if insights["recommendations"]:
        st.markdown("**💡 Recommended Action**")
        for rec in insights["recommendations"]:
            st.success(rec)


def _render_period_comparison(df: pd.DataFrame) -> None:
    """Period-over-period comparison widget for the Overview page."""
    if not _has_dates(df):
        return
    st.markdown("---")
    st.subheader("How do recent periods compare?")
    st.caption("See how your revenue, orders, and top product compare between any two date ranges.")

    pop_min   = df["date"].dt.date.min()
    pop_max   = df["date"].dt.date.max()
    pop_today = pd.Timestamp.today().normalize()

    _POP_PRESETS = [
        "Last 30 days vs Prior 30",
        "Last 7 days vs Prior 7",
        "This month vs Last month",
        "This quarter vs Last quarter",
        "Custom",
    ]
    pop_preset = st.selectbox("Preset", _POP_PRESETS, key="pop_preset")

    def _resolve(preset):
        t = pop_today
        if preset == "Last 30 days vs Prior 30":
            a_s = (t - pd.Timedelta(days=29)).date()
            a_e = t.date()
            b_e = (t - pd.Timedelta(days=30)).date()
            b_s = (t - pd.Timedelta(days=59)).date()
        elif preset == "Last 7 days vs Prior 7":
            a_s = (t - pd.Timedelta(days=6)).date()
            a_e = t.date()
            b_e = (t - pd.Timedelta(days=7)).date()
            b_s = (t - pd.Timedelta(days=13)).date()
        elif preset == "This month vs Last month":
            a_s = t.replace(day=1).date()
            a_e = t.date()
            b_e = (t.replace(day=1) - pd.Timedelta(days=1)).date()
            b_s = b_e.replace(day=1)
        elif preset == "This quarter vs Last quarter":
            qm = ((t.month - 1) // 3) * 3 + 1
            a_s = t.replace(month=qm, day=1).date()
            a_e = t.date()
            b_e = (t.replace(month=qm, day=1) - pd.Timedelta(days=1)).date()
            bqm = ((b_e.month - 1) // 3) * 3 + 1
            b_s = b_e.replace(month=bqm, day=1)
        else:  # Custom defaults to last 30 vs prior 30
            a_s = (t - pd.Timedelta(days=29)).date()
            a_e = t.date()
            b_e = (t - pd.Timedelta(days=30)).date()
            b_s = (t - pd.Timedelta(days=59)).date()
        ca_s = max(a_s, pop_min)
        ca_e = min(a_e, pop_max)
        cb_s = max(b_s, pop_min)
        cb_e = min(b_e, pop_max)
        # Clamp inverted ranges to nearest valid edge so the UI never shows an
        # empty default selection when today is far past the data window.
        if ca_s > ca_e:
            ca_s = ca_e = pop_max
        if cb_s > cb_e:
            cb_s = cb_e = pop_min
        return ca_s, ca_e, cb_s, cb_e

    a_s, a_e, b_s, b_e = _resolve(pop_preset)

    if pop_preset == "Custom":
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Period A**")
            a_s = st.date_input("Start", value=a_s, min_value=pop_min, max_value=pop_max, key="pop_a_s")
            a_e = st.date_input("End",   value=a_e, min_value=pop_min, max_value=pop_max, key="pop_a_e")
        with col_b:
            st.markdown("**Period B**")
            b_s = st.date_input("Start", value=b_s, min_value=pop_min, max_value=pop_max, key="pop_b_s")
            b_e = st.date_input("End",   value=b_e, min_value=pop_min, max_value=pop_max, key="pop_b_e")

    sub_a = df[(df["date"].dt.date >= a_s) & (df["date"].dt.date <= a_e)]
    sub_b = df[(df["date"].dt.date >= b_s) & (df["date"].dt.date <= b_e)]

    def _mets(sub):
        rev    = sub["revenue"].sum()
        orders = len(sub)
        avg_t  = rev / orders if orders else 0.0
        top_p  = sub.groupby("product")["revenue"].sum().idxmax() if not sub.empty else "—"
        return rev, orders, avg_t, top_p

    def _dpct(a, b):
        return (a - b) / b * 100 if b else None

    pa_rev, pa_ord, pa_avg, pa_top = _mets(sub_a)
    pb_rev, pb_ord, pb_avg, pb_top = _mets(sub_b)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**Period A** — {a_s} → {a_e}")
        if sub_a.empty:
            st.warning("No data in this date range.")
        else:
            d_rev = _dpct(pa_rev, pb_rev)
            d_ord = _dpct(pa_ord, pb_ord)
            d_avg = _dpct(pa_avg, pb_avg)
            st.metric("Revenue",     f"{_cur()}{pa_rev:,.2f}", delta=f"{d_rev:+.1f}% vs B" if d_rev is not None else None)
            st.metric("Orders",      f"{pa_ord:,}",            delta=f"{d_ord:+.1f}% vs B" if d_ord is not None else None)
            st.metric("Avg Ticket",  f"{_cur()}{pa_avg:.2f}",  delta=f"{d_avg:+.1f}% vs B" if d_avg is not None else None)
            st.metric("Top Product", pa_top)

    with col_b:
        st.markdown(f"**Period B** — {b_s} → {b_e}")
        if sub_b.empty:
            st.warning("No data in this date range.")
        else:
            st.metric("Revenue",     f"{_cur()}{pb_rev:,.2f}")
            st.metric("Orders",      f"{pb_ord:,}")
            st.metric("Avg Ticket",  f"{_cur()}{pb_avg:.2f}")
            st.metric("Top Product", pb_top)


def _render_quick_price_check(df: pd.DataFrame) -> None:
    """Interactive price slider showing revenue impact for the top product."""
    st.markdown("---")
    st.subheader("What if you changed your top price?")
    st.caption("Drag the price on your top product — see the revenue impact instantly.")

    sim = df.groupby("product").agg(
        quantity=("quantity", "sum"),
        revenue=("revenue", "sum"),
    ).reset_index()
    sim["avg_price"]   = sim["revenue"] / sim["quantity"].clip(lower=1)
    has_d              = _has_dates(df)
    n_months           = max((df["date"].max() - df["date"].min()).days / 30, 1.0) if has_d else 1
    sim["monthly_qty"] = sim["quantity"] / n_months

    top         = sim.sort_values("revenue", ascending=False).iloc[0]
    cur_price   = float(top["avg_price"])
    monthly_qty = float(top["monthly_qty"])
    cur_rev     = cur_price * monthly_qty
    smin        = max(round(cur_price * 0.70, 2), 0.01)
    smax        = max(round(cur_price * 1.30, 2), smin + 0.01)
    step        = next(
        s for s in (0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 500.0)
        if (smax - smin) / 50 <= s
    )

    cur = _cur()
    st.caption(f"Showing: **{top['product']}** · current avg price {cur}{cur_price:.2f}/unit")
    new_price = st.slider(
        "Adjust price",
        min_value=smin,
        max_value=smax,
        value=min(max(cur_price, smin), smax),
        step=step,
        format="%.2f",
        key="overview_sim_slider",
    )

    pct        = (new_price - cur_price) / cur_price if cur_price > 0 else 0
    est_e, _, _, est_note = _estimate_product_elasticity(df, top["product"])
    elasticity = est_e if est_e is not None else _DEFAULT_ELASTICITY

    new_rev = new_price * max(monthly_qty * (1 - elasticity * pct), 0)
    delta   = new_rev - cur_rev
    n_tx    = int((df["product"] == top["product"]).sum())

    if abs(pct) > 0.01:
        msg = (
            f"At {cur}{new_price:.2f}, estimated monthly revenue from this product "
            f"changes by **{cur}{delta:+,.0f}** {((delta / cur_rev * 100) if cur_rev else 0):+.1f}%."
        )
        st.success(msg) if delta >= 0 else st.warning(msg)
    else:
        st.info(
            f"Estimated monthly revenue from **{top['product']}**: "
            f"**{cur}{cur_rev:,.0f}**. Move the slider to simulate a price change."
        )
    st.caption(_confidence_label(n_tx))
    st.caption("→ Open **Pricing** in the sidebar for the full analysis across all products.")


def render_overview(df: pd.DataFrame, product_clusters=None):
    st.header("How is the business performing?")
    st.caption("Revenue snapshot — the numbers that actually matter")

    n_txn = len(df)
    if n_txn < 20:
        st.warning(
            f"⚠️ **Only {n_txn} sales recorded** — most insights need more data to be reliable. "
            "Upload more sales history to unlock better recommendations."
        )
    elif not _has_dates(df):
        st.info(
            "ℹ️ No date column detected — time-based analyses (trends, anomalies, forecasts) are disabled. "
            "If your file has a date column, map it in the sidebar."
        )

    cur             = _cur()
    total_revenue   = df["revenue"].sum()
    total_orders    = len(df)
    avg_order       = total_revenue / total_orders if total_orders else 0
    unique_products = df["product"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue",   f"{cur}{total_revenue:,.2f}")
    c2.metric("Total Orders",    f"{total_orders:,}")
    c3.metric("Avg Order Value", f"{cur}{avg_order:.2f}")
    c4.metric("Unique Products", f"{unique_products}")

    if "location" in df.columns and df["location"].nunique() > 1:
        by_loc = df.groupby("location").agg(
            revenue=("revenue", "sum"),
            orders=("revenue", "count")
        ).sort_values("revenue", ascending=False)
        st.subheader("How does each location compare?")
        st.dataframe(by_loc.style.format({"revenue": f"{cur}{{:,.2f}}"}),
                     use_container_width=True)

    st.markdown("---")
    _render_ai_brief_expander(df, product_clusters, button_key="gen_brief_overview")
    _render_trend_anomaly_section(df)
    _render_period_comparison(df)
    _render_quick_price_check(df)


# =============================================================================
# 2. K-MEANS CLUSTERING — Best Sellers (Stars, Cash Cows, Hidden Gems, Low Activity)
# =============================================================================

def _label_clusters(centers_df: pd.DataFrame) -> dict:
    """Label clusters uniquely — no two clusters can share a name.

    Each label is assigned to whichever cluster scores best for it,
    with already-claimed clusters excluded from subsequent assignments.
    Guarantees: Stars=high both, Cash Cows=high revenue/low qty,
    Hidden Gems=high qty/low revenue, Low Activity=low both.
    """
    df = centers_df.copy()
    # Normalize 0-1 so quantity and revenue are on the same scale
    q_range = df["quantity"].max() - df["quantity"].min() + 1e-9
    r_range = df["revenue"].max() - df["revenue"].min() + 1e-9
    df["q_n"] = (df["quantity"] - df["quantity"].min()) / q_range
    df["r_n"] = (df["revenue"] - df["revenue"].min()) / r_range

    # Score each cluster for each label (higher = better fit)
    score_map = {
        "Stars":        df["q_n"] + df["r_n"],        # high both
        "Low Activity": -(df["q_n"] + df["r_n"]),     # low both
        "Cash Cows":    df["r_n"] - df["q_n"],        # high revenue, low qty
        "Hidden Gems":  df["q_n"] - df["r_n"],        # high qty, low revenue
    }

    labels = {}
    used = set()
    for label in ["Stars", "Low Activity", "Cash Cows", "Hidden Gems"]:
        scores = score_map[label]
        for idx in scores.sort_values(ascending=False).index:
            if idx not in used:
                labels[idx] = label
                used.add(idx)
                break
    return labels


def _render_cluster_cards(agg: pd.DataFrame) -> None:
    """Cluster category expanders + scatter for the Best Sellers page."""
    advice = {
        "Stars":        ("⭐", "Your Best Sellers",
                         "High sales, high revenue — protect these at all costs. Never let them run out of stock, and make sure they're the first thing customers see."),
        "Cash Cows":    ("💰", "Steady Earners",
                         "Ordered often but lower value — try bundling with a pricier item. 'Add X for just $2 more' works well here."),
        "Hidden Gems":  ("💎", "Underrated Items",
                         "Good margins but not enough people know about them — promote these. Try a daily special or have staff recommend them first."),
        "Low Activity": ("📉", "Slow Movers",
                         "Low sales and low revenue — review before cutting. Check how long each item has been available — something new may just need more time to catch on."),
    }
    cur = _cur()
    for cat in ["Stars", "Cash Cows", "Hidden Gems", "Low Activity"]:
        sub = agg[agg["category"] == cat].sort_values("revenue", ascending=False)
        if sub.empty:
            continue
        icon, label, tip = advice[cat]
        with st.expander(f"{icon} **{label}** · {len(sub)} product{'s' if len(sub) != 1 else ''}"):
            st.caption(tip)
            st.dataframe(
                sub[["product", "quantity", "revenue"]].style.format({"revenue": f"{cur}{{:,.2f}}"}),
                use_container_width=True, hide_index=True
            )

    with st.expander("See full chart", expanded=False):
        show_text = len(agg) <= 25
        _cat_colors = {
            "Stars": "#2563eb", "Cash Cows": "#16a34a",
            "Hidden Gems": "#9333ea", "Low Activity": "#94a3b8",
        }
        fig = px.scatter(
            agg, x="quantity", y="revenue", color="category",
            size="revenue",
            size_max=38,
            hover_name="product",
            hover_data={"quantity": ":.0f", "revenue": ":$,.2f", "avg_txn": ":$,.2f", "product": False},
            labels={"quantity": "Units Sold", "revenue": "Revenue", "avg_txn": "Avg Sale Value"},
            text="product" if show_text else None,
            color_discrete_map=_cat_colors,
        )
        if show_text:
            fig.update_traces(textposition="top center", textfont=dict(size=9, color="#475569"))
        fig.update_layout(
            height=500, showlegend=True,
            xaxis_title="Units Sold",
            yaxis_title=f"Revenue ({_cur()})",
        )
        fig.update_yaxes(tickprefix=_cur(), tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "ℹ️ **Categories are based on data in this file only.** A product with limited availability "
            "(e.g. only in your offer for 2–3 weeks) may appear in Low Activity simply because there wasn't "
            "enough time to build sales — not because customers dislike it."
        )


def _render_rising_stars_section(df: pd.DataFrame) -> None:
    """Rising Stars momentum widget for the Best Sellers page."""
    with st.expander("Filter rising products", expanded=_tpl_expanded("rising_stars")):
        rs_col1, rs_col2 = st.columns(2)
        rs_min_rev = rs_col1.number_input(
            "Min revenue in last 30 days",
            min_value=0.0, value=0.0, step=50.0,
            help="Only surface products that reached at least this much revenue in the recent period.",
            key="rs_min_rev",
        )
        rs_min_units = rs_col2.number_input(
            "Min units sold in last 30 days",
            min_value=0.0, value=0.0, step=1.0,
            help="Only surface products that sold at least this many units in the recent period.",
            key="rs_min_units",
        )
    rising = _find_rising_stars(df, min_revenue=rs_min_rev, min_units=rs_min_units)
    if rising is None:
        return
    st.markdown("---")
    st.subheader("Which products are gaining momentum?")
    st.caption("These items are selling more now than a month ago — act fast to keep the momentum going.")
    cols = st.columns(min(len(rising), 5))
    for i, (_, row) in enumerate(rising.iterrows()):
        with cols[i]:
            st.metric(
                label=str(row["product"])[:22] + ("…" if len(str(row["product"])) > 22 else ""),
                value=f"{_cur()}{row['recent_rev']:,.0f}",
                delta=f"+{row['growth_pct']:.0f}% revenue growth",
            )
    st.markdown("**💡 What to do with these rising products**")
    for _, row in rising.iterrows():
        prod  = row["product"]
        pct   = row["growth_pct"]
        rev   = row["recent_rev"]
        units = row.get("recent_units", 0)
        urgency = (
            "This is a breakthrough moment — act immediately before the trend cools." if pct >= 100 else
            "Strong momentum — capitalize before competitors notice."               if pct >= 50  else
            "Early signal — start promoting now to lock in the trend."
        )
        st.write(
            f"- **{prod}** is up **{pct:.0f}%** ({_cur()}{rev:,.0f} recent revenue, {int(units)} units). "
            f"Feature it as a daily special, ensure you never stock out, and put it in your most visible position. {urgency}"
        )


def _render_declining_products_section(df: pd.DataFrame) -> None:
    """Declining product alerts for the Best Sellers page."""
    if _has_dates(df) and _decline_history_insufficient(df):
        date_span = (df["date"].max() - df["date"].min()).days
        st.info(
            f"ℹ️ **Need more history for decline detection** — your data spans {date_span} day(s). "
            "Upload 60+ days of data to enable 30-vs-30 day comparison."
        )
    declining = _find_declining_products(df)
    if not declining:
        return
    st.markdown("---")
    st.subheader("Which items are slowing down?")
    st.caption(
        "These items are selling less now than they were 30 days ago. "
        "The note below each one tells you whether it's likely a seasonal dip or a real problem."
    )
    for item in declining:
        seasonality = item.get("seasonality", "uncertain")
        if seasonality == "possibly_seasonal":
            season_badge = (
                f"🌀 *May be seasonal* — your overall business is also down {abs(item['overall_pct']):.0f}%. "
                f"Monitor before making permanent changes."
            )
        elif seasonality == "structural":
            overall_dir = "up" if item["overall_pct"] > 0 else "flat"
            season_badge = (
                f"🔴 *Falling behind* — your overall business is {overall_dir} "
                f"({item['overall_pct']:+.0f}%), but this product is dropping. Act now."
            )
        else:
            season_badge = "⚪ *Too early to tell* — watch for another month before acting."
        st.warning(
            f"**{item['product']}** — revenue dropped **{item['decline_pct']:.0f}%** "
            f"({_cur()}{item['older_rev']:,.0f} → {_cur()}{item['recent_rev']:,.0f})  "
            f"→ *Feature as a daily special, bundle with a Star product, or evaluate for removal.*\n\n"
            f"{season_badge}"
        )


def _render_cluster_action_plan(agg: pd.DataFrame) -> None:
    """Per-cluster concrete action steps expander for the Best Sellers page."""
    st.markdown("---")
    cur_sym          = _cur()
    icon_map         = {"Stars": "⭐", "Cash Cows": "💰", "Hidden Gems": "💎", "Low Activity": "📉"}
    display_name_map = {"Stars": "Your Best Sellers", "Cash Cows": "Steady Earners",
                        "Hidden Gems": "Underrated Items", "Low Activity": "Slow Movers"}

    total_rev = agg["revenue"].sum()

    with st.expander("What should you do with each group?", expanded=_tpl_expanded("best_sellers")):
        st.caption("Concrete next steps for each product group — based on your actual numbers.")
        for cat in ["Stars", "Cash Cows", "Hidden Gems", "Low Activity"]:
            sub = agg[agg["category"] == cat]
            if sub.empty:
                continue
            top3          = sub.nlargest(3, "revenue")
            top_name      = str(top3.iloc[0]["product"])
            top_rev       = top3.iloc[0]["revenue"]
            top_qty       = int(top3.iloc[0]["quantity"])
            top_avg_txn   = top3.iloc[0]["avg_txn"]
            top_share_pct = (top_rev / total_rev * 100) if total_rev > 0 else 0
            products_list = ", ".join(str(x) for x in top3["product"].tolist())
            second_name   = str(top3.iloc[1]["product"]) if len(top3) > 1 else top_name
            cat_rev       = sub["revenue"].sum()
            cat_share_pct = (cat_rev / total_rev * 100) if total_rev > 0 else 0

            if cat == "Stars":
                steps = [
                    f"Launch a loyalty program for **{top_name}** — your #1 seller at {cur_sym}{top_rev:,.0f} ({top_share_pct:.0f}% of total revenue). Reward repeat buyers — after 5 purchases, give one free. At {cur_sym}{top_avg_txn:,.0f} avg per sale that's a 20% cost — worth it for a guaranteed repeat buyer.",
                    f"Never let **{top_name}** or **{second_name}** run out of stock. Your Stars drive {cat_share_pct:.0f}% of total revenue — a stockout is a direct hit to your biggest earner. Set a reorder alert at 20% remaining inventory.",
                    f"Give **{top_name}** the most visible position — eye-level shelf, top of your list, or first on the board. Eye-level placement lifts sales 15–20% with zero extra cost — and {cur_sym}{top_rev:,.0f} in revenue means even a 10% lift is {cur_sym}{top_rev * 0.10:,.0f} back in your pocket.",
                ]
            elif cat == "Cash Cows":
                gems_sub = agg[agg["category"] == "Hidden Gems"]
                gem_name = str(gems_sub.nlargest(1, "quantity").iloc[0]["product"]) if not gems_sub.empty else "a Hidden Gem"
                gem_avg_txn = gems_sub.nlargest(1, "quantity").iloc[0]["avg_txn"] if not gems_sub.empty else 2.0
                bundle_addon = max(1, round(gem_avg_txn * 0.6))
                steps = [
                    f"Bundle **{top_name}** with **{gem_name}** — offer {gem_name} for {cur_sym}{bundle_addon} extra at checkout. Cash Cows have the order volume to make cross-sells automatic, and {gem_name} gets the visibility it needs. Run this for 2 weeks and measure.",
                    f"Script your staff to recommend **{top_name}** and **{second_name}** by name — 'Would you like to add {second_name}?' converts 30–40% better than a generic upsell. Your Cash Cows are generating {cur_sym}{cat_rev:,.0f}; a 5% upsell rate is real money.",
                    f"**{top_name}** earns {cur_sym}{top_avg_txn:,.0f} per sale on average — don't discount it. Bundle it with lower-margin items instead to lift your average order value without cutting into your strongest margin.",
                ]
            elif cat == "Hidden Gems":
                stars_sub = agg[agg["category"] == "Stars"]
                stars_avg_txn = stars_sub["avg_txn"].mean() if not stars_sub.empty else top_avg_txn
                value_ratio = top_avg_txn / stars_avg_txn if stars_avg_txn > 0 else 1.0
                value_note = (
                    f"{value_ratio:.1f}× the avg price of your Stars" if value_ratio > 1.1
                    else f"{value_ratio:.1f}× the avg Stars price" if value_ratio < 0.9
                    else "similar price to your Stars"
                )
                steps = [
                    f"Feature **{top_name}** as 'Staff Pick' this week — it earns {cur_sym}{top_avg_txn:,.0f} per sale ({value_note}) but has only moved {top_qty} units. Strong unit economics, low visibility. A spotlight costs you nothing.",
                    f"Highlight **{top_name}** in your top sales position — add a short description explaining what makes it the best choice. Customers buy with more confidence when they understand what they're getting.",
                    f"**{top_name}** has generated {cur_sym}{top_rev:,.0f} while staying under the radar. Give it a 2-week featured placement before making any decisions — don't cut a product that just lacks visibility.",
                ]
            else:  # Low Activity
                low_share_pct = (top_rev / total_rev * 100) if total_rev > 0 else 0
                steps = [
                    f"⚠️ **{top_name}** moved {top_qty} units and generated {cur_sym}{top_rev:,.0f} ({low_share_pct:.1f}% of total revenue). Before cutting it, check how long it has been listed — products under 30 days often just need time to find their audience.",
                    f"Give **{top_name}** a 2-week visibility test — daily special, staff mention, or front-of-shelf placement — before removing it. Removal has real costs: wasted inventory and a narrower offer. Test first, then decide.",
                    f"If the 2-week test shows any lift on **{top_name}**, keep it and iterate. If {cur_sym}{top_rev:,.0f} stays flat despite the push, that's your signal to drop it from your active offer and redirect that effort toward a stronger product.",
                ]
            with st.expander(f"{icon_map[cat]} **{display_name_map[cat]}** — Action Steps · applies to: *{products_list}*{' + more' if len(sub) > 3 else ''}"):
                for j, step in enumerate(steps, 1):
                    st.write(f"{j}. {step}")


# =============================================================================
# INSIGHT CHANGELOG — track cluster movements across uploads
# =============================================================================

def _record_cluster_snapshot(
    df: pd.DataFrame,
    product_clusters,
    upload_hash: str,
) -> None:
    """Save current cluster assignments to history. Deduplicates by upload_hash."""
    if product_clusters is None:
        return
    history = st.session_state.cluster_history

    if any(e["upload_hash"] == upload_hash for e in history):
        return

    assignments = dict(zip(
        product_clusters["product"].astype(str),
        product_clusters["category"].astype(str),
    ))

    if _has_dates(df):
        date_max = df["date"].max()
        label = date_max.strftime("%b %Y")
    else:
        label = f"Upload {len(history) + 1}"

    history.append({
        "upload_hash": upload_hash,
        "timestamp":   pd.Timestamp.now().isoformat(),
        "assignments": assignments,
        "label":       label,
    })

    if len(history) > 10:
        st.session_state.cluster_history = history[-10:]


def _compute_cluster_changelog(history: list) -> list:
    """Compare the two most recent cluster snapshots. Return list of movements."""
    if len(history) < 2:
        return []

    prev = history[-2]["assignments"]
    curr = history[-1]["assignments"]
    prev_label = history[-2]["label"]
    curr_label = history[-1]["label"]

    movements = []
    for product, curr_cat in curr.items():
        prev_cat = prev.get(product)
        if prev_cat is None:
            continue
        if prev_cat != curr_cat:
            movements.append({
                "product":    product,
                "from_cat":   prev_cat,
                "to_cat":     curr_cat,
                "prev_label": prev_label,
                "curr_label": curr_label,
            })

    return movements


def _render_insight_changelog(movements: list) -> None:
    """Render a compact notice of cluster movements between the two most recent uploads."""
    if not movements:
        return

    _cat_icon = {
        "Stars":        "⭐",
        "Cash Cows":    "💰",
        "Hidden Gems":  "💎",
        "Low Activity": "📉",
    }

    n = len(movements)
    prev_label = movements[0]["prev_label"]
    curr_label = movements[0]["curr_label"]

    with st.expander(
        f"📊 {n} product{'s' if n != 1 else ''} changed category since {prev_label}",
        expanded=True
    ):
        st.caption(
            f"Comparing {prev_label} → {curr_label}. "
            "Category shifts are the clearest signal of momentum change."
        )
        for m in movements:
            from_icon = _cat_icon.get(m["from_cat"], "•")
            to_icon   = _cat_icon.get(m["to_cat"],   "•")

            is_positive = m["to_cat"] in ("Stars", "Hidden Gems")
            is_negative = m["to_cat"] == "Low Activity"

            line = (
                f"**{m['product']}** moved "
                f"{from_icon} {m['from_cat']} → {to_icon} {m['to_cat']}"
            )

            if is_positive:
                st.success(line)
            elif is_negative:
                st.warning(line)
            else:
                st.info(line)


def render_best_sellers(df: pd.DataFrame, product_clusters=None):
    st.header("What's Selling?")
    st.caption("Your products sorted by what's working and what needs attention")

    cluster_ok = _recommendation_safety_check(df)["clustering"][0]
    if not cluster_ok:
        st.info("ℹ️ We need a bit more data before we can group your products into categories. Showing a simple revenue list for now.")

    agg = product_clusters
    if agg is None:
        basic = df.groupby("product").agg(
            quantity=("quantity", "sum"),
            revenue=("revenue", "sum")
        ).reset_index()
        st.warning("Need at least 4 products to group them into categories.")
        st.dataframe(basic.style.format({"revenue": f"{_cur()}{{:,.2f}}"}), use_container_width=True)
        return None

    _render_cluster_cards(agg)
    _record_cluster_snapshot(df, agg, st.session_state.get("_last_file_hash", "demo"))
    movements = _compute_cluster_changelog(st.session_state.cluster_history)
    _render_insight_changelog(movements)
    _render_rising_stars_section(df)
    _render_declining_products_section(df)
    _render_cluster_action_plan(agg)
    return agg




# =============================================================================
# PRICE ELASTICITY ESTIMATION — log-log OLS from transaction-level price variance
# =============================================================================

def _estimate_product_elasticity(df: pd.DataFrame, product: str) -> tuple:
    """Estimate price elasticity using daily-aggregated price/volume data.

    Aggregates to the daily level before fitting log-log OLS. Transaction-level
    estimation is unreliable in POS data because within-day price variance is
    almost entirely noise (rounding, modifiers, discounts) rather than real
    demand response. Daily aggregation isolates actual pricing decisions.

    Returns: (elasticity, low_95, high_95, note)
      - elasticity: |slope| — demand change per 1% price change
      - low_95 / high_95: directional uncertainty range (not a formal CI)
      - note: description for display
    Returns (None, None, None, reason) if data is insufficient or ambiguous.
    """
    prod_df = df[(df["product"] == product) & (df["quantity"] > 0)].copy()
    prod_df["unit_price"] = prod_df["revenue"] / prod_df["quantity"]

    n_raw = len(prod_df)
    if n_raw < 10:
        return None, None, None, f"insufficient data ({n_raw} transactions — need 10+)"

    # ── Step 1: Aggregate to daily level ──────────────────────────────────
    # Removes within-day noise; preserves real day-to-day pricing variation.
    if _has_dates(prod_df):
        prod_df["date_only"] = prod_df["date"].dt.date
        daily_agg = (
            prod_df.groupby("date_only")
            .agg(avg_price=("unit_price", "mean"), total_qty=("quantity", "sum"))
            .reset_index()
        )
        n_days = len(daily_agg)
        if n_days < 5:
            return None, None, None, f"insufficient daily observations ({n_days} days — need 5+)"
        price_series = daily_agg["avg_price"]
        qty_series   = daily_agg["total_qty"]
    else:
        # No dates — fall back to transaction-level with stricter CV threshold
        price_series = prod_df["unit_price"]
        qty_series   = prod_df["quantity"]
        n_days = n_raw

    # ── Step 2: Price variation guard ─────────────────────────────────────
    # Minimum 3% CV required — below this, any estimated elasticity is noise.
    price_mean = float(price_series.mean())
    price_cv   = float(price_series.std()) / (price_mean + 1e-9)
    if price_cv < 0.03:
        return None, None, None, (
            f"not enough price variation in the data to estimate reliably — "
            f"prices appear fixed. Run a controlled price experiment to get real demand data."
        )

    # ── Step 3: Bin into price quantiles ──────────────────────────────────
    try:
        # Allow up to 10 bins (was 6) so products with 30+ days can reach dof ≥ 5.
        n_bins = min(10, n_days // 3)
        if n_bins < 3:
            return None, None, None, f"too few daily observations for binning ({n_days} days)"
        agg_df = pd.DataFrame({"price": price_series.values, "qty": qty_series.values})
        agg_df["price_bin"] = pd.qcut(agg_df["price"], q=n_bins, duplicates="drop")
        binned = (
            agg_df.groupby("price_bin", observed=True)
            .agg(avg_price=("price", "mean"), avg_qty=("qty", "mean"), n=("qty", "count"))
            .reset_index()
        )
        binned = binned[binned["n"] >= 2]
    except Exception as e:
        return None, None, None, f"price binning failed: {e}"

    # Require at least 5 retained bins (dof ≥ 3) to produce a meaningful regression.
    # With only 3–4 bins (dof 1–2) the OLS fit is nearly deterministic; even random
    # data can pass the t-stat gate at those degrees of freedom.
    if len(binned) < 5:
        return None, None, None, (
            f"insufficient price bins after filtering ({len(binned)} retained — need 5+). "
            f"More price variation or a longer history is required."
        )

    log_p = np.log(binned["avg_price"].clip(lower=0.01).values)
    log_q = np.log(binned["avg_qty"].clip(lower=0.01).values)
    n_pts = len(log_p)

    # ── Step 4: Log-log OLS ───────────────────────────────────────────────
    X = np.column_stack([np.ones(n_pts), log_p])
    try:
        coeffs, _, _, _ = np.linalg.lstsq(X, log_q, rcond=None)
    except Exception as e:
        return None, None, None, f"regression failed: {e}"

    b = coeffs[1]
    fitted = X @ coeffs
    resid  = log_q - fitted
    dof    = n_pts - 2
    # Require dof ≥ 3 (5+ bins retained). Below this, OLS has near-perfect fit by
    # construction; a high t-stat is meaningless rather than informative.
    if dof < 3:
        return None, None, None, (
            f"not enough data points to estimate reliably — "
            f"Collect more pricing variation before estimating elasticity."
        )

    s2 = (resid ** 2).sum() / dof
    try:
        Xp_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError as e:
        return None, None, None, f"singular matrix: {e}"
    se_b = float(np.sqrt(max(s2 * Xp_inv[1, 1], 1e-9)))

    ss_tot = ((log_q - log_q.mean()) ** 2).sum()
    r2_raw = 1 - (resid ** 2).sum() / (ss_tot + 1e-9)
    r2     = float(np.clip(r2_raw, 0, 1)) if np.isfinite(r2_raw) else 0.0
    t_stat = abs(b) / se_b if se_b > 0 else 0

    # ── Step 5: Quality gate ──────────────────────────────────────────────
    # Use a dof-adjusted t-critical (≈ two-sided α=0.10) rather than a fixed 1.8.
    # Approximation t_crit ≈ 1.645 + 2.0/dof fits the Student-t table to <0.05 error
    # for dof ∈ [3, ∞]: dof=3 → 2.31 (true 2.35), dof=5 → 2.05 (true 2.02),
    # dof=10 → 1.85 (true 1.81), dof→∞ → 1.65.
    t_crit = max(1.8, 1.645 + 2.0 / dof)
    if t_stat < t_crit or r2 < 0.20:
        return None, None, None, (
            f"the relationship between price and sales volume is too weak to estimate reliably — "
            f"price variation may be confounded by promotions or seasonality. "
            f"A controlled price experiment would provide cleaner identification."
        )

    raw_elasticity = float(abs(b))
    _ELASTICITY_CAP = 2.5  # empirical ceiling for consumer goods
    _CI_CAP = 3.5
    elasticity = float(np.clip(raw_elasticity, 0.05, _ELASTICITY_CAP))
    low_95  = float(np.clip(abs(b) - 2 * se_b, 0.05, _CI_CAP))
    high_95 = float(np.clip(abs(b) + 2 * se_b, 0.05, _CI_CAP))

    fit_quality = "strong" if r2 > 0.5 and t_stat > 3 else ("moderate" if r2 > 0.25 else "weak")
    cap_note = ""
    if raw_elasticity > _ELASTICITY_CAP:
        cap_note = f" Raw estimate ({raw_elasticity:.2f}) capped at {_ELASTICITY_CAP} — treat as directional only."
        fit_quality = "moderate"  # downgrade if capped
    note = (
        f"data-estimated from {n_raw} transactions / {n_days} daily observations, "
        f"Based on {n_pts} price points — {fit_quality} confidence{cap_note}"
    )
    return elasticity, low_95, high_95, note


# =============================================================================
# 4. PRICE ELASTICITY — Price Intelligence
# =============================================================================

def render_price_intelligence(df: pd.DataFrame, product_clusters=None):
    st.header("Are you pricing your items right?")
    st.caption("See which items might be priced too low or too high — and what to do about it.")

    safety = _recommendation_safety_check(df)
    pricing_safe, pricing_reason = safety["pricing"]
    if not pricing_safe:
        st.info(f"Not enough data for pricing recommendations yet — {pricing_reason}.")
        return

    agg = df.groupby("product").agg(
        quantity=("quantity", "sum"),
        revenue=("revenue", "sum"),
        orders=("revenue", "count")
    ).reset_index()
    agg = agg[agg["quantity"] > 0]
    if agg.empty:
        st.warning("No quantity data for price analysis.")
        return
    agg["avg_price"] = agg["revenue"] / agg["quantity"]
    
    # Price buckets — use fewer bins if not enough unique prices
    _n_price_bins = min(5, agg["avg_price"].nunique())
    _bucket_labels = ["Low", "Mid-Low", "Mid", "Mid-High", "High"][:_n_price_bins]
    if _n_price_bins < 2:
        agg["price_bucket"] = "All"
    else:
        bucketed = None
        try:
            bucketed = pd.qcut(agg["avg_price"], q=_n_price_bins, duplicates="drop")
        except ValueError:
            try:
                bucketed = pd.cut(agg["avg_price"], bins=_n_price_bins)
            except ValueError:
                agg["price_bucket"] = "All"
                bucketed = None
        if bucketed is not None:
            actual_bins = bucketed.cat.categories.size
            agg["price_bucket"] = pd.Categorical(
                bucketed.cat.rename_categories(
                    dict(zip(bucketed.cat.categories, _bucket_labels[:actual_bins]))
                ),
                categories=_bucket_labels[:actual_bins],
                ordered=True,
            )
    by_bucket = agg.groupby("price_bucket", observed=True).agg(
        total_revenue=("revenue", "sum"),
        total_qty=("quantity", "sum"),
        products=("product", "count")
    ).reset_index()
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Revenue by Price Range", "Units Sold by Price Range"),
        horizontal_spacing=0.12,
    )
    fig.add_trace(
        go.Bar(
            x=by_bucket["price_bucket"], y=by_bucket["total_revenue"],
            name="Revenue",
            marker=dict(color="#2563eb", cornerradius=6),
            hovertemplate="%{x}<br>Revenue: " + _cur() + "%{y:,.0f}<extra></extra>",
            text=by_bucket["total_revenue"].apply(lambda v: f"{_cur()}{v:,.0f}"),
            textposition="outside", textfont=dict(size=10, color="#475569"),
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(
            x=by_bucket["price_bucket"], y=by_bucket["total_qty"],
            name="Units",
            marker=dict(color="#93c5fd", cornerradius=6),
            hovertemplate="%{x}<br>Units: %{y:,.0f}<extra></extra>",
            text=by_bucket["total_qty"].apply(lambda v: f"{v:,.0f}"),
            textposition="outside", textfont=dict(size=10, color="#475569"),
        ),
        row=1, col=2,
    )
    fig.update_layout(
        height=380, showlegend=False,
        margin=dict(l=48, r=16, t=56, b=48),
    )
    fig.update_yaxes(tickprefix=_cur(), tickformat=",.0f", row=1, col=1)
    fig.update_yaxes(tickformat=",.0f", row=1, col=2)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("What are you charging per item?")
    cur = _cur()
    st.dataframe(
        agg.sort_values("revenue", ascending=False)[["product", "avg_price", "quantity", "revenue"]]
        .style.format({"avg_price": f"{cur}{{:.2f}}", "revenue": f"{cur}{{:,.2f}}"}),
        use_container_width=True, hide_index=True
    )

    # ── Per-product Pricing Recommendations ──────────────────────────────
    price_recs = _get_price_recommendations(df)
    if price_recs:
        st.markdown("---")
        st.subheader("💰 What You Should Change")
        st.caption(
            "Suggestions based on how your prices compare to how well each item sells. "
            "Test any change for 2 weeks before making it permanent."
        )
        # Cross-category confound warning: when the portfolio spans a wide price range
        # (CV > 1.0), percentile-based thresholds compare e.g. a $2 coffee against a
        # $50 service. A cheap, high-volume item may be flagged as "low price" simply
        # because its absolute price is low relative to unrelated expensive products.
        _price_agg = df.groupby("product")["revenue"].sum() / df.groupby("product")["quantity"].sum().clip(lower=1)
        _price_mean = _price_agg.mean()
        _price_cv = float(_price_agg.std() / _price_mean) if pd.notna(_price_mean) and _price_mean > 0 else 0
        if _price_cv > 1.0:
            st.warning(
                "⚠️ **Your products have a wide range of prices.** "
                "The suggestions below compare all items against each other — a cheap, high-volume item "
                "may show up as 'under-priced' just because an expensive item is pulling the average up. "
                "Use these as a starting point, and apply your own judgment about items in the same category."
            )

        action_colors = {"↑ Raise Price": "🟢", "↓ Consider Lowering": "🟡", "✓ Maintain": "🔵"}
        for rec in price_recs:
            action_icon = action_colors.get(rec["action"], "⚪")
            with st.expander(f"{action_icon} **{rec['product']}** — {rec['action']}  ·  Current: {_cur()}{rec['current']:.2f}  →  Suggested: {_cur()}{rec['suggested']:.2f}"):
                st.write(rec["reason"])
                if rec["action"] == "↑ Raise Price":
                    st.info(
                        "**How to test:** Raise the price on this item only. Monitor unit sales for 14 days. "
                        "If volume drops by less than the % price increase, you've improved your margin. If volume holds — you underpriced it."
                    )
                elif rec["action"] == "↓ Consider Lowering":
                    st.warning(
                        "**How to test:** Run a 10% promotion for 2 weeks and track volume lift. "
                        "If new revenue (lower price × more units) beats current revenue, make it permanent."
                    )
                else:
                    st.success(
                        "**Protect this price point:** Avoid discounting this item. Instead, bundle it with a lower-margin item to lift your overall average order value."
                    )

        # Pricing strategy summary
        raise_count = sum(1 for r in price_recs if r["action"] == "↑ Raise Price")
        lower_count = sum(1 for r in price_recs if r["action"] == "↓ Consider Lowering")
        if raise_count > 0 or lower_count > 0:
            st.markdown("**📊 Pricing Summary**")
            cols_p = st.columns(3)
            cols_p[0].metric("Items to Raise", raise_count, help="High-demand, underpriced items")
            cols_p[1].metric("Items to Test Lower", lower_count, help="High-priced, low-volume items")
            cols_p[2].metric("Items to Protect", len(price_recs) - raise_count - lower_count, help="Strong margin performers")

    # ── Price Simulator ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔮 What If You Changed the Price?")
    st.caption("Move the slider to see how a price change might affect your monthly revenue — before you commit to it.")

    # Product aggregates
    sim_agg = df.groupby("product").agg(
        quantity=("quantity", "sum"),
        revenue=("revenue", "sum"),
    ).reset_index()
    sim_agg["avg_price"] = sim_agg["revenue"] / sim_agg["quantity"].clip(lower=1)

    # Monthly quantity estimate
    has_dates = _has_dates(df)
    n_months = max((df["date"].max() - df["date"].min()).days / 30, 1.0) if has_dates else 1
    sim_agg["monthly_qty"] = sim_agg["quantity"] / n_months

    sim_products = sim_agg.sort_values("revenue", ascending=False)["product"].tolist()
    selected_sim = st.selectbox("Select a product to simulate", sim_products, key="sim_product")

    sim_row = sim_agg[sim_agg["product"] == selected_sim].iloc[0]
    cur_price = float(sim_row["avg_price"])
    monthly_qty = float(sim_row["monthly_qty"])
    cur_monthly_rev = cur_price * monthly_qty

    # ── Elasticity: try data-driven first, fall back to category heuristic ──
    cat_map = (
        product_clusters.set_index("product")["category"].to_dict()
        if product_clusters is not None else {}
    )
    cat = cat_map.get(selected_sim, "")

    est_e, est_low, est_high, est_note = _estimate_product_elasticity(df, selected_sim)
    # Only trust OLS when fit clears both R²>0.5 AND t>3. Weak/moderate fits are
    # indistinguishable from observational noise and should not show a specific number.
    ols_strong = est_e is not None and "strong" in (est_note or "")

    if ols_strong:
        elasticity = est_e
        elas_low = est_low
        elas_high = est_high
        elas_source = f"data-estimated ({est_note})"
        sim_conf = "high"
    else:
        # OLS either failed outright or returned a weak/moderate fit — fall back to
        # category heuristics rather than showing a noisy point estimate as fact.
        if cat in ("Stars", "Cash Cows"):
            elasticity, elas_low, elas_high = 0.4, 0.25, 0.60
            elas_source = f"category heuristic — {cat} buyers tend to be loyal (less price-sensitive)."
        elif cat in ("Hidden Gems", "Low Activity"):
            elasticity, elas_low, elas_high = 0.8, 0.55, 1.10
            elas_source = f"category heuristic — {cat} segment tends to be more price-sensitive."
        else:
            elasticity, elas_low, elas_high = _DEFAULT_ELASTICITY, 0.45, 0.90
            elas_source = "moderate heuristic (cluster unknown)."
        sim_conf = "directional"

    slider_min = max(round(cur_price * 0.70, 2), 0.01)
    slider_max = max(round(cur_price * 1.30, 2), slider_min + 0.01)
    # Dynamic step: ~50 discrete positions across the range, snapped to a nice number
    _price_step = next(
        s for s in (0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 500.0)
        if (slider_max - slider_min) / 50 <= s
    )
    new_price = st.slider(
        "New price",
        min_value=slider_min,
        max_value=slider_max,
        value=min(max(cur_price, slider_min), slider_max),
        step=_price_step,
        format="%.2f",
        key="sim_price_slider",
    )

    price_change_pct = (new_price - cur_price) / cur_price if cur_price > 0 else 0

    # Three scenarios: pessimistic (high elasticity), expected, optimistic (low elasticity)
    def _sim_rev(e):
        qty = monthly_qty * (1 - e * price_change_pct)
        return new_price * max(qty, 0)

    rev_expected = _sim_rev(elasticity)
    rev_pessimistic = _sim_rev(elas_high)   # high elasticity → more demand loss
    rev_optimistic = _sim_rev(elas_low)     # low elasticity → less demand loss

    # Ensure order: pessimistic ≤ expected ≤ optimistic
    rev_low = min(rev_pessimistic, rev_optimistic)
    rev_high = max(rev_pessimistic, rev_optimistic)
    delta_expected = rev_expected - cur_monthly_rev
    delta_low = rev_low - cur_monthly_rev
    delta_high = rev_high - cur_monthly_rev

    cur_sym = _cur()

    if not ols_strong:
        st.info(
            "**Early signal — not enough pricing variation in your data to be precise.** "
            "This estimate is based on how similar products typically respond to price changes. "
            "Test any price change for at least 2 weeks before committing."
        )

    s1, s2, s3 = st.columns(3)
    s1.metric("Current monthly rev", f"{cur_sym}{cur_monthly_rev:,.2f}")
    s2.metric("Expected monthly rev", f"{cur_sym}{rev_expected:,.2f}", f"{delta_expected:+,.2f}")
    s3.metric("Price change", f"{price_change_pct * 100:+.1f}%")

    if abs(price_change_pct) > 0.01:
        pct_delta = delta_expected / cur_monthly_rev * 100 if cur_monthly_rev > 0 else 0
        direction = "increases" if delta_expected >= 0 else "decreases"
        _tier_lbl, _tier_emoji = _confidence_tier(sim_conf)
        _summary = (
            f"At {cur_sym}{new_price:.2f}, revenue likely **{direction}** "
            f"({pct_delta:+.1f}%). {_tier_emoji} **{_tier_lbl}**"
        )
        if delta_expected >= 0:
            st.success(_summary)
        else:
            st.warning(_summary)

        with st.expander("See the numbers behind this estimate"):
            range_str = f"{cur_sym}{rev_low:,.0f}–{cur_sym}{rev_high:,.0f}/mo"
            st.caption(
                f"Likely range: **{range_str}** — treat as a rough guide, not a guarantee. "
                f"Test any price change for 2 weeks before committing."
            )
            scenario_df = pd.DataFrame({
                "Scenario": ["If customers are price-sensitive", "Expected", "If customers are loyal"],
                f"Monthly rev ({cur_sym})": [f"{cur_sym}{rev_low:,.0f}", f"{cur_sym}{rev_expected:,.0f}", f"{cur_sym}{rev_high:,.0f}"],
                f"Change ({cur_sym})": [f"{delta_low:+,.0f}", f"{delta_expected:+,.0f}", f"{delta_high:+,.0f}"],
            })
            st.dataframe(scenario_df, use_container_width=True, hide_index=True)

    sim_n_tx = int((df["product"] == selected_sim).sum())
    st.caption(_confidence_label(sim_n_tx))


# =============================================================================
# 5. GROWTH FORECAST — Time Series Forecasting
# =============================================================================

def render_growth_forecast(df: pd.DataFrame):
    st.header("Where is the business headed?")
    st.caption("Based on your sales history, here's where your revenue is likely going.")

    if not _has_dates(df):
        st.warning("No date/timestamp column found. Upload data with dates to see the growth forecast.")
        return

    df = df.copy()
    df["date_only"] = df["date"].dt.date

    daily = df.groupby("date_only")["revenue"].sum().sort_index().reset_index()
    daily["date_only"] = pd.to_datetime(daily["date_only"])
    # Fill gaps so the time series is continuous (missing days = 0 revenue)
    full_idx = pd.date_range(daily["date_only"].min(), daily["date_only"].max(), freq="D")
    daily = (daily.set_index("date_only")
                  .reindex(full_idx, fill_value=0.0)
                  .rename_axis("date_only")
                  .reset_index())
    daily["days_since_start"] = (daily["date_only"] - daily["date_only"].min()).dt.days

    if len(daily) < 7:
        st.warning("Need at least 7 days of data for a meaningful forecast.")
        return

    forecast_weeks = st.slider("Forecast horizon (weeks)", 1, 8, 4)
    forecast_days = forecast_weeks * 7

    daily["rolling_7"] = daily["revenue"].rolling(7, min_periods=1).mean()
    last_date = daily["date_only"].max()
    avg_daily = daily["revenue"].mean()

    slope = 0  # will be set by whichever path runs

    # ── statsforecast path (primary: fastest + most accurate) ─────────────────
    use_statsforecast = False
    if _STATSFORECAST_AVAILABLE and len(daily) >= 10:
        try:
            sf_df = daily[["date_only", "revenue"]].rename(
                columns={"date_only": "ds", "revenue": "y"}
            ).copy()
            sf_df.insert(0, "unique_id", "total")
            with st.spinner("Analyzing your sales trends…"):
                sf = _StatsForecast(models=[_AutoARIMA(), _AutoETS()], freq="D", n_jobs=1)
                sf.fit(sf_df)
                fcast = sf.predict(h=forecast_days, level=[80])
            future_dates = pd.DatetimeIndex(fcast["ds"])
            mid_cols = [c for c in fcast.columns if c not in ("unique_id", "ds") and "-lo-" not in c and "-hi-" not in c]
            lo_cols  = [c for c in fcast.columns if "-lo-80" in c]
            hi_cols  = [c for c in fcast.columns if "-hi-80" in c]
            fcst_mid   = np.maximum(fcast[mid_cols].mean(axis=1).values, 0)
            fcst_lower = np.maximum(fcast[lo_cols].min(axis=1).values, 0) if lo_cols else fcst_mid * 0.85
            fcst_upper = np.maximum(fcast[hi_cols].max(axis=1).values, 0) if hi_cols else fcst_mid * 1.15
            # If the model returned all-zero forecasts while historical revenue is positive,
            # it converged to a degenerate solution — fall through to Prophet/linear instead.
            if fcst_mid.sum() == 0 and daily["revenue"].sum() > 0:
                use_statsforecast = False
            else:
                # Widen confidence intervals for short datasets — models underestimate
                # uncertainty when they haven't seen enough historical variance
                _n_history_days = len(daily)
                if _n_history_days < 60:
                    _ci_multiplier = max(1.0, 60 / _n_history_days)  # e.g., 30 days → 2x wider
                    _ci_center = fcst_mid
                    fcst_lower = np.maximum(_ci_center - (_ci_center - fcst_lower) * _ci_multiplier, 0)
                    fcst_upper = _ci_center + (fcst_upper - _ci_center) * _ci_multiplier
                slope = float((fcst_mid[-1] - fcst_mid[0]) / max(len(fcst_mid) - 1, 1)) if len(fcst_mid) >= 2 else 0.0
                method_note = "Revenue forecast"  # internal — not shown to user
                use_statsforecast = True
        except Exception as _sf_err:
            pass  # fall back silently to Prophet/linear
            use_statsforecast = False

    # ── Prophet path ──────────────────────────────────────────────────────────
    use_prophet = not use_statsforecast and _PROPHET_AVAILABLE and len(daily) >= 14

    if use_prophet:
        import logging
        logging.getLogger("prophet").setLevel(logging.WARNING)
        logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

        prophet_df = daily[["date_only", "revenue"]].rename(
            columns={"date_only": "ds", "revenue": "y"}
        ).copy()
        date_span = (last_date - daily["date_only"].min()).days

        # Winsorize outliers (clip bottom/top 1%) so bad days don't distort the trend
        q01 = prophet_df["y"].quantile(0.01)
        q99 = prophet_df["y"].quantile(0.99)
        prophet_df["y"] = prophet_df["y"].clip(lower=q01, upper=q99)

        try:
            m = _Prophet(
                weekly_seasonality=True,
                yearly_seasonality=date_span >= 365,   # enable after 1 year (was 2)
                daily_seasonality=False,
                interval_width=0.8,
                uncertainty_samples=500,               # was 200 — smoother bands
                changepoint_prior_scale=0.15 if date_span < 30 else (0.20 if date_span < 60 else 0.25),
                seasonality_prior_scale=10,
            )
            # Monthly seasonality captures payday & month-end spending cycles
            m.add_seasonality(name="monthly", period=30.5, fourier_order=5)
            # Public holidays — respects the user's selected region
            _holiday_country = st.session_state.get("country_code", "US")
            if _holiday_country:
                m.add_country_holidays(country_name=_holiday_country)
            with st.spinner("Analyzing your sales trends…"):
                m.fit(prophet_df)

            future = m.make_future_dataframe(periods=forecast_days)
            forecast = m.predict(future)

            future_fc = forecast[forecast["ds"] > last_date].copy()
            future_dates = pd.DatetimeIndex(future_fc["ds"])
            fcst_mid    = np.maximum(future_fc["yhat"].values, 0)
            fcst_upper  = np.maximum(future_fc["yhat_upper"].values, 0)
            fcst_lower  = np.maximum(future_fc["yhat_lower"].values, 0)

            # Widen confidence intervals for short datasets — models underestimate
            # uncertainty when they haven't seen enough historical variance
            _n_history_days = len(daily)
            if _n_history_days < 60:
                _ci_multiplier = max(1.0, 60 / _n_history_days)
                _ci_center = fcst_mid
                fcst_lower = np.maximum(_ci_center - (_ci_center - fcst_lower) * _ci_multiplier, 0)
                fcst_upper = _ci_center + (fcst_upper - _ci_center) * _ci_multiplier

            # Derive slope from Prophet's trend component for the metrics card
            hist_fc = forecast[forecast["ds"] <= last_date]
            if len(hist_fc) >= 2:
                slope = (hist_fc["trend"].iloc[-1] - hist_fc["trend"].iloc[0]) / max(len(hist_fc) - 1, 1)
            else:
                slope = 0.0

            method_note = "Revenue forecast"  # internal — not shown to user

        except Exception as _prophet_err:
            use_prophet = False   # Prophet failed → fall through to linear

    # ── Linear + day-of-week seasonal fallback ────────────────────────────────
    if not use_prophet and not use_statsforecast:
        # Fit on raw revenue so residuals are consistent (rolling_7 fit + raw revenue
        # residuals inflates std_resid since smoothing removes the variance we measure against)
        try:
            # Recency-weighted regression: recent data points matter more so that
            # a recent downturn isn't drowned out by earlier growth.
            _days = daily["days_since_start"].values.astype(float)
            _rev  = daily["revenue"].values.astype(float)
            _half_life = max(len(_days) / 3, 7)  # exponential decay half-life
            _weights = np.exp(np.log(2) * (_days - _days[-1]) / _half_life)
            slope, intercept = np.polyfit(_days, _rev, 1, w=_weights)
        except Exception:
            slope, intercept = 0.0, float(daily["revenue"].mean())
        trend_vals = slope * daily["days_since_start"].values + intercept
        std_resid  = (daily["revenue"].values - trend_vals).std()

        daily["dow"] = daily["date_only"].dt.dayofweek
        dow_factors = (
            daily.groupby("dow")["revenue"].mean() / avg_daily
            if avg_daily > 0 else pd.Series(1.0, index=range(7))
        ).reindex(range(7), fill_value=1.0)

        last_day = daily["days_since_start"].max()
        future_days_arr = np.arange(last_day + 1, last_day + forecast_days + 1)
        future_dates    = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days)

        seasonal   = np.array([dow_factors.iloc[d.dayofweek] if d.dayofweek in dow_factors.index else 1.0 for d in future_dates])
        fcst_mid   = np.maximum(slope * future_days_arr + intercept, 0) * seasonal
        # Band formula: starts at std_resid at horizon=1 and grows as √(h/n_hist).
        # Original (1 + √(h/n)) started at 1.38×std_resid for short histories (n≈7)
        # because √(1/7)≈0.38 was non-trivial. Fix: subtract the day-1 baseline so
        # the band always opens at exactly std_resid and widens from there.
        n_hist = max(len(daily), 1)
        raw_scale = np.sqrt(np.arange(1, forecast_days + 1) / n_hist)
        horizon_scale = raw_scale - raw_scale[0]          # 0 at day 1, grows after
        fcst_upper = fcst_mid + std_resid * (1 + horizon_scale)
        fcst_lower = np.maximum(fcst_mid - std_resid * (1 + horizon_scale), 0)

        # Widen confidence intervals for short datasets — models underestimate
        # uncertainty when they haven't seen enough historical variance
        _n_history_days = len(daily)
        if _n_history_days < 60:
            _ci_multiplier = max(1.0, 60 / _n_history_days)
            _ci_center = fcst_mid
            fcst_lower = np.maximum(_ci_center - (_ci_center - fcst_lower) * _ci_multiplier, 0)
            fcst_upper = _ci_center + (fcst_upper - _ci_center) * _ci_multiplier

        if _PROPHET_AVAILABLE:  # noqa: SIM108
            method_note = "Linear trend + day-of-week seasonal (Prophet failed — check logs)."
        else:
            method_note = "Linear trend + day-of-week seasonal. Advanced forecasting can be enabled — contact support for details."

    # ── Chart ─────────────────────────────────────────────────────────────────
    fig = go.Figure()
    # Daily dots (subtle)
    fig.add_trace(go.Scatter(
        x=daily["date_only"], y=daily["revenue"],
        name="Daily revenue",
        mode="markers",
        marker=dict(size=3, color="#93c5fd", opacity=0.4),
        hovertemplate="%{x|%b %d}<br>" + _cur() + "%{y:,.0f}<extra>Daily</extra>",
    ))
    # 7-day rolling average (primary line)
    fig.add_trace(go.Scatter(
        x=daily["date_only"], y=daily["rolling_7"],
        name="7-day average",
        line=dict(color="#1e3a5f", width=2.5, shape="spline"),
        hovertemplate="%{x|%b %d}<br>" + _cur() + "%{y:,.0f}<extra>7-day avg</extra>",
    ))
    # Confidence band (upper — invisible line)
    fig.add_trace(go.Scatter(
        x=future_dates, y=fcst_upper,
        mode="lines", line=dict(color="rgba(37,99,235,0)"), showlegend=False,
        hoverinfo="skip",
    ))
    # Confidence band (lower — filled to upper)
    fig.add_trace(go.Scatter(
        x=future_dates, y=fcst_lower,
        mode="lines", line=dict(color="rgba(37,99,235,0)"),
        fill="tonexty", fillcolor="rgba(37,99,235,0.08)",
        name="Likely range",
        hoverinfo="skip",
    ))
    # Forecast line (dashed)
    fig.add_trace(go.Scatter(
        x=future_dates, y=fcst_mid,
        name="Forecast",
        line=dict(color="#2563eb", width=2.5, dash="dash", shape="spline"),
        hovertemplate="%{x|%b %d}<br>" + _cur() + "%{y:,.0f}<extra>Forecast</extra>",
    ))
    # Divider annotation between history and forecast
    _split_date = daily["date_only"].iloc[-1]
    fig.add_vline(
        x=_split_date, line=dict(color="#94a3b8", width=1, dash="dot"),
    )
    fig.add_annotation(
        x=_split_date, y=1.06, yref="paper",
        text="Today", showarrow=False,
        font=dict(size=10, color="#64748b"),
    )
    fig.update_layout(
        height=480,
        xaxis_title="",
        yaxis_title="",
        showlegend=True,
    )
    fig.update_yaxes(tickprefix=_cur(), tickformat=",.0f")
    fig.update_xaxes(tickformat="%b %d")
    st.plotly_chart(fig, use_container_width=True, key=f"forecast_{forecast_weeks}")

    # ── Metrics ───────────────────────────────────────────────────────────────
    growth_pct  = (slope / avg_daily * 100) if avg_daily > 0 else 0
    trend_label = "Upward ↑" if growth_pct > 0.5 else ("Downward ↓" if growth_pct < -0.5 else "Flat →")

    c1, c2, c3 = st.columns(3)
    if len(daily) >= 14:
        last_7 = daily["revenue"].tail(7).sum()
        prev_7 = daily["revenue"].tail(14).head(7).sum()
        wow = ((last_7 - prev_7) / prev_7 * 100) if prev_7 > 0 else 0
        c1.metric("This week vs last week", f"{wow:+.1f}%", "vs prior 7 days")
    else:
        c1.metric("This week vs last week", "—", "Need 14+ days")

    c2.metric("Trend direction", trend_label, f"{growth_pct:+.1f}% daily avg")
    c3.metric("Avg daily revenue", f"{_cur()}{avg_daily:,.2f}")

    projected_total = float(np.sum(fcst_mid))
    trend_word = "up" if growth_pct > 0.5 else ("down" if growth_pct < -0.5 else "flat")
    st.info(
        f"Based on your recent trend, you're on track for roughly **{_cur()}{projected_total:,.0f}** "
        f"in revenue over the next {forecast_weeks} week{'s' if forecast_weeks != 1 else ''}. "
        f"This week is trending **{trend_word}** compared to last week."
    )
    st.caption(
        "ℹ️ The shaded area shows the likely range your revenue could land in — based on how much it has varied day-to-day. "
        "The further out the forecast goes, the wider this range gets. Use the middle line for planning; use the lower edge for a conservative cash-flow view."
    )

    # ── Per-product predictions ───────────────────────────────────────────
    st.markdown("---")
    st.subheader("📦 Which Items Are Driving This?")
    st.caption("How each of your top products is trending over the same period.")
    prod_forecasts = _per_product_forecast(df, forecast_weeks)
    if prod_forecasts:
        # Multi-line chart — weekly revenue history, top 5 products
        chart_items = [p for p in prod_forecasts[:5] if len(p["weekly_data"]) >= 4]
        if chart_items:
            fig_multi = go.Figure()
            _colors = ["#2563eb", "#16a34a", "#dc2626", "#9333ea", "#ea580c"]
            for ci, fp in enumerate(chart_items):
                fig_multi.add_trace(go.Scatter(
                    x=fp["weekly_data"]["week"],
                    y=fp["weekly_data"]["revenue"],
                    name=str(fp["product"])[:22],
                    line=dict(color=_colors[ci % len(_colors)], width=2.5, shape="spline"),
                    mode="lines+markers",
                    marker=dict(size=5, line=dict(width=2, color="white")),
                    hovertemplate="%{x|%b %d}<br>" + _cur() + "%{y:,.0f}<extra>%{fullData.name}</extra>",
                ))
            fig_multi.update_layout(
                height=340, showlegend=True,
                xaxis_title="", yaxis_title="",
                margin=dict(l=48, r=16, t=10, b=24),
            )
            fig_multi.update_yaxes(tickprefix=_cur(), tickformat=",.0f")
            fig_multi.update_xaxes(tickformat="%b %d")
            st.plotly_chart(fig_multi, use_container_width=True, key="prod_multi_chart")

        # Summary table
        table_rows = []
        for fp in prod_forecasts:
            if fp["projected_change_dollars"] is not None:
                change_str = f"{_cur()}{fp['projected_change_dollars']:+,.0f}"
                conf_lbl = "🟡 Worth testing"
            else:
                change_str = "—"
                conf_lbl = "🔴 Need more data"
            table_rows.append({
                "Product": fp["product"],
                "Direction": fp["direction"],
                f"Weekly Avg ({_cur()})": fp["current_weekly_avg"],
                f"Proj. ±{forecast_weeks}wk ({_cur()})": change_str,
                "Confidence": conf_lbl,
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        # Highlight top mover and top decliner
        growing = [p for p in prod_forecasts if "Growing" in p["direction"]]
        declining_prods = [p for p in prod_forecasts if "Declining" in p["direction"]]
        if growing:
            tg = growing[0]
            st.success(
                f"**{tg['product']}** is your strongest grower "
                f"(+{tg['slope_pct_weekly']:.1f}%/wk). "
                f"Keep it stocked and prominently placed."
            )
        if declining_prods:
            td = declining_prods[0]
            st.warning(
                f"**{td['product']}** is trending down "
                f"({td['slope_pct_weekly']:+.1f}%/wk). "
                f"Investigate causes — consider a promotion or bundle."
            )
    else:
        st.info("Upload data with dates and at least 4 weeks of history to see per-product predictions.")

    # ── Forecast explanation (plain language) ─────────────────────────────
    with st.expander("📖 How to read this forecast", expanded=_tpl_expanded("forecast")):
        projected_weekly_avg = projected_total / max(forecast_weeks, 1)
        st.write(
            "**The solid blue line** is your recent sales history smoothed out. "
            "**The dashed blue line** is the forecast — where your revenue is likely headed based on your trends. "
            "**The shaded area** is the likely range — actual results could land anywhere in it. "
            "The further out, the wider the range. "
            "Use the middle line for planning; use the bottom edge for a conservative view."
        )
        st.write(
            f"**Projected total over the next {forecast_weeks} week{'s' if forecast_weeks != 1 else ''}:** "
            f"{_cur()}{projected_total:,.0f} total · {_cur()}{projected_weekly_avg:,.0f}/week average"
        )

    # ── Growth Action Plan ────────────────────────────────────────────────
    trend_key = "upward" if growth_pct > 1 else ("downward" if growth_pct < -1 else "flat")
    actions = _growth_actions(
        trend_key,
        df=df,
        growth_pct=growth_pct,
        avg_daily=avg_daily,
        projected_total=projected_total,
        forecast_weeks=forecast_weeks,
        wow=locals().get("wow"),
    )

    st.markdown("---")
    st.subheader("What should you do next?")
    trend_context = {
        "upward": "Your revenue trend is **growing** — capitalize on momentum before it plateaus.",
        "downward": "Your revenue trend is **declining** — these steps are designed to stabilize and reverse the slide.",
        "flat": "Your revenue is **stable** — these steps are designed to break out of the plateau.",
    }
    st.caption(trend_context[trend_key])

    for i, action in enumerate(actions, 1):
        st.success(f"**Step {i}:** {action}")

    # ── Risk / Opportunity flags ──────────────────────────────────────────
    st.markdown("**⚠️ Watch-outs & Opportunities**")
    flag_cols = st.columns(2)
    if trend_key == "upward":
        flag_cols[0].warning("**Risk:** Growth can attract competitors or cause quality dips. Don't let operational capacity fall behind demand.")
        flag_cols[1].info("**Opportunity:** You're in the best position to raise prices or launch a premium tier — customers who keep buying are price-tolerant.")
    elif trend_key == "downward":
        flag_cols[0].warning("**Risk:** If the decline continues for 3+ weeks, it may reflect a structural issue (competition, seasonality, product fatigue) — not just a slow week.")
        flag_cols[1].info("**Opportunity:** Declining periods are the best time to negotiate better terms with suppliers and renegotiate variable costs.")
    else:
        flag_cols[0].warning("**Risk:** Flat revenue in an inflationary environment means real purchasing power is eroding. Costs rise; revenue stays the same — margins shrink.")
        flag_cols[1].info("**Opportunity:** Stable customer base = a captive audience for new product introductions. They already trust you — give them something new to try.")


# =============================================================================
# PRODUCT CLUSTERING HELPER
# =============================================================================

@st.cache_data(ttl=600)
def _get_product_clusters(df: pd.DataFrame, mapping_key: tuple = ()) -> pd.DataFrame | None:
    """Run K-Means and return product-level aggregates. Cached for fast navigation.

    mapping_key is included so the cache invalidates when column mapping changes,
    preventing stale clusters if two mappings produce numerically identical DataFrames.
    """
    agg = df.groupby("product").agg(
        quantity=("quantity", "sum"),
        revenue=("revenue", "sum")
    ).reset_index()
    if len(agg) < 4:
        return None

    # avg_txn kept for display / hover only — NOT used as a clustering feature.
    # avg_txn = revenue / quantity is algebraically derived from the other two columns,
    # so including it introduces perfect feature collinearity: the third axis is a
    # deterministic function of the first two, distorting cluster geometry and making
    # StandardScaler ill-conditioned.  Use only the two independent signals.
    agg["avg_txn"] = agg["revenue"] / agg["quantity"].clip(lower=1)

    # Log-transform to handle right-skewed revenue/quantity distributions
    # (a few bestsellers can otherwise dominate cluster geometry)
    X_raw = agg[["quantity", "revenue"]].values.clip(min=0)  # guard negatives; 2 independent features only
    X_log = np.log1p(X_raw)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_log)
    # If any feature has zero variance after scaling, StandardScaler returns NaN — fall back to raw log
    _used_scaler = not np.isnan(X_scaled).any()
    if not _used_scaler:
        X_scaled = X_log  # unscaled but at least finite

    # Find the best k (2-4) using silhouette score — avoids forcing 4 clusters
    # on datasets where fewer natural groups exist
    best_k, best_sil = 2, None
    max_k = min(4, len(agg) - 1)
    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        lbls = km.fit_predict(X_scaled)
        # silhouette_score fails when all distances are zero (identical data)
        # or when only 1 unique label is assigned
        if len(set(lbls)) < 2:
            continue
        try:
            sil = silhouette_score(X_scaled, lbls)
        except ValueError:
            continue
        if best_sil is None or sil > best_sil:
            best_sil, best_k = sil, k

    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    agg["cluster"] = kmeans.fit_predict(X_scaled)
    # When scaler was not applied (fallback), cluster centers are already in log space — skip inverse_transform
    if _used_scaler:
        centers_raw = np.expm1(scaler.inverse_transform(kmeans.cluster_centers_))
    else:
        centers_raw = np.expm1(kmeans.cluster_centers_)
    # Centers only have the 2 clustering features (quantity, revenue); avg_txn is not a cluster dimension
    centers = pd.DataFrame(centers_raw, columns=["quantity", "revenue"])
    # _label_clusters assigns up to 4 labels; with fewer clusters some labels simply won't appear
    cluster_labels = _label_clusters(centers)
    agg["category"] = agg["cluster"].map(cluster_labels)
    _sil_val = round(best_sil, 3) if best_sil is not None else None
    agg.attrs["silhouette_score"] = _sil_val  # may not survive all DataFrame ops
    agg.attrs["n_clusters"] = best_k
    # Store redundantly as constant columns so the values survive any downstream
    # DataFrame filtering (e.g. agg[agg["category"] == cat]) — .attrs does not
    # propagate through boolean-indexing on older pandas/Streamlit combinations.
    agg["_sil_score"] = _sil_val
    agg["_n_clusters"] = best_k
    return agg


# =============================================================================
# ADVISORY INTELLIGENCE — Trends, anomalies, recommendations
# =============================================================================

def _detect_overview_insights(df: pd.DataFrame) -> dict:
    """Detect revenue trends and anomalies; return insights + recommendations."""
    out: dict = {"has_dates": False, "insights": [], "anomalies": [], "recommendations": [], "trend": "flat"}
    if not _has_dates(df):
        return out
    out["has_dates"] = True
    dfc = df.copy()
    dfc["date_only"] = dfc["date"].dt.date
    _daily_raw = dfc.groupby("date_only")["revenue"].sum().sort_index()
    # Fill calendar gaps with 0 so WoW uses true 7-calendar-day windows
    # and anomaly detection sees zero-revenue days (closures, outages).
    _full_idx = pd.date_range(_daily_raw.index.min(), _daily_raw.index.max(), freq="D").date
    daily = _daily_raw.reindex(_full_idx, fill_value=0.0)
    n = len(daily)

    # ── Week-over-week ─────────────────────────────────────────────────────
    if n >= 14:
        last7 = daily.tail(7).sum()
        prev7 = daily.tail(14).head(7).sum()
        wow = (last7 - prev7) / prev7 * 100 if prev7 > 0 else 0
        out["wow_pct"] = round(wow, 1)
        dollar_delta = last7 - prev7
        delta_str = f"{_cur()}{abs(dollar_delta):,.0f} {'more' if dollar_delta >= 0 else 'less'} than last week"
        if wow > 10:
            out["insights"].append(f"Revenue is up **{wow:+.1f}%** this week vs last ({delta_str}) — strong momentum.")
            out["recommendations"].append(
                f"Momentum is on your side (+{delta_str}) — run a limited-time upsell on your top item this week to amplify the surge while customers are engaged."
            )
        elif wow < -10:
            out["insights"].append(f"Revenue is down **{wow:+.1f}%** vs last week ({delta_str}) — needs attention.")
            out["recommendations"].append(
                f"Revenue slipped {delta_str}. A quick 'bring a friend' deal or 3-day flash sale on your best seller can interrupt the slide. Act this week while it's recoverable."
            )
        else:
            out["insights"].append(f"Revenue is steady — this week vs last week: **{wow:+.1f}%** ({delta_str}).")
            out["recommendations"].append(
                "Steady is safe, not growing. Try a daily special this week — even small lifts in average order value compound meaningfully over time."
            )

    # ── Anomaly detection (robust MAD-based) ────────────────────────────────
    # Uses median + MAD instead of mean/std to avoid the self-masking problem.
    # MAD scale factor 1.4826 makes it consistent with std under normality.
    # Days with very few transactions are excluded — low volume naturally produces
    # volatile revenue that triggers false "dip" alerts.
    if n >= 14:
        # Count transactions per day to suppress noise from low-data days
        _daily_txn_counts = dfc.groupby("date_only").size()
        _daily_txn_counts = _daily_txn_counts.reindex(_full_idx, fill_value=0)
        _MIN_TXN_PER_DAY_FOR_ANOMALY = 3

        # Only include days with sufficient transactions in the anomaly calculation
        _sufficient_days = _daily_txn_counts >= _MIN_TXN_PER_DAY_FOR_ANOMALY
        daily_for_anomaly = daily[_sufficient_days]

        if len(daily_for_anomaly) >= 10:  # need enough qualified days for MAD
            median_r = daily_for_anomaly.median()
            mad_r = np.median(np.abs(daily_for_anomaly - median_r))
            mad_scaled = mad_r * 1.4826  # robust σ estimate
            if mad_scaled > 0:
                robust_z = (daily_for_anomaly - median_r) / mad_scaled
                for date, z_val in robust_z[np.abs(robust_z) > _MAD_ANOMALY_Z].items():
                    rev = daily_for_anomaly[date]
                    direction = "spike" if rev > median_r else "dip"
                    out["anomalies"].append({
                        "date": str(date),
                        "revenue": rev,
                        "direction": direction,
                        "z_score": round(float(abs(z_val)), 1),
                    })

    # ── Overall trend (linear slope) ───────────────────────────────────────
    if n >= 7:
        x = np.arange(n)
        slope, _ = np.polyfit(x, daily.values, 1)
        avg = daily.mean()
        slope_pct = slope / avg * 100 if avg > 0 else 0
        out["slope_pct"] = round(slope_pct, 2)
        out["trend"] = "upward" if slope_pct > 0.5 else ("downward" if slope_pct < -0.5 else "flat")

    return out


def _find_rising_stars(
    df: pd.DataFrame,
    n: int = 5,
    min_revenue: float = 0.0,
    min_units: float = 0.0,
) -> pd.DataFrame | None:
    """Products with the highest revenue momentum over last 30 days vs prior period.

    Args:
        min_revenue: Minimum recent-period revenue required to surface a product.
        min_units: Minimum recent-period unit quantity required to surface a product.
    """
    if not _has_dates(df):
        return None
    dfc = df.copy()
    dfc["date_only"] = pd.to_datetime(dfc["date"].dt.date)
    max_date = dfc["date_only"].max()
    # Compare last 30 days vs the PRIOR 30 days (equal periods — avoids comparing
    # 1 month vs 5 months which unfairly penalizes the recent period).
    recent_start = max_date - pd.Timedelta(days=29)
    prior_end = max_date - pd.Timedelta(days=30)
    prior_start = max_date - pd.Timedelta(days=59)
    if dfc["date_only"].min() > prior_start:
        return None  # Not enough history for a meaningful prior period
    recent_df = dfc[dfc["date_only"] >= recent_start]
    prior_df = dfc[(dfc["date_only"] >= prior_start) & (dfc["date_only"] <= prior_end)]
    recent = recent_df.groupby("product")["revenue"].sum()
    recent_qty = recent_df.groupby("product")["quantity"].sum()
    older = prior_df.groupby("product")["revenue"].sum()
    both = recent.index.intersection(older.index)
    if both.empty:
        return None
    # Apply minimum thresholds before ranking
    eligible = both[
        (recent[both] >= min_revenue) &
        (recent_qty.reindex(both, fill_value=0) >= min_units)
    ]
    if eligible.empty:
        return None
    # Filter out products with negligible older-period revenue to prevent
    # near-zero denominators from inflating growth % (e.g. $0.01 → $50 = 499,900%).
    # Use the 10th percentile of prior-period revenue rather than median/10:
    # - median/10 is unstable when the distribution is skewed (a high-revenue outlier
    #   can push the floor so high that legitimate small-product growth is excluded).
    # - The 10th percentile adapts to skewed distributions while still filtering
    #   the truly negligible tail without removing legitimate growth signals.
    older_vals = older[eligible].values
    # Percentile-based floor is unreliable with very few products; fall back to $1 minimum.
    if len(older_vals) >= 10:
        older_floor = max(float(np.percentile(older_vals, 10)), 1.0)
    else:
        older_floor = 1.0
    eligible = eligible[older[eligible] >= older_floor]
    if eligible.empty:
        return None
    growth_pct = (recent[eligible] - older[eligible]) / older[eligible].clip(lower=1.0) * 100
    # Velocity weight: combine percentage growth with absolute scale
    # log(revenue+1) ensures a $500→$800 product outranks a $1→$5 product
    velocity_score = growth_pct * np.log1p(recent[eligible])
    growth = velocity_score.sort_values(ascending=False)

    rising = growth[growth > 0].head(n).reset_index()
    rising.columns = ["product", "velocity_score"]
    rising["growth_pct"] = growth_pct[rising["product"]].values
    rising["recent_rev"] = rising["product"].map(recent).values
    rising["recent_units"] = rising["product"].map(recent_qty).values
    return rising if not rising.empty else None


def _decline_history_insufficient(df: pd.DataFrame) -> bool:
    """True if the dataset spans less than 60 days — not enough history for 30-vs-30 decline comparison."""
    if not _has_dates(df):
        return False
    dfc = df.copy()
    dfc["date_only"] = pd.to_datetime(dfc["date"].dt.date)
    max_date = dfc["date_only"].max()
    prior_start = max_date - pd.Timedelta(days=59)
    return bool(dfc["date_only"].min() > prior_start)


def _find_declining_products(df: pd.DataFrame, threshold_pct: float = 20) -> list:
    """Products whose revenue declined by threshold_pct% or more: recent 30 days vs prior 30 days.

    Uses equal-length rolling windows instead of a midpoint split to avoid:
    - Seasonal bias: comparing different season halves amplifies calendar effects.
    - New product penalty: a product added recently always looks bad in the "old" half.
    - Unequal period lengths: midpoint split produces asymmetric window sizes when
      data is skewed in time.

    Each result includes a 'seasonality' key:
      'possibly_seasonal' — product decline tracks the overall business decline
      'structural'        — product declining while overall business is stable/growing
      'uncertain'         — mixed signal or insufficient data for classification
    """
    if not _has_dates(df):
        return []
    dfc = df.copy()
    dfc["date_only"] = pd.to_datetime(dfc["date"].dt.date)
    max_date = dfc["date_only"].max()

    # Equal 30-day windows: recent period vs immediately preceding period
    recent_start = max_date - pd.Timedelta(days=29)
    prior_end    = max_date - pd.Timedelta(days=30)
    prior_start  = max_date - pd.Timedelta(days=59)

    # Require at least 60 days of history; otherwise the windows overlap or are empty
    if dfc["date_only"].min() > prior_start:
        return []

    recent_df = dfc[dfc["date_only"] >= recent_start]
    prior_df  = dfc[(dfc["date_only"] >= prior_start) & (dfc["date_only"] <= prior_end)]

    # Minimum transaction floor per product per window — avoids noise from products
    # with very few transactions producing large false-decline signals.
    # Raised from 3 → 5: with only 3 txns in a 30-day window a single outlier order
    # (e.g., a $0 void or a refund) shifts the total by 33%+, generating spurious signals.
    MIN_TXN_PER_WINDOW = 5
    recent_counts = recent_df.groupby("product")["revenue"].count()
    prior_counts  = prior_df.groupby("product")["revenue"].count()

    # Day-of-week normalization: compute per-product revenue as a weekday-weighted
    # average rather than raw sum. This prevents false declines when the two 30-day
    # windows have different weekend/weekday distributions.
    def _dow_normalized_revenue(sub_df: pd.DataFrame) -> pd.Series:
        """Return per-product revenue normalized by day-of-week composition."""
        sub = sub_df.copy()
        sub["dow"] = pd.to_datetime(sub["date"]).dt.dayofweek  # 0=Mon, 6=Sun
        n_days_per_dow = sub.groupby("dow")["date"].apply(lambda x: x.dt.date.nunique())
        prod_dow = sub.groupby(["product", "dow"])["revenue"].sum()
        result = {}
        for product in sub["product"].unique():
            total = 0.0
            for dow in range(7):
                if dow in n_days_per_dow.index:
                    days = n_days_per_dow[dow]
                    rev = prod_dow.get((product, dow), 0.0)
                    # Average daily revenue for this DoW × standard 4.3 weeks
                    total += (rev / max(days, 1)) * 4.3
            result[product] = total
        return pd.Series(result)

    recent = _dow_normalized_revenue(recent_df)
    older  = _dow_normalized_revenue(prior_df)

    # Overall business change (for seasonality baseline)
    older_total  = older.sum()
    recent_total = recent.sum()
    overall_pct  = (recent_total - older_total) / max(older_total, 0.01) * 100

    both = older.index.intersection(recent.index)
    if both.empty:
        return []

    results = []
    for product in both:
        # Skip products with too few transactions in either window — unreliable signal
        if recent_counts.get(product, 0) < MIN_TXN_PER_WINDOW:
            continue
        if prior_counts.get(product, 0) < MIN_TXN_PER_WINDOW:
            continue

        old_rev = older[product]
        new_rev = recent[product]
        if old_rev <= 0:
            continue
        change_pct = (new_rev - old_rev) / old_rev * 100
        if change_pct > -threshold_pct:
            continue

        # ── Seasonality classification ─────────────────────────────────────
        # "severity" > 1 means product declined more than the overall business.
        severity = abs(change_pct) / max(abs(overall_pct), 5.0)

        if severity < 1.5 and overall_pct < -5:
            seasonality = "possibly_seasonal"
        elif overall_pct >= 0 or severity >= 3.0:
            seasonality = "structural"
        else:
            seasonality = "uncertain"

        results.append({
            "product":     product,
            "decline_pct": round(abs(change_pct), 1),
            "older_rev":   old_rev,
            "recent_rev":  new_rev,
            "seasonality": seasonality,
            "overall_pct": round(overall_pct, 1),
        })

    results.sort(key=lambda x: x["decline_pct"], reverse=True)
    return results


def _get_price_recommendations(df: pd.DataFrame) -> list:
    """Per-product pricing suggestions — percentile-based, framed as testable experiments.

    Statistical approach:
    - Uses dataset percentiles (not hardcoded multipliers) for high-demand / high-price thresholds.
    - Requires a minimum transaction count per product to avoid noise from rarely-sold items.
    - When cost data is absent, omits profit projections entirely (avoiding false precision
      from a 65% uniform margin assumption that may be wildly wrong for any given product).
    - All recommendations are framed as 'worth testing' rather than deterministic advice.
    """
    has_cost = "cost" in df.columns and df["cost"].notna().any()

    # Minimum transactions required before we'll make a price suggestion.
    # Raise threshold is higher because a false "raise" erodes trust more than a false "lower".
    MIN_TXN_FOR_RAISE  = 25   # strong enough signal to confidently recommend increasing price
    MIN_TXN_FOR_LOWER  = 15   # minimum to suggest a test reduction
    MIN_TXN_FOR_MAINTAIN = 15

    agg_dict = {"quantity": ("quantity", "sum"), "revenue": ("revenue", "sum"),
                "transactions": ("revenue", "count")}
    if has_cost:
        agg_dict["cost"] = ("cost", "sum")
    agg = df.groupby("product").agg(**agg_dict).reset_index()
    agg["avg_price"] = agg["revenue"] / agg["quantity"].clip(lower=1)

    # Only compute margin when we have actual cost data
    if has_cost:
        agg["margin"] = agg["revenue"] - agg["cost"]
        agg["margin_pct"] = agg["margin"] / agg["revenue"].clip(lower=0.01)

    # Keep only products with enough data for at least a "Lower" recommendation
    agg = agg[agg["transactions"] >= MIN_TXN_FOR_LOWER].copy()

    if len(agg) < 3:
        return []

    # Percentile-based thresholds — adapt to the actual distribution rather than
    # applying arbitrary fixed multipliers (1.5× and 0.85× were purely heuristic).
    qty_high_threshold   = agg["quantity"].quantile(_QUANTILE_HIGH)
    qty_low_threshold    = agg["quantity"].quantile(_QUANTILE_LOW)
    price_low_threshold  = agg["avg_price"].quantile(_QUANTILE_LOW)
    price_high_threshold = agg["avg_price"].quantile(_QUANTILE_HIGH)
    if has_cost:
        margin_high_threshold = agg["margin"].quantile(_QUANTILE_HIGH)

    cur = _cur()

    recs = []
    for _, row in agg.iterrows():
        p    = row["product"]
        price = row["avg_price"]
        qty   = row["quantity"]
        n_txn = int(row["transactions"])

        # ── High demand, low price → suggest a modest test increase ──────
        if qty >= qty_high_threshold and price <= price_low_threshold and n_txn >= MIN_TXN_FOR_RAISE:
            sug = round(price * 1.05, 2)  # 5% — conservative test, not deterministic
            # Elasticity-adjusted revenue signal (directional only)
            _e, _, _, _note = _estimate_product_elasticity(df, p)
            _e_used = _e if _e is not None else None
            if _e_used is not None:
                adj_qty = qty * (1 - _e_used * 0.05)
                rev_signal = f"estimated revenue change: {cur}{adj_qty * sug - qty * price:+,.0f} (based on how customers have responded to past price changes — test before acting)"
            else:
                rev_signal = "not enough price variation to predict the impact — treat as a starting point only"
            reason = (
                f"High demand relative to your other products ({int(qty)} units, in the top third) "
                f"with a below-average price (in the bottom third). A small price increase may be "
                f"worth testing. Suggested starting point: {cur}{sug:.2f} (+5%). "
                f"Run for 2 weeks and monitor unit volume. {rev_signal}."
            )
            _margin_pct_val = None
            if has_cost:
                _margin_pct_val = row["margin_pct"]
                reason += f" Current margin: {_margin_pct_val:.0%}."
                # Cost-aware annotation: if margin data shows this product is below-median margin,
                # note that cost reduction may be more impactful than a price increase
                if "margin_pct" in agg.columns:
                    median_margin = agg["margin_pct"].median()
                    if _margin_pct_val < median_margin:
                        reason += (
                            f" Note: this product's margin ({_margin_pct_val:.0%}) is below your "
                            f"portfolio median ({median_margin:.0%}). Negotiating a lower cost from "
                            f"your supplier may be more impactful than raising the customer price."
                        )
            recs.append({
                "product": p, "action": "↑ Raise Price",
                "current": price, "suggested": sug,
                "n_txn": n_txn,
                "reason": reason,
                "margin_pct": _margin_pct_val,
                "priority": 0,
            })

        # ── High price, low demand → suggest a modest test reduction ─────
        elif price >= price_high_threshold and qty <= qty_low_threshold and n_txn >= MIN_TXN_FOR_LOWER:
            sug = round(price * 0.95, 2)  # 5% — conservative test
            reason = (
                f"Priced in the top third of your products but selling in the bottom third "
                f"({int(qty)} units). A modest price reduction may be worth testing to see "
                f"if volume responds. Suggested: {cur}{sug:.2f} (−5%) for 2 weeks. "
                f"If volume doesn't improve meaningfully, the issue may be visibility or "
                f"product-market fit rather than price. Do not reduce permanently without a test."
            )
            recs.append({
                "product": p, "action": "↓ Consider Lowering",
                "current": price, "suggested": sug,
                "n_txn": n_txn,
                "reason": reason,
                "priority": 1,
            })

        # ── Strong performer: high margin, price in the upper range → protect ──
        elif has_cost and price >= price_high_threshold and row["margin"] >= margin_high_threshold and n_txn >= MIN_TXN_FOR_MAINTAIN:
            recs.append({
                "product": p, "action": "✓ Maintain",
                "current": price, "suggested": price,
                "n_txn": n_txn,
                "reason": (
                    f"Strong margin ({row['margin_pct']:.0%}) at a competitive price point. "
                    "Avoid discounting. Consider bundling with a lower-margin item to lift "
                    "average order value without eroding this product's unit economics."
                ),
                "priority": 2,
            })
        elif not has_cost and price >= price_high_threshold and qty >= qty_high_threshold and n_txn >= MIN_TXN_FOR_MAINTAIN:
            # Without cost data we can only observe revenue performance
            recs.append({
                "product": p, "action": "✓ Maintain",
                "current": price, "suggested": price,
                "n_txn": n_txn,
                "reason": (
                    f"High price and high volume ({int(qty)} units) — a strong revenue signal. "
                    "Protect this price point and consider a bundle to lift average order value."
                ),
                "priority": 2,
            })

    recs.sort(key=lambda x: x["priority"])
    return recs[:8]




def _growth_actions(
    trend: str,
    df: pd.DataFrame | None = None,
    growth_pct: float = 0,
    avg_daily: float = 0,
    projected_total: float = 0,
    forecast_weeks: int = 4,
    wow: float | None = None,
) -> list:
    """Actionable recommendations tied to the forecast trend direction.

    When df is provided, recommendations reference actual product names and figures.
    """
    cur = _cur()

    # Extract real metrics from data
    top_product    = ""
    second_product = ""
    bottom_product = ""
    top_rev        = 0.0
    bottom_rev     = 0.0
    total_rev      = 0.0
    top_avg_txn    = 0.0

    if df is not None and not df.empty:
        by_rev    = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
        total_rev = float(by_rev.sum())
        if len(by_rev) >= 1:
            top_product = str(by_rev.index[0])
            top_rev     = float(by_rev.iloc[0])
        if len(by_rev) >= 2:
            second_product = str(by_rev.index[1])
        if len(by_rev) >= 1:
            bottom_product = str(by_rev.index[-1])
            bottom_rev     = float(by_rev.iloc[-1])
        top_rows    = df[df["product"] == top_product] if top_product else df
        top_avg_txn = top_rev / max(len(top_rows), 1)

    top_share_pct    = (top_rev / total_rev * 100) if total_rev > 0 else 0
    bottom_share_pct = (bottom_rev / total_rev * 100) if total_rev > 0 else 0
    weekly_avg       = avg_daily * 7

    top_ref    = f"**{top_product}**" if top_product else "your best seller"
    second_ref = f"**{second_product}**" if second_product else "your second-best item"
    bottom_ref = f"**{bottom_product}**" if bottom_product else "your lowest-volume items"

    growth_abs = abs(growth_pct)

    if trend == "upward":
        wow_note      = f" — you're already up {wow:+.1f}% vs last week" if wow is not None and wow > 0 else ""
        price_dollars = round(top_avg_txn * 0.06, 2) if top_avg_txn > 0 else 0
        price_note    = f" (about {cur}{price_dollars:,.2f} more per sale)" if price_dollars > 0 else ""
        return [
            f"**Double down on {top_ref}:** Revenue is growing at +{growth_abs:.1f}%/day{wow_note}. Introduce a complementary item alongside {top_ref} while customers are in a buying mood — bundle or upsell first, then introduce.",
            f"**Test a price increase on {second_ref}:** Growth periods absorb price changes more easily. A 5–8% increase{price_note} for 2 weeks will tell you whether volume holds — if it does, that's pure margin with no extra work.",
            f"**Build loyalty around {top_ref}:** Traffic is up and {top_ref} drives {top_share_pct:.0f}% of your revenue. A loyalty program tied to {top_ref} is cheap, captures customers now, and extends the growth curve.",
            f"**Lock in supply for {top_ref}:** Stockouts hurt most when demand is rising. Confirm inventory and supplier lead times now — at {cur}{weekly_avg:,.0f}/week in revenue, one stockout week is a real loss.",
        ]
    elif trend == "downward":
        wow_note    = f" (down {abs(wow):.1f}% vs last week)" if wow is not None and wow < 0 else ""
        weekly_loss = weekly_avg * (growth_abs / 100)
        return [
            f"**Run a 3-day promo on {top_ref} this week{wow_note}:** A flash sale or 'bring a friend' deal can interrupt a -{growth_abs:.1f}%/day slide — act now while it's still recoverable, not after another slow week.",
            f"**Drop {bottom_ref} from your active offer:** It contributes only {bottom_share_pct:.1f}% of total revenue ({cur}{bottom_rev:,.0f}). Low performers carry hidden costs — storage, time, and operational complexity. Remove it and focus energy on what works.",
            f"**Drive repeat visits with {top_ref}:** Keeping one existing customer costs 5× less than finding a new one. A 'come back this week' incentive tied to {top_ref} — your {cur}{top_rev:,.0f} earner — is your highest-ROI move right now.",
            f"**Re-engage past customers now:** At {cur}{weekly_avg:,.0f}/week and falling, a targeted 'We miss you' offer to lapsed buyers — featuring {top_ref} — can recover revenue faster than finding new customers.",
        ]
    else:  # flat
        addon_price = max(1, round(top_avg_txn * 0.10)) if top_avg_txn > 0 else 2
        return [
            f"**Feature {top_ref} prominently for 2 weeks:** Revenue is flat at ~{cur}{weekly_avg:,.0f}/week. Moving it to your most visible position is free and can break the plateau — track weekly totals before and after.",
            f"**Add a {cur}{addon_price} add-on when {top_ref} is ordered:** With steady traffic the easiest win is a small complement or upgrade. Even a 15% attach rate on {top_ref} lifts your weekly average meaningfully.",
            f"**Create off-peak urgency:** Identify your 2 slowest hours and run a limited offer during them. This unlocks dormant revenue without cannibalizing {top_ref} peak sales.",
            f"**Invest in reviews for {top_ref}:** Flat growth often means weak new-customer discovery. A Google/Yelp push featuring {top_ref} costs nothing, takes one afternoon to set up, and compounds for months.",
        ]


# =============================================================================
# PER-PRODUCT FORECAST HELPER
# =============================================================================

def _per_product_forecast(df: pd.DataFrame, forecast_weeks: int) -> list | None:
    """Linear trend forecast per top product. Returns list of dicts or None."""
    if not _has_dates(df):
        return None
    top_products = df.groupby("product")["revenue"].sum().nlargest(8).index.tolist()
    # Determine full weeks in the dataset (exclude partial first and last weeks)
    _data_min = df["date"].min()
    _data_max = df["date"].max()
    _first_full_week = (_data_min + pd.Timedelta(days=(7 - _data_min.dayofweek) % 7)).normalize()
    _last_full_week_end = (_data_max - pd.Timedelta(days=(_data_max.dayofweek + 1) % 7)).normalize()
    results = []
    for product in top_products:
        prod_df = df[df["product"] == product].copy()
        prod_df["week"] = prod_df["date"].dt.to_period("W").dt.start_time
        weekly = prod_df.groupby("week")["revenue"].sum().reset_index()
        weekly.columns = ["week", "revenue"]
        # Drop partial first/last weeks to avoid biasing the slope calculation
        if len(weekly) > 2:
            weekly = weekly[
                (weekly["week"] >= _first_full_week) &
                (weekly["week"] <= _last_full_week_end)
            ]
        if len(weekly) < 4:
            continue
        weekly["days"] = (weekly["week"] - weekly["week"].min()).dt.days
        x = weekly["days"].values.astype(float)
        y = weekly["revenue"].values.astype(float)
        # Recency-weighted so recent declines aren't masked by old growth
        _hl = max(len(x) / 3, 3)
        _w = np.exp(np.log(2) * (x - x[-1]) / (_hl * 7))
        slope, intercept = np.polyfit(x, y, 1, w=_w)
        avg_weekly = float(y.mean())
        slope_pct = slope / avg_weekly * 100 if avg_weekly > 0 else 0
        direction = "↑ Growing" if slope_pct > 2 else ("↓ Declining" if slope_pct < -2 else "→ Stable")
        current_weekly = float(y[-4:].mean())
        last_day = float(x[-1])
        # Sum projected revenue for each future week and compare to flat current average.
        # This correctly accumulates the trend rather than using end-point × weeks.
        future_days_arr = last_day + np.arange(1, forecast_weeks + 1) * 7
        projected_weekly_series = np.maximum(slope * future_days_arr + intercept, 0)
        total_projected_change = float(projected_weekly_series.sum() - current_weekly * forecast_weeks)
        confident = abs(slope_pct) > 3 and len(weekly) >= 6
        results.append({
            "product": product,
            "direction": direction,
            "slope_pct_weekly": round(slope_pct, 1),
            "projected_change_dollars": round(total_projected_change, 2) if confident else None,
            "current_weekly_avg": round(current_weekly, 2),
            "weekly_data": weekly[["week", "revenue"]].copy(),
            "n_transactions": len(prod_df),
        })
    return results if results else None


# =============================================================================
# MARKET BASKET — Association rules (mlxtend Apriori)
# =============================================================================

@st.cache_data(ttl=600)
def _compute_basket_rules(df_csv: str) -> tuple:
    """Build association rules from session baskets. Cached for fast navigation.

    Returns (frequent_itemsets, rules_df, error_str | None, basket_method_str).
    Uses transaction_id column when available for true order-level baskets;
    falls back to day × location proxy.
    rules_df has extra columns: antecedent (str), consequent (str).
    """
    if not _MLXTEND_AVAILABLE:
        return None, None, "mlxtend_missing", ""

    df = pd.read_csv(io.StringIO(df_csv))
    if "date" not in df.columns:
        return None, None, "no_date", ""
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # Build baskets: prefer transaction_id when available (true per-order baskets),
    # fall back to day × location proxy when no transaction IDs exist.
    has_txn_id = (
        "transaction_id" in df.columns
        and df["transaction_id"].notna().any()
        and (df["transaction_id"] != "None").any()
        and (df["transaction_id"] != "nan").any()
    )
    if has_txn_id:
        # True order-level baskets — most accurate
        df["_session"] = df["transaction_id"].astype(str)
        basket_method = "order-level (transaction ID)"
    else:
        # Proxy: all products sold at a given location on a given day
        loc_col_val = df["location"] if "location" in df.columns else pd.Series("All", index=df.index)
        df["_session"] = df["date"].dt.date.astype(str) + "_" + loc_col_val.astype(str)
        basket_method = "day × location proxy (no transaction ID found)"
    baskets = df.groupby("_session")["product"].apply(list).reset_index()
    n_baskets = len(baskets)

    if n_baskets < 10:
        return None, None, f"insufficient_data ({n_baskets} sessions — need 10+)", basket_method

    te = _TransactionEncoder()
    te_array = te.fit_transform(baskets["product"])
    basket_df = pd.DataFrame(te_array, columns=te.columns_)

    # min_support: at least 5 occurrences or 5%, whichever is larger
    min_support = max(0.05, 5 / n_baskets)
    try:
        frequent_itemsets = _apriori(basket_df, min_support=min_support, use_colnames=True, max_len=2)
    except Exception as exc:
        return None, None, str(exc), basket_method

    if frequent_itemsets.empty:
        return None, None, "no_frequent_itemsets", basket_method

    try:
        rules = _assoc_rules(frequent_itemsets, metric="lift", min_threshold=1.05)
    except Exception as exc:
        return None, None, str(exc), basket_method

    if rules.empty:
        return None, None, "no_rules", basket_method

    # Keep single-item consequents for clarity
    rules = rules[rules["consequents"].apply(len) == 1].copy()
    if rules.empty:
        return frequent_itemsets, None, "no_single_consequent_rules", basket_method
    rules["antecedent"] = rules["antecedents"].apply(lambda x: ", ".join(sorted(str(i) for i in x)))
    rules["consequent"] = rules["consequents"].apply(lambda x: str(next(iter(x))))
    rules = rules.sort_values("lift", ascending=False).reset_index(drop=True)
    return frequent_itemsets, rules, None, basket_method


def render_market_basket(df: pd.DataFrame):
    st.header("What do customers buy together?")
    st.caption("Which items do your customers naturally buy together — and how can you use that to sell more?")

    if not _MLXTEND_AVAILABLE:
        st.warning("The 'What Sells Together' feature isn't available in the current setup. Contact support to enable it.")
        return

    if not _has_dates(df):
        st.warning("A date column is required to find product pairings.")
        return

    with st.spinner("Finding products that sell together…"):
        frequent_itemsets, rules, err, _basket_method_str = _compute_basket_rules(df.to_csv(index=False))

    if err:
        msg_map = {
            "mlxtend_missing": "Bundle analysis isn't available in the current setup. Contact support to enable it.",
            "no_date": "Date column required to find product pairings.",
            "no_frequent_itemsets": "No frequent product combinations found. Try uploading data with more transaction days.",
            "no_rules": "No strong product pairings found. Your products may sell independently.",
            "no_single_consequent_rules": "No simple two-item bundles found in your data.",
        }
        st.info(msg_map.get(err, "This analysis is unavailable with your current data. Try uploading more transaction history."))
        return

    # ── Basket method note ────────────────────────────────────────────────────
    _basket_method = _basket_method_str or "day × location proxy"
    _using_proxy = "transaction ID" not in _basket_method
    if not _using_proxy:
        st.success("✅ We can see exactly what customers buy together — your data includes order IDs.")
    else:
        st.warning(
            "⚠️ **Approximate results** — your data doesn't include an Order or Transaction ID. "
            "We're estimating based on what sold on the same day at the same location. On a busy day, "
            "this groups many items together even if no single customer bought them all. "
            "Use these results for rough ideas only. "
            "To get accurate data, re-export your sales file with an Order ID or Transaction Number column."
        )

    # ── Metrics ───────────────────────────────────────────────────────────────
    dfc = df.copy()
    has_txn = (
        "transaction_id" in dfc.columns
        and dfc["transaction_id"].notna().any()
        and (dfc["transaction_id"] != "None").any()
        and (dfc["transaction_id"] != "nan").any()
    )
    if has_txn:
        dfc["_session"] = dfc["transaction_id"].astype(str)
    else:
        _loc_col = dfc["location"].astype(str) if "location" in dfc.columns else pd.Series("All", index=dfc.index)
        dfc["_session"] = dfc["date"].dt.date.astype(str) + "_" + _loc_col
    n_sessions = dfc["_session"].nunique()

    m1, m2, m3 = st.columns(3)
    m1.metric("Orders looked at" if has_txn else "Days looked at", f"{n_sessions:,}")
    m2.metric("Common item pairs found", len(frequent_itemsets))
    m3.metric("Bundle opportunities", len(rules))

    # ── Co-occurrence heatmap ─────────────────────────────────────────────────
    two_item = frequent_itemsets[frequent_itemsets["itemsets"].apply(len) == 2].copy()
    if not two_item.empty:
        top_prods = (
            df.groupby("product")["revenue"].sum()
            .nlargest(12).index.tolist()
        )
        matrix = pd.DataFrame(0.0, index=top_prods, columns=top_prods)
        for _, row in two_item.iterrows():
            items = list(row["itemsets"])
            if items[0] in matrix.index and items[1] in matrix.columns:
                matrix.loc[items[0], items[1]] = round(row["support"] * 100, 1)
                matrix.loc[items[1], items[0]] = round(row["support"] * 100, 1)
        # Truncate long product names for cleaner axis labels
        _short_names = {n: (n[:18] + "…" if len(n) > 20 else n) for n in matrix.index}
        _matrix_display = matrix.rename(index=_short_names, columns=_short_names)
        fig_hm = px.imshow(
            _matrix_display,
            color_continuous_scale=[
                [0.0, "#f0f4f8"],
                [0.3, "#93c5fd"],
                [0.6, "#3b82f6"],
                [1.0, "#1e3a5f"],
            ],
            labels=dict(color="Co-occurrence %"),
        )
        fig_hm.update_traces(
            texttemplate="%{z:.1f}%",
            textfont=dict(size=9),
        )
        fig_hm.update_layout(
            height=460,
            coloraxis_colorbar=dict(
                title="Support %",
                thickness=12,
                len=0.6,
                outlinewidth=0,
            ),
            margin=dict(l=100, r=8, t=24, b=100),
        )
        st.plotly_chart(fig_hm, use_container_width=True)

    # ── Rules table ───────────────────────────────────────────────────────────
    st.subheader("Which items sell together?")
    if _using_proxy:
        st.caption(
            "⚠️ Since your data doesn't include order IDs, we're estimating based on what sells on the same day. "
            "Take these results as a rough guide only."
        )
    else:
        st.caption("Items higher on the list are more likely to be bought in the same order. The 'Strength' column shows how much stronger the connection is compared to random chance.")

    display = rules.head(15)[["antecedent", "consequent", "support", "confidence", "lift"]].copy()
    display.columns = ["Item A", "Item B", "% Together", "% When A, also B", "How much more likely"]
    display["% Together"]       = (display["% Together"]       * 100).round(1).astype(str) + "%"
    display["% When A, also B"] = (display["% When A, also B"] * 100).round(1).astype(str) + "%"
    display["How much more likely"] = display["How much more likely"].round(2).astype(str) + "×"
    st.dataframe(display, use_container_width=True, hide_index=True)

    # ── Bundle recommendations ────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Which items should you bundle?")

    if _using_proxy:
        # Proxy mode: co-occurrence is day × location, not individual customer baskets.
        # Rules reflect "popular products appear on the same busy days" — not actual
        # customer buying behaviour. Acting on these as bundle signals risks misleading
        # the owner, so we suppress actionable recommendations entirely.
        st.warning(
            "⚠️ **Bundle suggestions unavailable without order IDs.** "
            "Without a Transaction or Order ID column, we can't tell whether two items were "
            "actually bought by the same customer. "
            "Re-export your sales data with an Order ID column to unlock bundle recommendations."
        )
    else:
        st.caption("Concrete actions for your top pairings — bundle deals that can increase what each customer spends.")

        agg_p = df.groupby("product").agg(revenue=("revenue", "sum"), quantity=("quantity", "sum")).reset_index()
        agg_p["avg_price"] = agg_p["revenue"] / agg_p["quantity"].clip(lower=1)
        price_map = agg_p.set_index("product")["avg_price"].to_dict()
        cur = _cur()

        # Revenue-weighted bundle impact: prioritizes high-value, high-confidence pairs
        _rules_ranked = rules.copy()
        _rules_ranked["_price_a"] = _rules_ranked["antecedent"].map(price_map).fillna(0)
        _rules_ranked["_price_b"] = _rules_ranked["consequent"].map(price_map).fillna(0)
        _rules_ranked["bundle_impact"] = (
            _rules_ranked["lift"] *
            (_rules_ranked["_price_a"] + _rules_ranked["_price_b"]) *
            _rules_ranked["support"]
        )
        _rules_ranked = _rules_ranked.sort_values("bundle_impact", ascending=False)

        for idx, rule in _rules_ranked.head(8).iterrows():
            ant, cons = rule["antecedent"], rule["consequent"]
            lift, conf_pct = rule["lift"], rule["confidence"] * 100
            p1, p2 = price_map.get(ant, 0), price_map.get(cons, 0)

            with st.expander(f"🔗 **{ant}** + **{cons}** — bought together {lift:.1f}× more often"):
                col_text, col_kpi = st.columns([4, 1])
                with col_text:
                    st.write(
                        f"Customers who buy **{ant}** also buy **{cons}** "
                        f"**{conf_pct:.0f}% of the time** — {lift:.1f}× more often than you'd expect by chance."
                    )
                    if p1 > 0 and p2 > 0:
                        bundle_price = (p1 + p2) * 0.90
                        st.success(
                            f"**Bundle deal:** Offer **{ant} + {cons}** for {cur}{bundle_price:.2f} "
                            f"(vs {cur}{p1 + p2:.2f} separately). A 10% combo discount drives both items "
                            f"and lifts your average order value."
                        )
                    else:
                        st.success(
                            f"Feature **{ant}** and **{cons}** together as a daily combo — "
                            f"they already naturally sell on the same days."
                        )
                        st.caption("Bundle price unavailable — add a unit price column to your data for a specific discount suggestion.")
                with col_kpi:
                    st.metric("How much more likely", f"{lift:.2f}×")
                    st.metric("Buy rate", f"{conf_pct:.0f}%")

    # ── How to read ───────────────────────────────────────────────────────────
    with st.expander("📖 What do these numbers mean?"):
        st.write(
            "**% Together** = how often these two items were sold on the same day (or in the same order). "
            "**% When A, also B** = when someone buys item A, what percent of the time do they also get item B? "
            "**How much more likely** = how much more often they appear together than you'd expect by chance. "
            "A value of 2.0× means customers buy them together twice as often as random chance. "
            "Use these to design combo deals, train your staff on upsell suggestions, and build meal packages."
        )
        if not _using_proxy:
            st.write(
                "**These results are based on actual individual orders** — the most accurate way to see what customers buy together."
            )
        else:
            st.write(
                "**These results are based on same-day sales**, not individual customer orders. "
                "Popular items will appear together often just because they both sell on busy days — "
                "not because the same customer bought both. For more reliable results, add an Order ID column to your data."
            )


# =============================================================================
# HEALTH BRIEF — Auto-generated 2-paragraph business summary on data load
# =============================================================================

def _generate_health_brief(df: pd.DataFrame, product_clusters) -> dict | None:
    """Generate and cache a 2-paragraph health brief via AI.

    Returns {"paragraph_1": str, "paragraph_2": str} or None on failure.
    """
    if len(df) < 30:
        return None

    client = _get_groq_client()
    if client is None:
        return None

    data_ctx = _build_data_context(df, product_clusters)
    cache_key = "health_brief_" + hashlib.md5(data_ctx.encode()).hexdigest()[:16]

    if cache_key in st.session_state:
        return st.session_state[cache_key]

    profile_ctx = _build_profile_context()
    profile_context_block = (
        f"\nBUSINESS PROFILE (use this to tune language and benchmarks):\n{profile_ctx}"
        if profile_ctx else ""
    )

    prompt = (
        "You are a business advisor writing a 2-paragraph health brief for a small "
        "business owner. They will read this the moment their data loads.\n\n"
        "Write exactly 2 paragraphs. No headers. No bullet points. No markdown. "
        "Plain prose only. Maximum 120 words total.\n\n"
        "Paragraph 1 — State of the business right now:\n"
        "Open with the single most important fact (revenue total, trend direction, or a "
        "standout product). Name actual numbers. Be direct — no preamble like \"based on "
        "your data.\" Just state it. End with a one-sentence read on whether the business "
        "is in a good position, needs attention, or is at a turning point.\n\n"
        "Paragraph 2 — The one thing to focus on this week:\n"
        "Name a specific product or time pattern from the data. Give one concrete action "
        "tied to a number. This should feel like advice from someone who has run a "
        "business, not a report generator.\n\n"
        "Rules:\n"
        "- Never use: \"leverage\", \"actionable\", \"insights\", \"it's worth noting\", "
        "\"the data suggests\", \"notably\", \"in conclusion\"\n"
        "- Every sentence must contain at least one number or product name from the data\n"
        "- If industry/goal is known from the business profile, use industry-appropriate "
        "language (e.g. \"covers\" for restaurants, \"footfall\" for retail)\n"
        "- 120 words maximum — enforced, not a guideline\n"
        f"{profile_context_block}\n\n"
        f"BUSINESS DATA:\n{data_ctx}"
    )

    try:
        response = _groq_generate(client, prompt)
        full_text = (response.text or "").strip()

        # Split on first blank line between paragraphs
        parts = full_text.split("\n\n", 1)
        if len(parts) == 2:
            result = {"paragraph_1": parts[0].strip(), "paragraph_2": parts[1].strip()}
        else:
            result = {"paragraph_1": full_text, "paragraph_2": ""}

        st.session_state[cache_key] = result
        return result
    except Exception:
        return None


def _render_health_brief(df: pd.DataFrame, product_clusters) -> None:
    """Render the auto-generated health brief card at the top of Action Center."""
    if len(df) < 30:
        return

    data_ctx = _build_data_context(df, product_clusters)
    cache_key = "health_brief_" + hashlib.md5(data_ctx.encode()).hexdigest()[:16]

    already_cached = cache_key in st.session_state

    if already_cached:
        brief = st.session_state[cache_key]
    else:
        with st.spinner("Reading your data..."):
            brief = _generate_health_brief(df, product_clusters)

    if brief is None:
        return

    p2_html = (
        f"<p style='font-family:Raleway,sans-serif;font-size:0.97rem;line-height:1.8;"
        f"color:#93c5fd;margin:0;'>{brief['paragraph_2']}</p>"
        if brief.get("paragraph_2") else ""
    )

    st.markdown(
        f"""
        <div style='background:#1e3a5f;border-radius:12px;padding:1.8rem 2rem;margin-bottom:1.5rem;'>
            <p style='font-size:0.65rem;font-weight:700;letter-spacing:0.2em;color:#93c5fd;
                      text-transform:uppercase;margin:0 0 0.8rem 0;'>YOUR BUSINESS TODAY</p>
            <p style='font-family:Raleway,sans-serif;font-size:0.97rem;line-height:1.8;
                      color:#f0f4f8;margin:0 0 0.8rem 0;'>{brief['paragraph_1']}</p>
            {p2_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# ACTION CENTER — Aggregate all signals into a ranked priority list
# =============================================================================

def _prescribe_low_activity(
    df: pd.DataFrame,
    product_clusters,
) -> dict | None:
    """Return a computed prescription action card for Low Activity products, or None."""
    if product_clusters is None:
        return None

    dead = product_clusters[product_clusters["category"] == "Low Activity"].nlargest(3, "revenue")
    if dead.empty:
        return None

    cur = _cur()
    has_dates = _has_dates(df)
    months = max((df["date"].max() - df["date"].min()).days / 30, 0.034) if has_dates else 1

    prod_agg = (
        df.groupby("product")
        .agg(quantity=("quantity", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )
    prod_lookup = prod_agg.set_index("product")

    price_lines = []
    total_recovery = 0.0
    valid_products = 0

    for _, row in dead.iterrows():
        pname = row["product"]
        if pname not in prod_lookup.index:
            continue

        p_qty = prod_lookup.loc[pname, "quantity"]
        p_rev = prod_lookup.loc[pname, "revenue"]

        # avg_price: prefer unit_price column, else revenue / quantity
        if "unit_price" in df.columns and df["unit_price"].notna().any():
            avg_price = df[df["product"] == pname]["unit_price"].mean()
        else:
            avg_price = p_rev / max(p_qty, 1)

        # Guard: skip products with zero price (avoids division issues)
        if avg_price <= 0:
            continue

        valid_products += 1
        monthly_qty = p_qty / months
        monthly_rev = p_rev / months
        discount_price = avg_price * 0.80

        # demand elasticity 1.2 for a 20% price drop → 24% qty lift
        new_qty = monthly_qty * (1 + 1.2 * 0.20)
        recovery_rev = discount_price * new_qty
        incremental = max(recovery_rev - monthly_rev, 0.0)
        total_recovery += incremental

        price_lines.append(
            f"{pname}: try {cur}{discount_price:.2f} (was {cur}{avg_price:.2f})"
        )

    # If every product had avg_price == 0, fall back
    if valid_products == 0:
        return None

    total_recovery = round(total_recovery)
    names = ", ".join(str(x) for x in dead["product"].tolist()[:3])

    return {
        "title": (
            f"Consider discounting these {len(dead)} slow items — "
            f"projected recovery: {cur}{total_recovery:,.0f}/month"
        ),
        "detail": (
            "These products are generating almost no revenue at their current price. "
            "A 20% discount could unlock dormant demand:\n"
            + "\n".join(price_lines)
            + "\nRun for 2 weeks. If volume doesn't lift, consider removing them entirely."
        ),
        "impact_dollars": float(total_recovery),
        "impact_low": round(total_recovery * 0.5, 2),
        "impact_high": round(total_recovery * 1.5, 2),
        "impact_range": (
            f"~{cur}{total_recovery:,.0f}/month if demand responds "
            f"(range: {cur}{round(total_recovery*0.5):,.0f}–"
            f"{cur}{round(total_recovery*1.5):,.0f})"
        ),
        "confidence": "directional",
        "priority": 3,
    }


def _build_action_center(df: pd.DataFrame, product_clusters) -> dict:
    """Gather all analysis signals and rank by estimated dollar impact.

    Returns dict with keys:
        quick_wins: list of action dicts (sorted by impact desc)
        watch_outs: list of action dicts (sorted by impact desc)
    """
    cur = _cur()
    has_dates = _has_dates(df)
    months = max((df["date"].max() - df["date"].min()).days / 30, 0.034) if has_dates else 1  # 0.034 ≈ 1 day

    prod_agg = (
        df.groupby("product")
        .agg(quantity=("quantity", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )
    prod_agg["avg_price"] = prod_agg["revenue"] / prod_agg["quantity"].clip(lower=1)
    prod_agg["monthly_qty"] = prod_agg["quantity"] / months
    prod_lookup = prod_agg.set_index("product")
    prod_tx_counts = df.groupby("product").size()

    quick_wins: list = []
    watch_outs: list = []

    # ── 1. Price raise opportunities ──────────────────────────────────────
    has_cost = "cost" in df.columns and df["cost"].notna().any()
    gross_margin_fallback = st.session_state.get("gross_margin_pct", 0.65)
    price_recs = _get_price_recommendations(df)
    for rec in price_recs:
        if rec["action"] == "↑ Raise Price" and rec["product"] in prod_lookup.index:
            mq = prod_lookup.loc[rec["product"], "monthly_qty"]
            margin_pct = rec.get("margin_pct") or gross_margin_fallback
            revenue_gain = mq * (rec["suggested"] - rec["current"])
            # Profit impact: incremental revenue × margin rate
            impact = revenue_gain * margin_pct
            # Confidence range: ±25% reflecting demand-response uncertainty
            impact_low = impact * 0.75
            impact_high = impact * 1.25
            metric_label = "profit" if has_cost else "revenue (est. profit)"
            quick_wins.append({
                "title": f"Raise **{rec['product']}** price → {cur}{rec['suggested']:.2f}",
                "detail": (
                    f"Selling ~{int(mq)}/mo at {cur}{rec['current']:.2f} — demand is high, "
                    f"price is below your portfolio average. A 10% increase is unlikely to hurt volume. "
                    f"({margin_pct:.0%} margin on this product)"
                ),
                "impact_dollars": round(impact, 2),
                "impact_low": round(impact_low, 2),
                "impact_high": round(impact_high, 2),
                "confidence": "directional",
                "impact_range": f"Could add ~{cur}{impact:,.0f}/month",
                "impact_label": f"Could add ~{cur}{impact:,.0f}/month",
                "n_transactions": int(prod_tx_counts.get(rec["product"], 0)),
                "priority": 1,
            })

    # ── 2. Rising Stars ───────────────────────────────────────────────────
    rising = _find_rising_stars(df, n=3)
    if rising is not None:
        for _, row in rising.iterrows():
            potential = row["recent_rev"] * (row["growth_pct"] / 100)
            quick_wins.append({
                "title": f"Amplify **{row['product']}** — gaining momentum fast",
                "detail": (
                    f"Revenue up **{row['growth_pct']:.0f}%** in the last 30 days "
                    f"({cur}{row['recent_rev']:,.0f} recent). Feature as a daily special, "
                    f"stock up, and promote to sustain the trend."
                ),
                "impact_dollars": round(potential, 2),
                "confidence": "directional",
                "impact_range": f"Could add ~{cur}{potential:,.0f}/month",
                "impact_label": f"Could add ~{cur}{potential:,.0f}/month",
                "n_transactions": int(prod_tx_counts.get(row["product"], 0)),
                "priority": 2,
            })

    # ── 3. Cross-cluster bundle opportunity (Star + Hidden Gem only) ──────
    # Only fire when the two products are in DIFFERENT clusters.
    # Bundling two Stars is noise — the value is pairing a high-volume anchor
    # with an underexposed gem to lift average order value.
    if product_clusters is not None:
        stars = product_clusters[product_clusters["category"] == "Stars"].nlargest(1, "revenue")
        gems  = product_clusters[product_clusters["category"] == "Hidden Gems"].nlargest(1, "quantity")
        if not stars.empty and not gems.empty:
            star_name = str(stars.iloc[0]["product"])
            gem_name  = str(gems.iloc[0]["product"])
            star_rev  = float(stars.iloc[0]["revenue"])
            gem_qty   = int(gems.iloc[0]["quantity"])
            # Confirm they are genuinely in different clusters (star ≠ gem category)
            star_cat = str(stars.iloc[0]["category"])
            gem_cat  = str(gems.iloc[0]["category"])
            if star_cat != gem_cat and star_name != gem_name:
                # Estimate: if 10% of Star customers add the Gem at full price
                gem_price = float(gems.iloc[0]["revenue"]) / max(gem_qty, 1)
                bundle_upside = gem_price * (float(stars.iloc[0]["quantity"]) * 0.10)
                bundle_low  = round(bundle_upside * 0.6, 2)
                bundle_high = round(bundle_upside * 1.4, 2)
                quick_wins.append({
                    "title": f"Bundle **{star_name}** with **{gem_name}** to lift avg order",
                    "detail": (
                        f"**{star_name}** (Star — {_cur()}{star_rev:,.0f} revenue) drives your highest volume. "
                        f"**{gem_name}** (Hidden Gem — {gem_qty} units) has strong unit economics but low awareness. "
                        f"An 'Add {gem_name} for just a little more' upsell captures revenue from existing customers at zero acquisition cost."
                    ),
                    "impact_dollars": round(bundle_upside, 2),
                    "impact_low": bundle_low,
                    "impact_high": bundle_high,
                    "confidence": "directional",
                    "impact_range": f"Could add ~{_cur()}{bundle_upside:,.0f}/month (small, easy to test)",
                    "impact_label": f"Could add ~{_cur()}{bundle_upside:,.0f}/month",
                    "n_transactions": int(prod_tx_counts.get(star_name, 0)),
                    "priority": 3,
                })
        elif not gems.empty:
            # No Stars — just spotlight top Hidden Gem
            gem_row = gems.iloc[0]
            quick_wins.append({
                "title": f"Spotlight **{gem_row['product']}** — Hidden Gem with untapped demand",
                "detail": (
                    f"Sells well ({int(gem_row['quantity'])} units) but generates modest revenue. "
                    f"Feature as 'Staff Pick', highlight it at the point of sale, or run a 1-week promotion."
                ),
                "impact_dollars": None,
                "impact_label": "High potential",
                "n_transactions": int(prod_tx_counts.get(gem_row["product"], 0)),
                "priority": 3,
            })

    # ── 4. WoW momentum ───────────────────────────────────────────────────
    insights = _detect_overview_insights(df)
    wow = insights.get("wow_pct", 0)
    if wow > 10:
        quick_wins.append({
            "title": f"Your sales are up {wow:.0f}% this week — capitalize now",
            "detail": (
                f"Sales are up {wow:.1f}% compared to last week. Run a limited upsell on your top item "
                f"while customers are already engaged — don't let the surge pass unused."
            ),
            "impact_dollars": None,
            "impact_label": f"+{wow:.0f}% this week vs last",
            "n_transactions": len(df),
            "priority": 4,
        })
    elif wow < -10:
        watch_outs.append({
            "title": f"Sales dropped {abs(wow):.0f}% this week — act fast",
            "detail": (
                f"Sales are down {abs(wow):.1f}% compared to last week. A 3-day flash sale or 'bring a friend' deal "
                f"on your best seller can interrupt the slide. Act this week while it's recoverable."
            ),
            "impact_dollars": None,
            "impact_label": f"{wow:.0f}% this week vs last",
            "n_transactions": len(df),
            "priority": 1,
        })

    # ── 5. Declining products ─────────────────────────────────────────────
    # Only run when there's sufficient history for a 30-vs-30 comparison.
    # _find_declining_products already returns [] if span < 60 days, but we
    # capture the flag here so the render layer can show a "Need more history" notice.
    declining = _find_declining_products(df)
    for item in declining[:3]:
        at_risk_total = item["older_rev"] - item["recent_rev"]
        # Both windows are 30 days → at_risk_total IS the monthly decline rate
        at_risk_monthly = at_risk_total
        at_risk_low = at_risk_monthly * 0.75
        at_risk_high = at_risk_monthly * 1.25
        # Build seasonality note
        if item.get("seasonality") == "possibly_seasonal":
            seasonality_note = (
                f" Note: your overall business is also down {abs(item['overall_pct']):.0f}% — "
                f"this may be a seasonal dip. Monitor before making changes."
            )
        elif item.get("seasonality") == "structural":
            seasonality_note = (
                f" Your overall business is {'up' if item['overall_pct'] > 0 else 'flat'} "
                f"({item['overall_pct']:+.0f}%) — this looks like a problem specific to this item."
            )
        else:
            seasonality_note = ""
        watch_outs.append({
            "title": f"**{item['product']}** is losing revenue — investigate now",
            "detail": (
                f"Revenue dropped {item['decline_pct']:.0f}% "
                f"({cur}{item['older_rev']:,.0f} → {cur}{item['recent_rev']:,.0f}). "
                f"Bundle with a Star product, run a flash sale, or evaluate for removal."
                f"{seasonality_note}"
            ),
            "impact_dollars": round(at_risk_monthly, 2),
            "impact_low": round(at_risk_low, 2),
            "impact_high": round(at_risk_high, 2),
            "confidence": "directional",
            "impact_range": f"~{cur}{at_risk_monthly:,.0f}/month at risk if nothing changes",
            "impact_label": f"~{cur}{at_risk_monthly:,.0f}/month at risk",
            "n_transactions": int(prod_tx_counts.get(item["product"], 0)),
            "priority": 2,
        })

    # ── 6. Low Activity products ──────────────────────────────────────────
    if product_clusters is not None:
        dead = product_clusters[product_clusters["category"] == "Low Activity"].nlargest(3, "revenue")
        if not dead.empty:
            names = ", ".join(str(x) for x in dead["product"].tolist()[:3])
            prescription = _prescribe_low_activity(df, product_clusters)
            if prescription is not None:
                watch_outs.append(prescription)
            else:
                # Fallback to original generic card if prescription fails
                _dead_txns = sum(int(prod_tx_counts.get(p, 0)) for p in dead["product"].tolist()[:3])
                watch_outs.append({
                    "title": f"These items are barely selling: {names}",
                    "detail": (
                        "Low sales and low revenue. Before removing anything, check how "
                        "long each item has been in your offer — something new may just "
                        "need more time and visibility."
                    ),
                    "impact_dollars": None,
                    "impact_label": "Operational cost",
                    "n_transactions": _dead_txns,
                    "priority": 3,
                })

    # ── 7. Overall trend direction ────────────────────────────────────────
    trend = insights.get("trend", "flat")
    if trend == "downward":
        watch_outs.append({
            "title": "Revenue has been declining — time to review",
            "detail": (
                "Your overall sales trend is pointing downward. If this continues for 3+ weeks, it may mean "
                "competition, product fatigue, or a seasonal shift. Review your top products and check "
                "whether service quality has slipped during your busiest hours."
            ),
            "impact_dollars": None,
            "impact_label": "Trend risk",
            "n_transactions": len(df),
            "priority": 4,
        })

    # ── 8. Period-over-period comparison cards ────────────────────────────
    period_uploads = st.session_state.get("period_uploads", [])
    if len(period_uploads) >= 2:
        p_b = period_uploads[-1]
        p_a = period_uploads[-2]
        period_cmp = _compare_periods(p_a["df"], p_b["df"], p_a["label"], p_b["label"])
        if period_cmp is not None:
            rev_delta = period_cmp["revenue_delta_pct"]
            if rev_delta < -5:
                top_faller_name = (
                    period_cmp["top_fallers"][0]["product"]
                    if period_cmp["top_fallers"] else "your top items"
                )
                watch_outs.insert(0, {
                    "title": f"Revenue is down {abs(rev_delta):.0f}% vs {p_a['label']}",
                    "detail": (
                        f"Your sales this period are lower than last period. "
                        f"Check the Period Comparison above for which products are driving the drop. "
                        f"**{top_faller_name}** is showing the biggest decline."
                    ),
                    "impact_dollars": None,
                    "impact_label": "Period-over-period decline",
                    "confidence": "high",
                    "n_transactions": len(df),
                    "priority": 1,
                })
            elif rev_delta > 5:
                top_riser_name = (
                    period_cmp["top_risers"][0]["product"]
                    if period_cmp["top_risers"] else "your top items"
                )
                quick_wins.insert(0, {
                    "title": f"Revenue is up {rev_delta:.0f}% vs {p_a['label']} — keep the momentum",
                    "detail": (
                        f"Your sales are ahead of last period. "
                        f"**{top_riser_name}** is leading the growth — consider featuring it more, "
                        f"stocking up, or running a promotion to lock in the trend."
                    ),
                    "impact_dollars": None,
                    "impact_label": f"+{rev_delta:.0f}% vs {p_a['label']}",
                    "confidence": "high",
                    "n_transactions": len(df),
                    "priority": 1,
                })

    def _sort_key(a):
        return (-(float(a["impact_dollars"]) if a["impact_dollars"] is not None else 0.0), a["priority"])

    quick_wins.sort(key=_sort_key)
    watch_outs.sort(key=_sort_key)
    return {"quick_wins": quick_wins, "watch_outs": watch_outs}


def _compare_periods(df_a: pd.DataFrame, df_b: pd.DataFrame, label_a: str, label_b: str):
    """Compare two period DataFrames and return a structured diff dict.

    Returns None if either period has < 30 rows total.
    Each riser/faller dict: {"product": str, "delta_pct": float, "rev_b": float}
    """
    if len(df_a) < 30 or len(df_b) < 30:
        return None

    def _agg(df):
        return (
            df.groupby("product")
            .agg(revenue=("revenue", "sum"), transactions=("revenue", "count"))
            .reset_index()
        )

    agg_a = _agg(df_a)
    agg_b = _agg(df_b)

    rev_a = df_a["revenue"].sum()
    rev_b = df_b["revenue"].sum()
    orders_a = len(df_a)
    orders_b = len(df_b)
    aov_a = rev_a / orders_a if orders_a else 0.0
    aov_b = rev_b / orders_b if orders_b else 0.0

    def _safe_pct(a, b):
        return (b - a) / abs(a) * 100 if a != 0 else 0.0

    merged = pd.merge(
        agg_a[["product", "revenue", "transactions"]],
        agg_b[["product", "revenue", "transactions"]],
        on="product", how="outer", suffixes=("_a", "_b"),
    ).fillna(0)

    # Only compare products with sufficient transactions in BOTH periods
    both = merged[
        (merged["transactions_a"] >= _MIN_PRODUCT_TXN_FOR_PERIOD) &
        (merged["transactions_b"] >= _MIN_PRODUCT_TXN_FOR_PERIOD)
    ].copy()

    both["delta_pct"] = both.apply(
        lambda r: _safe_pct(r["revenue_a"], r["revenue_b"]), axis=1
    )

    def _to_item(r):
        return {"product": r["product"], "delta_pct": r["delta_pct"], "rev_b": r["revenue_b"]}

    top_risers  = both.nlargest(3, "delta_pct").apply(_to_item, axis=1).tolist()
    top_fallers = both.nsmallest(3, "delta_pct").apply(_to_item, axis=1).tolist()

    products_a = set(agg_a["product"].tolist())
    products_b = set(agg_b["product"].tolist())

    return {
        "revenue_delta_pct":  _safe_pct(rev_a, rev_b),
        "orders_delta_pct":   _safe_pct(orders_a, orders_b),
        "aov_delta_pct":      _safe_pct(aov_a, aov_b),
        "top_risers":         top_risers,
        "top_fallers":        top_fallers,
        "new_products":       sorted(products_b - products_a),
        "dropped_products":   sorted(products_a - products_b),
        "label_a":            label_a,
        "label_b":            label_b,
        "rev_a":              rev_a,
        "rev_b":              rev_b,
    }


def render_period_comparison(comparison: dict) -> None:
    """Render a compact diff card panel showing period-over-period changes."""
    if comparison is None:
        st.info(
            "Not enough data to compare — each period needs at least 30 rows. "
            "Try uploading a larger export."
        )
        return

    cur = _cur()
    label_a = comparison["label_a"]

    st.markdown(
        "<h3 style='margin-bottom:0.3rem;'>How do these periods compare?</h3>",
        unsafe_allow_html=True,
    )

    # ── Three metric chips ──────────────────────────────────────────────────
    def _delta_color(pct: float) -> str:
        return "off" if abs(pct) < 1 else "normal"

    rev_pct = comparison["revenue_delta_pct"]
    ord_pct = comparison["orders_delta_pct"]
    aov_pct = comparison["aov_delta_pct"]

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Revenue",
        f"{rev_pct:+.1f}% vs {label_a}",
        delta=f"{rev_pct:+.1f}%",
        delta_color=_delta_color(rev_pct),
    )
    c2.metric(
        "Orders",
        f"{ord_pct:+.1f}% vs {label_a}",
        delta=f"{ord_pct:+.1f}%",
        delta_color=_delta_color(ord_pct),
    )
    c3.metric(
        "Avg Order Value",
        f"{aov_pct:+.1f}% vs {label_a}",
        delta=f"{aov_pct:+.1f}%",
        delta_color=_delta_color(aov_pct),
    )

    # ── Risers and fallers ──────────────────────────────────────────────────
    left, right = st.columns(2)
    with left:
        st.markdown("**📈 Rising this period**")
        risers_shown = [r for r in comparison["top_risers"] if r["delta_pct"] > 0]
        if risers_shown:
            for item in risers_shown:
                st.markdown(
                    f"- {item['product']} +{item['delta_pct']:.0f}% "
                    f"({cur}{item['rev_b']:,.0f} this period)"
                )
        else:
            st.caption("Nothing rising significantly.")

    with right:
        st.markdown("**📉 Slipping this period**")
        fallers_shown = [r for r in comparison["top_fallers"] if r["delta_pct"] < 0]
        if fallers_shown:
            for item in fallers_shown:
                st.markdown(
                    f"- {item['product']} {item['delta_pct']:.0f}% "
                    f"({cur}{item['rev_b']:,.0f} this period)"
                )
        else:
            st.caption("Nothing slipping significantly.")

    # ── New / dropped product notes ─────────────────────────────────────────
    new_p     = comparison.get("new_products", [])
    dropped_p = comparison.get("dropped_products", [])
    if new_p:
        names = ", ".join(new_p[:5]) + (f" and {len(new_p) - 5} more" if len(new_p) > 5 else "")
        st.info(f"{len(new_p)} new item{'s' if len(new_p) > 1 else ''} this period: {names}")
    if dropped_p:
        names = ", ".join(dropped_p[:5]) + (f" and {len(dropped_p) - 5} more" if len(dropped_p) > 5 else "")
        st.info(f"{len(dropped_p)} item{'s' if len(dropped_p) > 1 else ''} not sold this period: {names}")


def render_action_center(df: pd.DataFrame, product_clusters):
    st.header("What should you focus on today?")
    st.caption("The most important things to act on, ranked by estimated impact on your revenue.")

    # Data freshness warning — only on Action Center
    if _has_dates(df):
        _most_recent = df["date"].max()
        _days_stale = (pd.Timestamp.now() - _most_recent).days
        if _days_stale > 60:
            _stale_date = _most_recent.strftime("%b %d, %Y")
            st.warning(f"Heads up — your most recent data is from {_stale_date}. Recommendations reflect conditions as of then.")

    _render_health_brief(df, product_clusters)

    cur = _cur()

    # ── Top-line metrics banner ────────────────────────────────────────────
    total_revenue   = df["revenue"].sum()
    total_orders    = len(df)
    avg_order       = total_revenue / total_orders if total_orders else 0
    insights = _detect_overview_insights(df)
    wow = insights.get("wow_pct")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue",   f"{cur}{total_revenue:,.2f}")
    m2.metric("Total Orders",    f"{total_orders:,}")
    m3.metric("Avg Order Value", f"{cur}{avg_order:.2f}")
    if wow is not None:
        wow_delta = f"{wow:+.1f}% vs prior week"
        m4.metric("Week-over-Week", f"{wow:+.1f}%", delta=wow_delta,
                  delta_color="normal" if wow >= 0 else "inverse")
    else:
        m4.metric("Unique Products", f"{df['product'].nunique()}")

    # ── Business profile nudge ─────────────────────────────────────────────
    if (
        not st.session_state.business_profile.get("profile_saved")
        and not st.session_state.get("demo_mode")
    ):
        st.info(
            "💡 **Set up your Business Profile** (sidebar → Business Profile) "
            "to get AI recommendations tailored to your industry and goals. "
            "Takes 30 seconds."
        )

    # ── Period Comparison ──────────────────────────────────────────────────
    period_uploads = st.session_state.get("period_uploads", [])
    if len(period_uploads) >= 2:
        period_labels = [p["label"] for p in period_uploads]
        sel_col_a, vs_col, sel_col_b, _run_col = st.columns([2, 0.3, 2, 1])
        with sel_col_a:
            idx_a = sel_col_a.selectbox("Compare:", period_labels,
                                        index=len(period_labels) - 2,
                                        key="period_sel_a")
        with vs_col:
            st.markdown("<div style='padding-top:1.9rem;text-align:center;font-weight:700;'>vs</div>",
                        unsafe_allow_html=True)
        with sel_col_b:
            idx_b = sel_col_b.selectbox("", period_labels,
                                        index=len(period_labels) - 1,
                                        label_visibility="hidden",
                                        key="period_sel_b")
        if idx_a == idx_b:
            st.info("Select two different periods to compare.")
        else:
            entry_a = next(p for p in period_uploads if p["label"] == idx_a)
            entry_b = next(p for p in period_uploads if p["label"] == idx_b)
            cmp = _compare_periods(entry_a["df"], entry_b["df"], idx_a, idx_b)
            render_period_comparison(cmp)
        st.markdown("---")

    # ── "Need more history" notice for decline detection ──────────────────
    if _has_dates(df) and _decline_history_insufficient(df):
        date_span = (df["date"].max() - df["date"].min()).days
        st.info(
            f"ℹ️ **Only {date_span} day(s) of data** — we need at least 60 days to detect which items are losing sales. "
            "Upload more history to unlock this."
        )

    st.markdown("---")

    # ── Gather and merge all actions into one ranked list ─────────────────
    center = _build_action_center(df, product_clusters)
    all_actions = center["quick_wins"] + center["watch_outs"]

    # Unified sort: by impact_dollars desc (None → 0), then priority asc
    all_actions.sort(key=lambda a: (
        -(float(a["impact_dollars"]) if a["impact_dollars"] is not None else 0.0),
        a.get("priority", 9)
    ))

    if not all_actions:
        st.info("Not enough data to generate recommendations. Upload a dataset with product names and revenue.")
        return

    # Confidence label map — translate internal tiers to plain-English labels
    _conf_display = {
        "high":         ("Strong signal",      "🟢"),
        "directional":  ("Worth testing",      "🟡"),
        "insufficient": ("Need more data",     "🔴"),
    }

    # ── Recommendation cards ───────────────────────────────────────────────
    for i, action in enumerate(all_actions, 1):
        is_risk = action in center["watch_outs"]
        col_main, col_badge = st.columns([5, 1])

        with col_main:
            card_body = f"**#{i} — {action['title']}**\n\n{action['detail']}"
            # Always show impact range — labelled clearly as estimate
            _impact_val = action.get("impact_dollars")
            if _impact_val is not None and _impact_val > 0 and action.get("impact_range"):
                card_body += f"\n\n*Estimate: {action['impact_range']}*"
            elif _impact_val is not None and _impact_val > 0 and action.get("impact_label"):
                card_body += f"\n\n*{action['impact_label']}*"
            else:
                pass
            if is_risk:
                st.warning(card_body)
            else:
                st.success(card_body)

        with col_badge:
            conf_key = action.get("confidence", "directional")
            conf_label, conf_emoji = _conf_display.get(conf_key, ("Worth testing", "🟡"))
            st.markdown(
                f"<div style='text-align:center;padding-top:0.8rem;'>"
                f"<div style='font-size:1.5rem;'>{conf_emoji}</div>"
                f"<div style='font-size:0.65rem;font-weight:700;text-transform:uppercase;"
                f"letter-spacing:0.12em;color:#2563eb;margin-top:0.3rem;'>{conf_label}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            n_tx = action.get("n_transactions")
            if n_tx is not None:
                st.caption(f"Based on {n_tx:,} transactions.")

    # ── Confidence legend ─────────────────────────────────────────────────
    st.caption(
        "🟢 **Strong signal** — backed by sufficient transaction data. "
        "🟡 **Worth testing** — data points this way, but not enough variation to be precise; run a short test before committing. "
        "🔴 **Need more data** — too few transactions to draw conclusions."
    )

    st.markdown("---")
    _render_ai_brief_expander(df, product_clusters, button_key="gen_brief_dashboard")

    if not _has_dates(df):
        st.info("Upload data with a date column to unlock trend and momentum signals.")

    render_monthly_report_section(df, product_clusters)

    # ── Anomaly history nudge ──────────────────────────────────────────────
    anom_log = st.session_state.get("anomaly_log", [])
    if (
        len(anom_log) >= 3
        and any(not e.get("note") for e in anom_log)
        and not st.session_state.get("anomaly_nudge_shown", False)
    ):
        unannotated = sum(1 for e in anom_log if not e.get("note"))
        st.info(
            f"📋 **{unannotated} unusual days in your history have no notes yet.** "
            "Adding a note takes 5 seconds — and builds a record you'll thank yourself for later. "
            "Open **Sales event log** in the sidebar."
        )
        st.session_state.anomaly_nudge_shown = True


def _build_data_context(df: pd.DataFrame, product_clusters) -> str:
    """Build a rich text summary of the data to feed to the AI as context."""
    lines = []
    sym = _cur()

    # Overview stats
    total_revenue = df["revenue"].sum()
    total_orders = len(df)
    avg_order = total_revenue / total_orders if total_orders else 0
    unique_products = df["product"].nunique()
    has_cost = "cost" in df.columns and df["cost"].notna().any()
    lines.append(f"BUSINESS OVERVIEW:")
    lines.append(f"- Total revenue: {sym}{total_revenue:,.2f}")
    lines.append(f"- Total orders/rows: {total_orders:,}")
    lines.append(f"- Average order value: {sym}{avg_order:.2f}")
    lines.append(f"- Unique products: {unique_products}")
    lines.append(f"- Cost data available: {'Yes' if has_cost else 'No (margin estimates only)'}")

    # Date range — critical for AI to give time-calibrated advice
    if _has_dates(df):
        date_min = df["date"].min().date()
        date_max = df["date"].max().date()
        span_days = (date_max - date_min).days
        span_months = round(span_days / 30, 1)
        lines.append(f"- Data period: {date_min} to {date_max} ({span_days} days / ~{span_months} months)")
        daily_avg = total_revenue / max(span_days, 1)
        lines.append(f"- Average daily revenue: {sym}{daily_avg:,.2f}")
    else:
        lines.append("- No date column available (snapshot data only)")

    # Location breakdown
    if "location" in df.columns and df["location"].nunique() > 1:
        by_loc = df.groupby("location")["revenue"].sum().sort_values(ascending=False)
        lines.append(f"\nREVENUE BY LOCATION:")
        for loc, rev in by_loc.items():
            lines.append(f"- {_sanitize_for_prompt(loc)}: {sym}{rev:,.2f}")

    # Top 10 products by revenue (include margin when cost data available)
    agg_dict = {"quantity": ("quantity", "sum"), "revenue": ("revenue", "sum")}
    if has_cost:
        agg_dict["cost"] = ("cost", "sum")
    top_products = (
        df.groupby("product")
        .agg(**agg_dict)
        .reset_index()
        .nlargest(10, "revenue")
    )
    top_products["avg_price"] = top_products["revenue"] / top_products["quantity"].clip(lower=1)
    if has_cost:
        top_products["gross_profit"] = top_products["revenue"] - top_products["cost"]
        top_products["margin_pct"] = top_products["gross_profit"] / top_products["revenue"].clip(lower=0.01)
    gross_margin_fallback = st.session_state.get("gross_margin_pct", 0.65)
    lines.append(f"\nTOP 10 PRODUCTS BY REVENUE:")
    for _, row in top_products.iterrows():
        prod = _sanitize_for_prompt(row["product"])
        if has_cost:
            lines.append(
                f"- {prod}: {sym}{row['revenue']:,.2f} revenue, {int(row['quantity'])} units, "
                f"avg price {sym}{row['avg_price']:.2f}, gross profit {sym}{row['gross_profit']:,.2f} "
                f"({row['margin_pct']:.0%} margin)"
            )
        else:
            est_profit = row["revenue"] * gross_margin_fallback
            lines.append(
                f"- {prod}: {sym}{row['revenue']:,.2f} revenue, {int(row['quantity'])} units, "
                f"avg price {sym}{row['avg_price']:.2f}, est. profit ~{sym}{est_profit:,.2f} "
                f"({gross_margin_fallback:.0%} est. margin)"
            )

    # Cluster breakdown
    if product_clusters is not None and len(product_clusters) >= 4:
        lines.append(f"\nPRODUCT CLUSTERS (K-Means):")
        for cat in ["Stars", "Cash Cows", "Hidden Gems", "Low Activity"]:
            group = product_clusters[product_clusters["category"] == cat].nlargest(5, "revenue")
            if not group.empty:
                names = ", ".join(_sanitize_for_prompt(p) for p in group["product"].astype(str))
                lines.append(f"- {cat}: {names}")

    # Peak hours (if date available)
    if _has_dates(df):
        df_time = df.copy()
        df_time["hour"] = df_time["date"].dt.hour
        df_time["day_of_week"] = df_time["date"].dt.day_name()
        by_hour = df_time.groupby("hour")["revenue"].sum()
        by_day = df_time.groupby("day_of_week")["revenue"].sum()
        if not by_hour.empty and not by_day.empty:
            peak_hour = by_hour.idxmax()
            peak_day = by_day.idxmax()
            lines.append(f"\nPEAK TRADING TIMES:")
            lines.append(f"- Busiest hour: {peak_hour}:00")
            lines.append(f"- Busiest day: {peak_day}")

    # Price range
    agg_price = df.groupby("product").agg(
        quantity=("quantity", "sum"), revenue=("revenue", "sum")
    ).reset_index()
    agg_price["avg_price"] = agg_price["revenue"] / agg_price["quantity"].clip(lower=1)
    lines.append(f"\nPRICING:")
    lines.append(f"- Lowest avg product price: {sym}{agg_price['avg_price'].min():.2f}")
    lines.append(f"- Highest avg product price: {sym}{agg_price['avg_price'].max():.2f}")
    lines.append(f"- Median avg product price: {sym}{agg_price['avg_price'].median():.2f}")

    # Week-over-week and trend momentum
    if _has_dates(df):
        insights = _detect_overview_insights(df)
        wow = insights.get("wow_pct")
        trend = insights.get("trend", "flat")
        slope_pct = insights.get("slope_pct", 0)
        lines.append(f"\nMOMENTUM:")
        lines.append(f"- Overall trend: {trend} ({slope_pct:+.2f}% per day avg)")
        if wow is not None:
            lines.append(f"- Week-over-week change: {wow:+.1f}%")

        # Rising stars
        rising = _find_rising_stars(df, n=5)
        if rising is not None and not rising.empty:
            lines.append(f"\nRISING PRODUCTS (last 30 days vs prior period):")
            for _, row in rising.iterrows():
                lines.append(
                    f"- {_sanitize_for_prompt(row['product'])}: +{row['growth_pct']:.0f}% revenue growth "
                    f"({sym}{row['recent_rev']:,.0f} recent)"
                )

        # Declining products
        declining = _find_declining_products(df)
        if declining:
            lines.append(f"\nDECLINING PRODUCTS:")
            for item in declining[:5]:
                lines.append(
                    f"- {_sanitize_for_prompt(item['product'])}: -{item['decline_pct']:.0f}% revenue "
                    f"({sym}{item['older_rev']:,.0f} → {sym}{item['recent_rev']:,.0f}), "
                    f"seasonality: {item['seasonality']}"
                )

    # Price recommendations
    price_recs = _get_price_recommendations(df)
    if price_recs:
        lines.append(f"\nPRICING OPPORTUNITIES:")
        for rec in price_recs[:6]:
            lines.append(
                f"- {_sanitize_for_prompt(rec['product'])}: {_sanitize_for_prompt(rec['action'])} "
                f"({sym}{rec['current']:.2f} → {sym}{rec['suggested']:.2f}). {_sanitize_for_prompt(rec['reason'])}"
            )

    # Association rules (market basket) — only if mlxtend is available and date exists
    if _MLXTEND_AVAILABLE and _has_dates(df):
        _, basket_rules, basket_err, _bm = _compute_basket_rules(df.to_csv(index=False))
        _is_proxy = _bm and "transaction ID" not in _bm
        if basket_rules is not None and not basket_rules.empty:
            if _is_proxy:
                lines.append(
                    "\nPRODUCT CO-OCCURRENCE (proxy only — day × location, NOT individual baskets):"
                )
                lines.append(
                    "  WARNING: No transaction/order ID in data. These pairs reflect products that"
                    " appear on the same busy days, not proven customer basket behaviour."
                    " Do NOT recommend bundles based on this data."
                )
            else:
                lines.append("\nTOP PRODUCT BUNDLES (market basket — order-level, reliable):")
            for _, rule in basket_rules.head(5).iterrows():
                lines.append(
                    f"- {_sanitize_for_prompt(rule['antecedent'])} → {_sanitize_for_prompt(rule['consequent'])} "
                    f"(lift {rule['lift']:.1f}×, confidence {rule['confidence']*100:.0f}%)"
                )

    return "\n".join(lines)


# =============================================================================
# MONTHLY SUMMARY REPORT — helpers and render function
# =============================================================================

def _safe_day_format(ts: "pd.Timestamp", fmt_with_day: str, fmt_fallback: str) -> str:
    """Format a timestamp, falling back on Windows where %-d is unsupported."""
    try:
        return ts.strftime(fmt_with_day)
    except ValueError:
        return ts.strftime(fmt_fallback).replace(" 0", " ")


def _derive_period_label(df: pd.DataFrame) -> str:
    """Derive a human-readable period label from df's date range."""
    if not _has_dates(df):
        return "Current Period"
    date_min = df["date"].min()
    date_max = df["date"].max()
    if date_min.year == date_max.year and date_min.month == date_max.month:
        return date_min.strftime("%B %Y")
    start_str = _safe_day_format(date_min, "%b %-d", "%b %d")
    if date_min.year == date_max.year:
        return f"{start_str} – {_safe_day_format(date_max, '%b %-d, %Y', '%b %d, %Y')}"
    return f"{start_str}, {date_min.year} – {_safe_day_format(date_max, '%b %-d, %Y', '%b %d, %Y')}"


def _format_report_for_export(report_text: str, business_name: str, period_label: str) -> str:
    """Assemble plain-text content for download and copy block."""
    name = business_name.strip() if business_name and business_name.strip() else "Business"
    paragraphs = [p.strip() for p in report_text.strip().split("\n\n") if p.strip()]
    lines = [
        f"{name} — Performance Summary",
        period_label,
        "Generated by Analytic",
        "",
    ]
    for para in paragraphs:
        lines.append(para)
        lines.append("")
    lines += [
        "---",
        "Analytic · analyticbi.com",
        "This report was generated automatically from your sales data.",
    ]
    return "\n".join(lines)


def _generate_narrative_report(df: pd.DataFrame, product_clusters, period_label: str | None = None) -> str | None:
    """Generate a 3-paragraph plain-English business performance summary via AI."""
    client = _get_groq_client()
    if client is None:
        return None
    if period_label is None:
        period_label = _derive_period_label(df)
    data_context = _build_data_context(df, product_clusters)
    profile_ctx = _build_profile_context()
    profile_block = f"\n\n{profile_ctx}\n" if profile_ctx else ""
    prompt = f"""You are writing a brief business performance summary for a small business owner. \
They will forward this to their accountant, business partner, or investor.

Write exactly 3 paragraphs. No headers, no bullet points, no markdown. \
Plain prose only. Each paragraph should be 3–5 sentences.

Paragraph 1 — Performance overview:
Summarize overall revenue, order volume, and trend direction for {period_label}. \
Mention the top-performing product by name and its revenue. \
If week-over-week or period-over-period data is available, include the direction.
Be specific with numbers. Do not use vague language.

Paragraph 2 — What's working and what needs attention:
Name the 1–2 strongest products and why they matter (volume, margin, or growth). \
Name 1 product that is underperforming or declining, if one exists.
If a pricing or bundle opportunity exists, mention it in one sentence.
Be specific. Use the actual product names and dollar figures from the data.

Paragraph 3 — Forward-looking action:
Give 2 concrete actions the owner should take in the next 30 days.
Each action should reference a specific product or time pattern from the data.
End with one sentence that frames the overall business health in plain English.
No filler. No "in conclusion." Just useful guidance.

Rules:
- Never use the words: "leverage", "synergy", "actionable", "insights", "data-driven", \
  "it's worth noting", "notably", "the data suggests", "it appears"
- Write like a trusted advisor who has run a business — direct, warm, specific
- If cost/margin data is available, mention profit, not just revenue
- Maximum 200 words total
{profile_block}
BUSINESS DATA:
{data_context}"""
    try:
        response = _groq_generate(client, prompt)
        return response.text.strip() if response and response.text else None
    except Exception:
        return None


def render_monthly_report_section(df: pd.DataFrame, product_clusters) -> None:
    """Render the Monthly Summary Report section inside Action Center."""
    st.markdown("---")
    st.markdown("#### Want a summary you can share?")
    st.caption("One-click summary you can forward to your accountant, partner, or investor.")

    if _get_groq_client() is None:
        st.info("Add your Groq API key in the sidebar to unlock report generation.")
        return

    if len(df) < 30:
        st.info("Upload at least 30 transactions to generate a meaningful report.")
        return

    period_label = _derive_period_label(df)

    _profile_biz_name = st.session_state.business_profile.get("business_name", "")
    st.text_input(
        "",
        value=_profile_biz_name if _profile_biz_name else "",
        key="report_business_name",
        placeholder="Your business name (optional — e.g. Brew & Bites)",
        label_visibility="collapsed",
    )

    if st.button("Generate Summary Report", key="gen_report_btn", type="primary"):
        with st.spinner("Writing your summary..."):
            result = _generate_narrative_report(df, product_clusters, period_label)
        if result is None:
            st.session_state["report_text"] = None
            st.warning("Could not generate report — check your AI API key in settings.")
        else:
            st.session_state["report_text"] = result
            st.session_state["report_generated_at"] = pd.Timestamp.now()

    report_text = st.session_state.get("report_text")
    if not report_text:
        return

    business_name = st.session_state.get("report_business_name", "")
    header_line = (
        f"{business_name.strip()} — {period_label}"
        if business_name and business_name.strip()
        else period_label
    )
    paragraphs_html = "".join(
        f"<p style='margin:0 0 1rem 0;'>{para}</p>"
        for para in report_text.strip().split("\n\n")
        if para.strip()
    )
    st.markdown(
        f"<div style='background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;"
        f"padding:2rem;margin-top:1rem;'>"
        f"<div style='font-weight:700;color:#1e3a5f;font-size:1.05rem;"
        f"margin-bottom:0.5rem;'>{header_line}</div>"
        f"<div style='font-size:0.7rem;color:#94a3b8;letter-spacing:0.1em;"
        f"text-transform:uppercase;margin-bottom:1.2rem;'>Generated by Analytic</div>"
        f"<div style='font-family:Raleway,sans-serif;font-size:0.95rem;line-height:1.85;"
        f"color:#1a202c;white-space:pre-wrap;'>{paragraphs_html}</div>"
        f"<div style='margin-top:1.5rem;font-size:0.65rem;color:#cbd5e1;"
        f"text-align:right;letter-spacing:0.15em;'>Analytic — analyticbi.com</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    export_text = _format_report_for_export(report_text, business_name, period_label)
    period_label_slug = (
        period_label.lower()
        .replace(" ", "_")
        .replace("–", "-")
        .replace(",", "")
        .replace(".", "")
    )
    file_name = f"analytic_report_{period_label_slug}.txt"

    col1, col2, col3 = st.columns([1.5, 1.5, 3])
    with col1:
        st.download_button(
            label="⬇ Download .txt",
            data=export_text,
            file_name=file_name,
            mime="text/plain",
            key="dl_report_txt",
        )
    with col2:
        if st.button("📋 Copy to clipboard", key="copy_report_btn"):
            st.session_state["show_copy_block"] = not st.session_state.get("show_copy_block", False)
    with col3:
        pass

    if st.session_state.get("show_copy_block", False):
        st.code(export_text, language=None)

    generated_at = st.session_state.get("report_generated_at")
    if generated_at is not None:
        st.caption(f"Generated {generated_at.strftime('%b %d, %Y at %I:%M %p')}")


# =============================================================================
# AI ADVISOR — Streaming chat about the business data
# =============================================================================

def _build_profile_context() -> str:
    """Return a compact profile block for AI prompt injection.

    Returns empty string if profile_saved is False or all fields are blank.
    Only includes lines where the value is non-empty and not '(not set)'.
    """
    profile = st.session_state.get("business_profile", {})
    if not profile.get("profile_saved"):
        return ""

    _skip = {"", "(not set)"}
    lines = []
    if profile.get("business_name", "") not in _skip:
        lines.append(f"- Name: {profile['business_name']}")
    if profile.get("industry", "") not in _skip:
        lines.append(f"- Industry: {profile['industry']}")
    if profile.get("business_size", "") not in _skip:
        lines.append(f"- Size: {profile['business_size']}")
    if profile.get("customer_type", "") not in _skip:
        lines.append(f"- Customers: {profile['customer_type']}")
    if profile.get("seasonality", "") not in _skip:
        lines.append(f"- Seasonality: {profile['seasonality']}")
    if profile.get("goals", "") not in _skip:
        lines.append(f"- Current goal: {profile['goals']}")

    if not lines:
        return ""

    return "BUSINESS PROFILE:\n" + "\n".join(lines)


def _detect_industry_from_data(df: pd.DataFrame) -> str:
    """Pure heuristic industry detection from product names. Requires >=2 keyword hits to avoid false positives."""
    try:
        products_lower = df["product"].str.lower().tolist()

        def _hits(keywords):
            return sum(1 for p in products_lower if any(kw in p for kw in keywords))

        if _hits(["espresso", "latte", "cappuccino", "americano", "flat white",
                   "cold brew", "macchiato", "cortado"]) >= 2:
            return "café"
        elif _hits(["burger", "pizza", "pasta", "entree", "entrée", "starter",
                    "main course", "side dish", "dessert", "appetizer"]) >= 2:
            return "restaurant"
        elif _hits(["croissant", "muffin", "loaf", "sourdough", "brioche",
                    "éclair", "tart", "scone"]) >= 2:
            return "bakery"
        elif _hits(["t-shirt", "jeans", "dress", "jacket", "sneakers",
                    "blouse", "hoodie", "cardigan"]) >= 2:
            return "clothing retail"
        elif _hits(["shampoo", "conditioner", "facial", "massage",
                    "manicure", "wax", "blowout"]) >= 2:
            return "beauty / salon"
        return ""
    except Exception:
        return ""


def _build_persona_system_prompt(industry: str) -> str:
    """Return an industry-specific persona instruction block for the system message."""
    if not industry:
        return ""

    mapping = {
        "café": (
            "This is a café or coffee shop. Use café-appropriate language: "
            "'covers' for customer visits, 'upsell' for add-ons, 'loyalty' for regulars. "
            "Benchmark average ticket at $6–9 for drink-only, $12–16 with food. "
            "Staffing advice should reference morning rush and afternoon lull patterns. "
            "Promotions should focus on loyalty schemes, daily specials, and seasonal drinks."
        ),
        "restaurant": (
            "This is a restaurant or bar. Use restaurant-appropriate language: "
            "'covers' for table turns, 'check average' for AOV, 'comp' for discounts. "
            "Benchmark check average at $18–30 casual, $40+ fine dining. "
            "Flag any items with food cost above 35% as margin risks. "
            "Staffing advice should reference service periods: breakfast, lunch, dinner."
        ),
        "bakery": (
            "This is a bakery or patisserie. "
            "Flag low-margin items (bread, simple pastries) vs high-margin (cakes, tarts). "
            "Waste is a key concern — declining items should be flagged as waste risk. "
            "Promotions should focus on end-of-day markdowns and pre-order bundles."
        ),
        "clothing retail": (
            "This is a clothing or accessories retail store. "
            "Use retail language: 'units sold', 'sell-through rate', 'markdown'. "
            "Slow-moving inventory carries carrying cost — flag items unsold for 60+ days. "
            "Promotions should focus on bundle offers and clearance events."
        ),
        "beauty / salon": (
            "This is a beauty salon or spa. "
            "Services are the primary product. Flag any service with high time cost vs revenue. "
            "Upsell language: 'add-on treatment', 'express service'. "
            "Staffing advice should reference appointment density and peak booking days."
        ),
    }

    return mapping.get(
        industry,
        f"This is a {industry} business. "
        "Tailor all advice to the specific dynamics and language of this industry.",
    )


def render_ai_advisor(df: pd.DataFrame, product_clusters=None):
    st.header("Ask Your Business Anything")
    st.caption("Chat with your data — ask about any product, trend, or decision")

    model = _get_groq_client()

    # Initialize chat history — keyed to the current dataset so switching
    # files or demo variants auto-clears stale conversation.
    _data_id = hashlib.md5(pd.util.hash_pandas_object(df.head(50)).values.tobytes()).hexdigest()[:10]
    if st.session_state.get("_chat_data_id") != _data_id:
        st.session_state.chat_messages = []
        st.session_state["_chat_data_id"] = _data_id
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Build system context from data
    clusters = product_clusters
    data_ctx = _build_data_context(df, clusters)

    # Step 1: check business profile
    profile = st.session_state.get("business_profile", {})
    profile_industry = profile.get("industry", "").lower().strip()

    # Step 2: check previously detected advisor persona
    persona = st.session_state.get("advisor_persona", {})
    detected_industry = persona.get("industry", "")

    # Step 3: attempt heuristic detection if neither is known
    if not profile_industry and not detected_industry:
        detected_industry = _detect_industry_from_data(df)
        if detected_industry:
            st.session_state.advisor_persona["industry"] = detected_industry
            st.session_state.advisor_persona["detected"] = True

    # Step 4: profile takes priority
    final_industry = profile_industry or detected_industry

    # Step 5: build persona block
    persona_block = _build_persona_system_prompt(final_industry) if final_industry else ""

    # Step 6: assemble system message
    profile_ctx = _build_profile_context()
    profile_block = f"\n\n{profile_ctx}" if profile_ctx else ""
    persona_section = f"\n\nINDUSTRY CONTEXT:\n{persona_block}" if persona_block else ""

    tpl = _INDUSTRY_TEMPLATES.get(
        st.session_state.get("industry_template", "(none)"),
        _INDUSTRY_TEMPLATES["(none)"]
    )
    tpl_hint = tpl.get("ai_hint", "")
    tpl_section = f"\n\nINDUSTRY TEMPLATE GUIDANCE:\n{tpl_hint}" if tpl_hint else ""

    system_message = (
        "You are a business advisor for a small business owner. "
        "You have access to their complete sales data and business profile below. "
        "Always tailor your advice to their specific industry, size, and goals. "
        "Reference actual product names and numbers from their data in every answer. "
        "Plain English only. No jargon. Keep answers concise and actionable."
        f"{persona_section}"
        f"{tpl_section}"
        f"{profile_block}\n\n"
        f"THEIR BUSINESS DATA:\n{data_ctx}"
    )

    # Suggested questions when chat is empty
    if not st.session_state.chat_messages:
        st.markdown("**Suggested questions to get started:**")
        for q in [
            "Which product should I promote this week?",
            "Where am I losing the most revenue?",
            "What's my most profitable product?",
            "When are my busiest hours and how should I staff?",
            "Which Low Activity products are worth keeping?",
        ]:
            st.markdown(f"- *{q}*")

        # Persona detection notice — shown only on first visit (chat empty)
        persona = st.session_state.get("advisor_persona", {})
        if persona.get("detected") and persona.get("industry"):
            st.caption(
                f"💡 I've identified this as a **{persona['industry']}** business "
                f"based on your products. My answers are tuned for your industry. "
                f"If that's wrong, update your Business Profile in the sidebar."
            )

        st.markdown("---")

    # Render existing chat history — show restored indicator if returning
    if st.session_state.chat_messages:
        n_msgs = len(st.session_state.chat_messages)
        st.caption(f"Conversation restored ({n_msgs} message{'s' if n_msgs != 1 else ''})")
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("badge"):
                st.caption(msg["badge"])

    # Silently skip if no API key — never show config instructions to a client
    if model is None:
        return

    # Chat input
    if user_input := st.chat_input("Ask anything about your business..."):
        # Add user message to history
        st.session_state.chat_messages.append({
            "role": "user", "content": user_input
        })
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build Groq conversation history
        # First message carries the system context — always included
        groq_history = [
            {"role": "user", "parts": [system_message]},
            {"role": "model", "parts": ["Understood. I have reviewed the business data and I am ready to answer questions about it."]},
        ]
        # Cap history to last 20 messages to stay within context window
        # (system context + data context already uses significant tokens)
        _recent_msgs = st.session_state.chat_messages[-20:]
        for msg in _recent_msgs[:-1]:
            role = "model" if msg["role"] == "assistant" else "user"
            groq_history.append({"role": role, "parts": [msg["content"]]})

        # Add current user message
        groq_history.append({"role": "user", "parts": [user_input]})

        # Generate response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            with st.spinner("Thinking..."):
                try:
                    response = _groq_generate(model, groq_history)
                    full_response = response.text or ""
                    response_placeholder.markdown(full_response)
                except Exception as e:
                    err = str(e)
                    if "429" in err:
                        st.warning("Rate limit reached — wait ~30 seconds and ask again.")
                    else:
                        st.error("AI Advisor is temporarily unavailable. Please try again in a moment.")
                        st.session_state["_last_ai_error"] = str(err)
                    full_response = ""
            badge = _build_data_confidence_badge(df)
            st.caption(badge)

        # Save assistant response to history
        st.session_state.chat_messages.append({
            "role": "assistant", "content": full_response, "badge": badge
        })

    # Clear chat button
    if st.session_state.chat_messages:
        if st.button("Clear conversation", key="clear_chat"):
            st.session_state.chat_messages = []
            st.rerun()

    if st.session_state.get("_last_ai_error") and st.secrets.get("DEBUG_MODE", False):
        st.caption(f"🔧 Debug: {st.session_state['_last_ai_error']}")


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    # ── Period uploads — init before any other session state reads ─────────
    if "period_uploads" not in st.session_state:
        st.session_state.period_uploads = []
        # Each entry: {"label": str, "df": pd.DataFrame, "uploaded_at": pd.Timestamp}
        # Max 6 entries. Oldest is dropped when limit is exceeded.

    # ── Anomaly history log — init before any other session state reads ────
    if "anomaly_log" not in st.session_state:
        st.session_state.anomaly_log = []
        # Each entry (dict):
        # {
        #   "id":           str,          # unique — md5(date + direction)[:8]
        #   "date":         str,          # "2025-02-14"
        #   "date_label":   str,          # "Feb 14, 2025"
        #   "direction":    str,          # "spike" | "dip"
        #   "revenue":      float,        # actual revenue on that day
        #   "z_score":      float,        # MAD z-score
        #   "pct_above":    float,        # how far above/below median as %
        #   "top_product":  str,          # top revenue product on that day (or "")
        #   "note":         str,          # user annotation, default ""
        #   "auto_label":   str,          # AI-suggested label
        #   "logged_at":    str,          # ISO timestamp of first detection
        #   "upload_label": str,          # period label if multi-period upload, else ""
        # }

    # ── Business profile — init before any other session state reads ───────
    if "business_profile" not in st.session_state:
        st.session_state.business_profile = {
            "business_name":    "",
            "industry":         "",
            "business_size":    "",
            "location_context": "",
            "seasonality":      "",
            "customer_type":    "",
            "goals":            "",
            "profile_saved":    False,
        }

    # ── Advisor persona — tracks auto-detected industry for AI tuning ──────
    if "advisor_persona" not in st.session_state:
        st.session_state.advisor_persona = {
            "industry":       "",   # e.g. "restaurant", "retail", "café", "bakery"
            "detected":       False,
            "detection_turn": -1,   # which turn number triggered detection
        }

    # ── Industry template ───────────────────────────────────────────────────
    if "industry_template" not in st.session_state:
        st.session_state.industry_template = "(none)"

    # ── Cluster history (insight changelog) ────────────────────────────────
    if "cluster_history" not in st.session_state:
        st.session_state.cluster_history = []

    st.title("ANALYTIC")
    st.markdown(
        "<p style='font-family:Raleway,sans-serif;font-size:0.8rem;font-weight:700;"
        "text-transform:uppercase;letter-spacing:0.35em;color:#2563eb;"
        "margin-top:-1rem;margin-bottom:2.5rem;'>"
        "Business Intelligence Platform — Est. 2026</p>",
        unsafe_allow_html=True,
    )

    # ── Settings (always visible) ──────────────────────────────────────────
    st.sidebar.markdown(
        "<p style='font-size:0.7rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.2em;color:#93c5fd;'>Settings</p>",
        unsafe_allow_html=True,
    )
    _cur_map = {"$ USD": "$", "€ EUR": "€", "£ GBP": "£", "¥ JPY": "¥", "₹ INR": "₹"}
    _cur_sel = st.sidebar.selectbox("Currency", list(_cur_map), key="cur_sel")
    st.session_state.currency_sym = _cur_map[_cur_sel]

    _country_map = {
        "US 🇺🇸": "US", "UK 🇬🇧": "GB", "Canada 🇨🇦": "CA",
        "Australia 🇦🇺": "AU", "India 🇮🇳": "IN", "None (no holidays)": None,
    }
    _ctry_sel = st.sidebar.selectbox("Holiday region (forecast)", list(_country_map), key="country_sel")
    st.session_state.country_code = _country_map[_ctry_sel]

    # ── Data source ────────────────────────────────────────────────────────
    st.sidebar.markdown(
        "<p style='font-size:0.7rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.2em;color:#93c5fd;margin-top:0.8rem;'>Your Data</p>",
        unsafe_allow_html=True,
    )

    # Demo data buttons
    _demo_col1, _demo_col2 = st.sidebar.columns(2)
    if _demo_col1.button("☕ Coffee Shop", use_container_width=True, help="6 months, 2 locations, 18 products"):
        st.session_state.demo_mode = True
        st.session_state.demo_variant = "coffee"
    if _demo_col2.button("🛍️ Retail Store", use_container_width=True, help="6 months, 1 location, 20 products"):
        st.session_state.demo_mode = True
        st.session_state.demo_variant = "retail"

    uploaded = st.sidebar.file_uploader(
        "Or upload your own CSV / Excel / TSV",
        type=["csv", "xlsx", "xls", "tsv", "txt"],
        help="Works with any small business POS export or sales dataset (CSV, Excel, TSV, tab-delimited)",
    )
    if uploaded:
        MAX_UPLOAD_MB = 50
        MAX_ROWS = 200_000
        if uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
            st.sidebar.error(f"This file is too large. Try exporting just the last 6–12 months of data, or splitting it into smaller files (under {MAX_UPLOAD_MB} MB).")
            uploaded = None
        else:
            st.session_state.demo_mode = False  # uploaded file takes priority

    # ── Resolve raw_df ─────────────────────────────────────────────────────
    demo_mode = st.session_state.get("demo_mode", False)

    if not uploaded and not demo_mode:
        # Landing page
        st.markdown("""
<div style='max-width:720px;margin-top:1.5rem;'>

<div style='background-color:#1e3a5f;border-radius:16px;padding:2.8rem;margin-bottom:2.5rem;'>
<p style='font-family:Cormorant,serif;font-size:2rem;font-weight:400;color:#f0f4f8;line-height:1.5;margin:0;letter-spacing:0.03em;'>
Your sales data already holds the answers.<br>
<span style='color:#93c5fd;font-style:italic;'>Most business owners never look.</span>
</p>
<p style='font-family:Raleway,sans-serif;font-size:1rem;font-weight:400;color:#e2e8f0;line-height:1.9;margin-top:1.3rem;'>
Analytic turns your existing transaction data into clear, actionable decisions —
what to sell more of, when to run promotions, what to cut from your offer, and where
your revenue is actually coming from. No guesswork. No spreadsheet diving. Just answers.
</p>
</div>

<p style='font-family:Raleway,sans-serif;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.25em;color:#2563eb;margin-bottom:1.2rem;'>What you'll see — clear answers, no clutter</p>

<div style='display:grid;grid-template-columns:1fr 1fr;gap:1rem;'>

<div style='background:#1e3a5f;border-radius:12px;padding:1.4rem;'>
<p style='font-family:Cormorant,serif;font-size:1.2rem;font-weight:500;color:#93c5fd;margin:0;'>🎯 Action Center</p>
<p style='font-family:Raleway,sans-serif;font-size:0.95rem;color:#f0f4f8;margin:0.5rem 0 0;line-height:1.6;'>Your daily to-do list — the most important things to act on today, ranked by impact on your revenue. Start here every day.</p>
</div>

<div style='background:#e2e8f0;border:1px solid #93c5fd;border-radius:12px;padding:1.4rem;'>
<p style='font-family:Cormorant,serif;font-size:1.2rem;font-weight:500;color:#1e3a5f;margin:0;'>📊 Business Overview</p>
<p style='font-family:Raleway,sans-serif;font-size:0.95rem;color:#1e3a5f;margin:0.5rem 0 0;line-height:1.6;'>Revenue totals, week-over-week trends, unusual sales days, and a side-by-side comparison of any two time periods.</p>
</div>

<div style='background:#e2e8f0;border:1px solid #93c5fd;border-radius:12px;padding:1.4rem;'>
<p style='font-family:Cormorant,serif;font-size:1.2rem;font-weight:500;color:#1e3a5f;margin:0;'>⭐ What's Selling</p>
<p style='font-family:Raleway,sans-serif;font-size:0.95rem;color:#1e3a5f;margin:0.5rem 0 0;line-height:1.6;'>Products sorted into Best Sellers, Steady Earners, Underrated Items, and Slow Movers — with rising and declining item alerts.</p>
</div>

<div style='background:#e2e8f0;border:1px solid #93c5fd;border-radius:12px;padding:1.4rem;'>
<p style='font-family:Cormorant,serif;font-size:1.2rem;font-weight:500;color:#1e3a5f;margin:0;'>💰 Pricing</p>
<p style='font-family:Raleway,sans-serif;font-size:0.95rem;color:#1e3a5f;margin:0.5rem 0 0;line-height:1.6;'>Find items you might be under-charging for — and a price simulator so you can test a change before committing.</p>
</div>

<div style='background:#e2e8f0;border:1px solid #93c5fd;border-radius:12px;padding:1.4rem;'>
<p style='font-family:Cormorant,serif;font-size:1.2rem;font-weight:500;color:#1e3a5f;margin:0;'>📈 Forecast</p>
<p style='font-family:Raleway,sans-serif;font-size:0.95rem;color:#1e3a5f;margin:0.5rem 0 0;line-height:1.6;'>Where is your revenue heading? See your trend projected forward and which products are driving it.</p>
</div>

<div style='background:#e2e8f0;border:1px solid #93c5fd;border-radius:12px;padding:1.4rem;'>
<p style='font-family:Cormorant,serif;font-size:1.2rem;font-weight:500;color:#1e3a5f;margin:0;'>🔗 What Sells Together</p>
<p style='font-family:Raleway,sans-serif;font-size:0.95rem;color:#1e3a5f;margin:0.5rem 0 0;line-height:1.6;'>Discover natural product pairings and bundle opportunities to lift your average order value.</p>
</div>

<div style='background:#2563eb;border-radius:12px;padding:1.4rem;'>
<p style='font-family:Cormorant,serif;font-size:1.2rem;font-weight:500;color:#f0f4f8;margin:0;'>🤖 AI Advisor</p>
<p style='font-family:Raleway,sans-serif;font-size:0.95rem;color:#e2e8f0;margin:0.5rem 0 0;line-height:1.6;'>Ask anything about your data. AI-powered — answers like a consultant who has read every row.</p>
</div>

</div>

<p style='font-family:Raleway,sans-serif;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.2em;color:#2563eb;margin-top:2rem;'>
👈 Click <strong>Coffee Shop</strong> or <strong>Retail Store</strong> demo, or upload your own file from the sidebar
</p>
</div>
        """, unsafe_allow_html=True)
        return

    if demo_mode and not uploaded:
        _variant = st.session_state.get("demo_variant", "coffee")
        if _variant == "retail":
            raw_df = _generate_retail_demo_df()
            st.sidebar.success("Demo: Main Street Retail — 6 months, 20 products")
        else:
            raw_df = _generate_demo_df()
            st.sidebar.success("Demo: Brew & Bites Coffee Shop — 6 months, 2 locations")
    else:
        raw_df = load_raw_file(uploaded)
        if raw_df is None:
            return
        if len(raw_df) > MAX_ROWS:
            st.error(
                f"This file has {len(raw_df):,} rows — Analytic works best with up to {MAX_ROWS:,}. "
                f"Try filtering your export to the most recent 6–12 months before uploading."
            )
            return
        # Clear stale column-mapping session keys whenever a new file is uploaded
        try:
            file_hash = hashlib.md5(uploaded.getvalue()).hexdigest()[:8]
        except Exception:
            file_hash = getattr(uploaded, "name", "")
        if st.session_state.get("_last_file_hash") != file_hash:
            for _k in ["map_product", "map_qty", "map_rev", "map_up", "map_cost", "map_date", "map_loc", "map_txn",
                       "chat_history", "chat_messages", "_chat_data_id", "data_context", "data_context_hash"]:
                st.session_state.pop(_k, None)
            st.session_state["_last_file_hash"] = file_hash

    # ── Column mapping ─────────────────────────────────────────────────────
    auto_mapping = _detect_columns(raw_df)

    st.sidebar.markdown(
        "<p style='font-size:0.7rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.2em;color:#93c5fd;margin-top:1rem;'>Column Mapping</p>",
        unsafe_allow_html=True,
    )
    cols = list(raw_df.columns)

    def _idx(opt_list, val):
        return opt_list.index(val) if val in opt_list else 0

    def _clean_mapping(m):
        return {k: (None if v in ("(none)", "(none—use 1)") else v) for k, v in m.items()}

    # Build detected-summary line
    _rev_label = auto_mapping.get("revenue") or auto_mapping.get("unit_price")
    _det_parts = [f"Product={auto_mapping['product']}" if auto_mapping.get("product") else "Product=?"]
    if _rev_label:
        _det_parts.append(f"Revenue={_rev_label}")
    else:
        _det_parts.append("Revenue=?")
    if auto_mapping.get("date"):
        _det_parts.append(f"Date={auto_mapping['date']}")
    if auto_mapping.get("location"):
        _det_parts.append(f"Location={auto_mapping['location']}")

    if demo_mode:
        st.sidebar.caption("Auto-configured for demo data")
    else:
        st.sidebar.caption("Detected: " + " · ".join(_det_parts))

    # ── Business Profile ───────────────────────────────────────────────────
    st.sidebar.markdown(
        "<p style='font-size:0.7rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.2em;color:#93c5fd;margin-top:0.8rem;'>Business Profile</p>",
        unsafe_allow_html=True,
    )
    _prof = st.session_state.business_profile
    if _prof["profile_saved"]:
        _summary_name     = _prof.get("business_name", "") or "Your business"
        _summary_industry = _prof.get("industry", "") or ""
        _summary_line = f"✓ {_summary_name}" + (f" · {_summary_industry}" if _summary_industry and _summary_industry != "(not set)" else "")
        st.sidebar.success(_summary_line)
        if st.sidebar.button("Edit profile", key="edit_profile_btn"):
            st.session_state.business_profile["profile_saved"] = False
            st.rerun()
    else:
        with st.sidebar.expander("⚙️ Business Profile", expanded=False):
            template_choice = st.selectbox(
                "Industry template",
                options=list(_INDUSTRY_TEMPLATES.keys()),
                index=list(_INDUSTRY_TEMPLATES.keys()).index(
                    st.session_state.get("industry_template", "(none)")
                ),
                key="template_sel",
                help="Pre-configures which insights surface first for your business type.",
            )
            st.session_state.industry_template = template_choice
            st.text_input(
                "Business name",
                value=_prof["business_name"],
                placeholder="e.g. Brew & Bites Coffee",
                key="prof_name",
            )
            st.selectbox(
                "Industry",
                options=[
                    "(not set)",
                    "Coffee shop / café",
                    "Restaurant / bar",
                    "Retail — food & grocery",
                    "Retail — clothing & accessories",
                    "Retail — general",
                    "Bakery / patisserie",
                    "Food truck / market stall",
                    "Beauty / salon / spa",
                    "Fitness / gym / studio",
                    "Service business",
                    "Other",
                ],
                key="prof_industry",
            )
            st.selectbox(
                "Size",
                options=[
                    "(not set)",
                    "Solo / owner-operated",
                    "2–5 staff",
                    "6–15 staff",
                    "16–50 staff",
                    "50+ staff",
                ],
                key="prof_size",
            )
            st.selectbox(
                "Customers are mainly",
                options=[
                    "(not set)",
                    "Walk-in / foot traffic",
                    "Regulars / repeat customers",
                    "Online / delivery",
                    "Mixed walk-in and regulars",
                    "Corporate / B2B",
                ],
                key="prof_customer",
            )
            st.text_input(
                "Seasonality (optional)",
                placeholder="e.g. Slow in Jan, busy in summer",
                value=_prof["seasonality"],
                key="prof_seasonality",
            )
            st.selectbox(
                "My main goal right now",
                options=[
                    "(not set)",
                    "Increase revenue",
                    "Improve profit margins",
                    "Reduce slow-moving stock",
                    "Grow average order value",
                    "Understand what's working",
                    "Prepare for a busy season",
                    "Cut costs",
                ],
                key="prof_goal",
            )
            if st.button("Save Profile", key="save_profile_btn", use_container_width=True):
                st.session_state.business_profile.update({
                    "business_name":   st.session_state.get("prof_name", ""),
                    "industry":        st.session_state.get("prof_industry", "(not set)"),
                    "business_size":   st.session_state.get("prof_size", "(not set)"),
                    "customer_type":   st.session_state.get("prof_customer", "(not set)"),
                    "seasonality":     st.session_state.get("prof_seasonality", ""),
                    "goals":           st.session_state.get("prof_goal", "(not set)"),
                    "profile_saved":   True,
                })
                st.sidebar.success("Profile saved ✓")
                st.rerun()

    _detection_incomplete = not auto_mapping.get("product") or (
        not auto_mapping.get("revenue") and not auto_mapping.get("unit_price")
    )
    with st.sidebar.expander("Override column mapping", expanded=_detection_incomplete):
        _override_raw = {
            "product":    st.selectbox("Product column", cols,
                              index=_idx(cols, auto_mapping["product"]), key="map_product"),
            "quantity":   st.selectbox("Quantity column", ["(none—use 1)"] + cols,
                              index=0 if not auto_mapping["quantity"] else _idx(cols, auto_mapping["quantity"]) + 1,
                              key="map_qty"),
            "revenue":    st.selectbox("Revenue/Total column", ["(none)"] + cols,
                              index=0 if not auto_mapping["revenue"] else _idx(cols, auto_mapping["revenue"]) + 1,
                              key="map_rev"),
            "unit_price": st.selectbox("Unit price (if no revenue)", ["(none)"] + cols,
                              index=0 if not auto_mapping["unit_price"] else _idx(cols, auto_mapping["unit_price"]) + 1,
                              key="map_up"),
            "cost":       st.selectbox("Cost / COGS column (optional)", ["(none)"] + cols,
                              index=0 if not auto_mapping.get("cost") else _idx(cols, auto_mapping["cost"]) + 1,
                              key="map_cost"),
            "date":       st.selectbox("Date/Time column", ["(none)"] + cols,
                              index=0 if not auto_mapping["date"] else _idx(cols, auto_mapping["date"]) + 1,
                              key="map_date"),
            "location":   st.selectbox("Location column", ["(none)"] + cols,
                              index=0 if not auto_mapping["location"] else _idx(cols, auto_mapping["location"]) + 1,
                              key="map_loc"),
            "transaction_id": st.selectbox("Order/Transaction ID column", ["(none)"] + cols,
                              index=0 if not auto_mapping.get("transaction_id") else _idx(cols, auto_mapping["transaction_id"]) + 1,
                              help="Used for Market Basket Analysis. Map your Order ID, Check #, or Transaction ID column for accurate co-purchase detection.",
                              key="map_txn"),
        }

    mapping_override = _clean_mapping(_override_raw)

    # ── Validation feedback ────────────────────────────────────────────────
    missing = []
    if not mapping_override.get("revenue") and not mapping_override.get("unit_price"):
        missing.append("⚠️ No revenue/price column — open Override above.")
    if not mapping_override.get("product"):
        missing.append("⚠️ No product column — open Override above.")
    if missing:
        for m in missing:
            st.sidebar.warning(m)

    # Gross margin fallback — used when no cost column is mapped
    if not mapping_override.get("cost"):
        st.sidebar.markdown(
            "<p style='font-size:0.68rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.15em;color:#93c5fd;margin-top:0.6rem;'>Margin (no cost column)</p>",
            unsafe_allow_html=True,
        )
        gross_margin_pct = st.sidebar.slider(
            "Estimated gross margin %",
            min_value=10, max_value=90, value=65, step=5,
            help="If your data has no cost column, set your typical gross margin here. "
                 "Used to convert revenue impact into profit impact.",
            key="gross_margin_slider",
        )
        st.session_state["gross_margin_pct"] = gross_margin_pct / 100.0
    else:
        st.session_state.pop("gross_margin_pct", None)  # use actual cost data instead

    _mapping_key = tuple(sorted((mapping_override or {}).items()))
    df = prepare_data(raw_df, mapping_override)
    if df is None:
        return

    # ── Build a timeline (multi-period uploader) ────────────────────────────
    st.sidebar.markdown(
        "<p style='font-size:0.7rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.2em;color:#93c5fd;margin-top:0.8rem;'>Timeline</p>",
        unsafe_allow_html=True,
    )
    with st.sidebar.expander("▼ Build a timeline (optional)"):
        # ── Zero-friction path: auto-split current file by calendar month ──
        if _has_dates(df):
            months_available = sorted(df["date"].dt.to_period("M").unique())
            if len(months_available) >= 2:
                if st.button("Split by month", key="split_by_month",
                             help="Auto-fill the timeline using your current file, one entry per calendar month"):
                    st.session_state.period_uploads = []  # reset before splitting
                    for period in months_available[-6:]:  # cap at 6 most-recent months
                        month_df = df[df["date"].dt.to_period("M") == period].copy()
                        lbl = period.strftime("%b %Y")
                        st.session_state.period_uploads.append({
                            "label": lbl,
                            "df": month_df,
                            "uploaded_at": pd.Timestamp.now(),
                        })
                    st.sidebar.success(f"Split into {len(st.session_state.period_uploads)} months.")
                st.caption("Or upload separate files below:")

        period_file = st.file_uploader(
            "Upload a period file (CSV / Excel / TSV)",
            type=["csv", "xlsx", "xls", "tsv", "txt"],
            key="period_upload_widget",
            accept_multiple_files=False,
        )
        period_label = st.text_input(
            "Label this period (e.g. March 2025)",
            key="period_label",
            placeholder=pd.Timestamp.now().strftime("%B %Y"),
        )
        if st.button("Add to timeline", key="add_period_btn"):
            if period_file is None:
                st.warning("Please upload a file first.")
            else:
                _lbl = (period_label or "").strip() or pd.Timestamp.now().strftime("%B %Y")
                _raw = load_raw_file(period_file)
                if _raw is not None:
                    _auto = _detect_columns(_raw)
                    if not _auto.get("product") or (
                        not _auto.get("revenue") and not _auto.get("unit_price")
                    ):
                        st.sidebar.error(
                            "Could not detect product/revenue columns in this file. "
                            "Check your column names."
                        )
                    else:
                        _p_df, _p_err = _prepare_data_impl(_raw, _auto)
                        if _p_df is None:
                            st.sidebar.error(
                                f"Could not process this file: {_p_err or 'unknown error'}"
                            )
                        else:
                            uploads = st.session_state.period_uploads
                            uploads.append({
                                "label": _lbl,
                                "df": _p_df,
                                "uploaded_at": pd.Timestamp.now(),
                            })
                            if len(uploads) > 6:
                                uploads.pop(0)  # drop oldest
                            st.sidebar.success(f"Added: {_lbl}")

        # ── Timeline list ───────────────────────────────────────────────────
        uploads = st.session_state.period_uploads
        if uploads:
            st.caption("Your timeline:")
            for i, entry in enumerate(uploads):
                row_a, row_b = st.columns([5, 1])
                row_a.markdown(f"✓ **{entry['label']}** — {len(entry['df']):,} rows")
                if row_b.button("✕", key=f"del_period_{i}",
                                help=f"Remove {entry['label']}"):
                    st.session_state.period_uploads.pop(i)
                    st.rerun()
        else:
            st.caption("No periods added yet.")

    # ── Date range filter ──────────────────────────────────────────────────
    if _has_dates(df):
        min_d = df["date"].min().date()
        max_d = df["date"].max().date()
        span_days = (max_d - min_d).days
        if span_days > 5 * 365:
            st.warning(
                f"Your data spans **{span_days // 365} years** ({min_d} → {max_d}). "
                "Forecasts and trend analysis work best with 1–3 years of data. "
                "Use the date filter below to focus on a recent period."
            )
        st.sidebar.markdown(
            "<p style='font-size:0.7rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.2em;color:#93c5fd;margin-top:1rem;'>Filters</p>",
            unsafe_allow_html=True,
        )
        date_range = st.sidebar.date_input(
            "Date range", value=(min_d, max_d),
            min_value=min_d, max_value=max_d, key="date_range",
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            d0, d1 = date_range
            df = df[(df["date"].dt.date >= d0) & (df["date"].dt.date <= d1)]
        if df.empty:
            st.sidebar.warning("No data in selected date range.")
            return

    # ── Location filter ────────────────────────────────────────────────────
    locations = sorted(df["location"].unique().tolist())
    if len(locations) > 1:
        loc_filter = st.sidebar.selectbox(
            "Location", ["All locations"] + locations, key="loc_filter",
        )
        if loc_filter != "All locations":
            df = df[df["location"] == loc_filter]
            if df.empty:
                st.warning("No data for the selected location and date range.")
                return

    st.sidebar.success(f"Loaded {len(df):,} rows · {df['product'].nunique()} products")

    # ── Auto-suggest industry template (runs once, never overwrites user choice) ──
    if not st.session_state.get("_industry_infer_done", False):
        st.session_state._industry_infer_done = True
        if st.session_state.get("industry_template", "(none)") == "(none)":
            _inferred = _infer_industry_template(df, raw_cols=list(raw_df.columns))
            if _inferred:
                st.session_state.industry_template = _inferred
                st.sidebar.info(
                    f"Industry detected: **{_inferred}** — change in Business Profile if needed."
                )

    # ── Navigation — conditionally show pages ────────────────────────────
    _date_span_days = (df["date"].max() - df["date"].min()).days if _has_dates(df) else 0
    _has_txn_col = (
        "transaction_id" in df.columns
        and df["transaction_id"].notna().any()
        and (df["transaction_id"].astype(str) != "None").any()
    )

    chapters = [
        ("Action Center",      render_action_center),
        ("Business Overview",  render_overview),
        ("What's Selling",     render_best_sellers),
        ("Pricing",            render_price_intelligence),
    ]
    if _date_span_days >= 14:
        chapters.append(("Forecast", render_growth_forecast))
    chapters.append(("What Sells Together", render_market_basket))
    chapters += [
        ("AI Advisor",         render_ai_advisor),
    ]

    choice = st.sidebar.radio("Navigate", [c[0] for c in chapters], index=0)

    # ── Anomaly History — collapsed sidebar link ───────────────────────────
    with st.sidebar.expander("Sales event log"):
        if st.button("Open sales event log", key="open_anomaly_log", use_container_width=True):
            st.session_state["_show_anomaly_history"] = True
        anom_count = len(st.session_state.get("anomaly_log", []))
        if anom_count > 0:
            st.caption(f"{anom_count} unusual day{'s' if anom_count != 1 else ''} logged")
        else:
            st.caption("No unusual days logged yet.")

    product_clusters = _get_product_clusters(df, mapping_key=_mapping_key)

    # ── Export ─────────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    export_df  = _build_export_df(df, product_clusters)
    csv_bytes  = export_df.to_csv(index=False).encode()
    st.sidebar.download_button(
        "📥 Download Insights CSV",
        data=csv_bytes,
        file_name="analytic_report.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if st.session_state.get("_show_anomaly_history"):
        st.session_state["_show_anomaly_history"] = False
        render_anomaly_history()
    else:
        for name, fn in chapters:
            if choice == name and fn is not None:
                if name in ("Action Center", "Pricing", "Business Overview", "What's Selling", "AI Advisor"):
                    fn(df, product_clusters)
                else:
                    fn(df)
                break


def render_anomaly_history() -> None:
    st.header("What happened on unusual days?")
    st.caption(
        "Unusual sales days detected across all your uploads. "
        "Add notes to build a record of what caused each one."
    )

    log = st.session_state.anomaly_log
    if not log:
        st.info(
            "No anomalies logged yet. Upload data with at least 14 days of history "
            "to start detecting unusual days."
        )
        return

    # ── Summary bar ────────────────────────────────────────────────────────
    total = len(log)
    spikes = sum(1 for e in log if e["direction"] == "spike")
    dips = total - spikes
    s1, s2, s3 = st.columns(3)
    s1.metric("Total anomalies logged", total)
    s2.metric("🔺 Spikes", spikes)
    s3.metric("🔻 Dips", dips)

    # ── Filter / sort row ──────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 2])
    type_filter = fc1.selectbox(
        "Type",
        ["All", "Spikes only", "Dips only"],
        key="anom_filter_type",
    )
    sort_by = fc2.selectbox(
        "Sort by",
        ["Most recent", "Largest spike", "Largest dip", "Annotated first"],
        key="anom_sort",
    )
    notes_filter = fc3.selectbox(
        "Show",
        ["All", "Annotated only", "Unannotated only"],
        key="anom_filter_notes",
    )
    _ = fc4  # spacer

    # ── Apply filters ──────────────────────────────────────────────────────
    filtered = list(log)
    if type_filter == "Spikes only":
        filtered = [e for e in filtered if e["direction"] == "spike"]
    elif type_filter == "Dips only":
        filtered = [e for e in filtered if e["direction"] == "dip"]
    if notes_filter == "Annotated only":
        filtered = [e for e in filtered if e.get("note", "")]
    elif notes_filter == "Unannotated only":
        filtered = [e for e in filtered if not e.get("note", "")]

    # ── Apply sort ─────────────────────────────────────────────────────────
    if sort_by == "Most recent":
        filtered.sort(key=lambda e: e["date"], reverse=True)
    elif sort_by == "Largest spike":
        filtered.sort(key=lambda e: e["z_score"] if e["direction"] == "spike" else -999, reverse=True)
    elif sort_by == "Largest dip":
        filtered.sort(key=lambda e: e["z_score"] if e["direction"] == "dip" else -999, reverse=True)
    elif sort_by == "Annotated first":
        filtered.sort(key=lambda e: (0 if e.get("note") else 1, e["date"]), reverse=False)

    # ── Download button ────────────────────────────────────────────────────
    st.download_button(
        "⬇ Export history (.csv)",
        data=_build_anomaly_csv(),
        file_name="analytic_anomaly_history.csv",
        mime="text/csv",
        key="dl_anomaly_csv",
    )

    cur = _cur()

    # ── Render cards ───────────────────────────────────────────────────────
    for entry in filtered:
        icon = "🔺" if entry["direction"] == "spike" else "🔻"
        z = entry["z_score"]
        if z > 3.5:
            z_color = "#dc2626"
        elif z > 2.5:
            z_color = "#d97706"
        else:
            z_color = "#2563eb"

        pct = entry["pct_above"]
        pct_str = f"{pct:+.0f}%"
        tp_str = f" · Top product: {entry['top_product']}" if entry["top_product"] else ""
        upload_html = (
            f"<div style='font-size:0.7rem;color:#94a3b8;'>From: {entry['upload_label']}</div>"
            if entry.get("upload_label") else ""
        )

        left_col, right_col = st.columns([4, 1])
        with left_col:
            st.markdown(
                f"<div style='font-size:1rem;font-weight:700;color:#1e3a5f;'>{icon} {entry['date_label']}</div>"
                f"<div style='font-size:0.85rem;font-style:italic;color:#2563eb;'>{entry['auto_label']}</div>"
                f"<div style='font-size:0.8rem;color:#64748b;'>"
                f"Revenue: {cur}{entry['revenue']:,.2f} · {pct_str} vs normal{tp_str}"
                f"</div>"
                f"{upload_html}",
                unsafe_allow_html=True,
            )
            st.text_input(
                label="",
                placeholder="Add a note (e.g. we ran a 20% off promo)",
                value=entry.get("note", ""),
                key=f"note_{entry['id']}",
                label_visibility="collapsed",
                on_change=_save_anomaly_note,
                args=(entry["id"], f"note_{entry['id']}"),
            )
        with right_col:
            _z_label = "Very unusual" if z > 3.5 else ("Unusual" if z > 2.5 else "Slightly unusual")
            st.markdown(
                f"<div style='text-align:center;padding-top:0.4rem;'>"
                f"<span style='font-weight:700;font-size:0.85rem;color:{z_color};'>{_z_label}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button("✕", key=f"del_{entry['id']}", help="Remove from history"):
                st.session_state.anomaly_log = [
                    e for e in st.session_state.anomaly_log if e["id"] != entry["id"]
                ]
                st.rerun()

        st.markdown("---")

    # ── Clear all ──────────────────────────────────────────────────────────
    if st.button("🗑 Clear all history", key="clear_anomaly_log"):
        if st.session_state.get("confirm_clear_anomalies"):
            st.session_state.anomaly_log = []
            st.session_state.confirm_clear_anomalies = False
            st.rerun()
        else:
            st.session_state.confirm_clear_anomalies = True
            st.warning("Click again to confirm — this cannot be undone.")


if __name__ == "__main__":
    main()
