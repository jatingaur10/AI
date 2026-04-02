"""
╔═══════════════════════════════════════════════════════════════╗
║       GOD MODE  —  COMPLETE PORTFOLIO DASHBOARD               ║
║       Bloomberg Terminal Aesthetic  |  Pure Python            ║
╠═══════════════════════════════════════════════════════════════╣
║  RUN:  streamlit run dashboard.py                             ║
║  INSTALL: pip install streamlit plotly pandas yfinance        ║
╚═══════════════════════════════════════════════════════════════╝
"""

import json
import math
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════
# 0.  PAGE CONFIG  —  must be first Streamlit call
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="GOD MODE — PORTFOLIO COMMAND CENTER",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
# 1.  GLOBAL STYLE  — Bloomberg Terminal × Amber
# ═══════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ── Google Font ─────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;700&family=Bebas+Neue&display=swap');

/* ── Root palette ────────────────────────────────────── */
:root {
    --bg-base:    #050608;
    --bg-card:    #0b0d11;
    --bg-panel:   #0f1117;
    --border:     #1c2030;
    --border-hi:  #2a3050;
    --amber:      #ffb300;
    --amber-dim:  #b37d00;
    --amber-glow: rgba(255,179,0,0.12);
    --green:      #00e676;
    --red:        #ff1744;
    --blue:       #40c4ff;
    --purple:     #ea80fc;
    --text-hi:    #f0f0f0;
    --text-mid:   #8a90a0;
    --text-low:   #3a4060;
    --font-data:  'IBM Plex Mono', monospace;
    --font-head:  'Bebas Neue', sans-serif;
}

/* ── Base ────────────────────────────────────────────── */
html, body, .stApp {
    background: var(--bg-base) !important;
    color: var(--text-hi) !important;
    font-family: var(--font-data) !important;
}

/* ── Scanline overlay ────────────────────────────────── */
.stApp::before {
    content: '';
    position: fixed; top:0; left:0; right:0; bottom:0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.08) 2px,
        rgba(0,0,0,0.08) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── Hide Streamlit chrome ───────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1rem 2rem !important; max-width: 100% !important; }

/* ── Sidebar ─────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-hi) !important; }

/* ── Metric card ─────────────────────────────────────── */
.gm-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-top: 2px solid var(--amber);
    border-radius: 4px;
    padding: 14px 18px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
    position: relative;
    overflow: hidden;
}
.gm-card::after {
    content: '';
    position: absolute; top:0; left:0; right:0; height:1px;
    background: linear-gradient(90deg, var(--amber), transparent);
    opacity: 0.6;
}
.gm-card:hover { border-color: var(--amber-dim); }

.gm-card-label {
    font-family: var(--font-data);
    font-size: 9px; font-weight: 500;
    letter-spacing: 2px; text-transform: uppercase;
    color: var(--text-mid); margin-bottom: 6px;
}
.gm-card-value {
    font-family: var(--font-head);
    font-size: 28px; line-height: 1;
    letter-spacing: 1px; color: var(--amber);
}
.gm-card-sub {
    font-family: var(--font-data);
    font-size: 10px; color: var(--text-mid);
    margin-top: 4px;
}
.green { color: var(--green) !important; }
.red   { color: var(--red)   !important; }
.blue  { color: var(--blue)  !important; }
.amber { color: var(--amber) !important; }

/* ── Section header ──────────────────────────────────── */
.gm-section-header {
    font-family: var(--font-head);
    font-size: 13px; letter-spacing: 4px;
    color: var(--amber); text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px; margin: 18px 0 12px;
    display: flex; align-items: center; gap: 10px;
}
.gm-section-header::before {
    content: ''; display: inline-block;
    width: 4px; height: 16px;
    background: var(--amber); border-radius: 2px;
}

/* ── Portfolio row ───────────────────────────────────── */
.port-row {
    display: grid;
    grid-template-columns: 160px 1fr 1fr 1fr 1fr 90px 70px;
    gap: 0;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    align-items: center;
    font-size: 12px;
    transition: background 0.15s;
}
.port-row:hover { background: var(--amber-glow); }
.port-row-head {
    font-size: 9px; letter-spacing: 2px;
    color: var(--text-low); text-transform: uppercase;
}

/* ── Grade badge ─────────────────────────────────────── */
.grade {
    display: inline-block;
    font-family: var(--font-head);
    font-size: 20px; width: 36px; height: 36px;
    line-height: 36px; text-align: center;
    border-radius: 4px; font-weight: 700;
}
.grade-A  { background: rgba(0,230,118,0.15); color: var(--green); border: 1px solid var(--green); }
.grade-B  { background: rgba(255,179,0,0.15); color: var(--amber); border: 1px solid var(--amber); }
.grade-C  { background: rgba(64,196,255,0.15); color: var(--blue);  border: 1px solid var(--blue); }
.grade-D  { background: rgba(255,23,68,0.15);  color: var(--red);   border: 1px solid var(--red); }

/* ── Signal pill ─────────────────────────────────────── */
.signal {
    display: inline-block;
    font-size: 9px; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase;
    padding: 3px 10px; border-radius: 20px;
}
.signal-buy  { background: rgba(0,230,118,0.2); color: var(--green); border: 1px solid var(--green); }
.signal-sell { background: rgba(255,23,68,0.2);  color: var(--red);   border: 1px solid var(--red); }
.signal-hold { background: rgba(138,144,160,0.2); color: var(--text-mid); border: 1px solid var(--border-hi); }

/* ── Recommendation card ─────────────────────────────── */
.rec-card {
    background: var(--bg-card);
    border-left: 3px solid var(--amber);
    padding: 10px 14px; margin: 6px 0;
    border-radius: 0 4px 4px 0;
    font-size: 12px; color: var(--text-hi);
    line-height: 1.6;
}

/* ── Terminal log ────────────────────────────────────── */
.terminal {
    background: #000;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 14px;
    font-family: var(--font-data);
    font-size: 11px;
    line-height: 1.8;
    max-height: 220px;
    overflow-y: auto;
    color: var(--amber);
}
.terminal-line-sys  { color: #ff9100; }
.terminal-line-ok   { color: var(--green); }
.terminal-line-warn { color: #ff5252; }
.terminal-line-info { color: var(--blue); }

/* ── Table override ──────────────────────────────────── */
.stDataFrame, .stDataFrame table {
    font-family: var(--font-data) !important;
    font-size: 11px !important;
    background: var(--bg-card) !important;
    color: var(--text-hi) !important;
}
.stDataFrame thead th {
    background: var(--bg-panel) !important;
    color: var(--amber) !important;
    font-size: 9px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid var(--border) !important;
}
.stDataFrame tbody tr:hover td {
    background: var(--amber-glow) !important;
}

/* ── Divider ─────────────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 8px 0 !important; }

/* ── Button ──────────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--amber) !important;
    color: var(--amber) !important;
    font-family: var(--font-head) !important;
    font-size: 13px !important;
    letter-spacing: 2px !important;
    border-radius: 3px !important;
    padding: 6px 18px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: var(--amber-glow) !important;
    border-color: var(--text-hi) !important;
    color: var(--text-hi) !important;
}

/* ── Selectbox / slider ──────────────────────────────── */
.stSelectbox > div > div, .stMultiSelect > div > div {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text-hi) !important;
    font-family: var(--font-data) !important;
    font-size: 12px !important;
}

/* ── Progress bar ────────────────────────────────────── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--amber-dim), var(--amber)) !important;
    border-radius: 2px !important;
}

/* ── Top banner ──────────────────────────────────────── */
.gm-topbar {
    display: flex; align-items: center;
    justify-content: space-between;
    background: var(--bg-card);
    border-bottom: 1px solid var(--border);
    padding: 10px 20px;
    margin: -16px -32px 16px;
}
.gm-topbar-logo {
    font-family: var(--font-head);
    font-size: 22px; letter-spacing: 4px;
    color: var(--amber);
}
.gm-topbar-sub {
    font-size: 10px; letter-spacing: 3px;
    color: var(--text-mid); text-transform: uppercase;
}
.gm-topbar-live {
    display: flex; align-items: center; gap: 8px;
    font-size: 11px; color: var(--green);
}
.live-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green);
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(0,230,118,0.6); }
    70%  { box-shadow: 0 0 0 8px rgba(0,230,118,0); }
    100% { box-shadow: 0 0 0 0 rgba(0,230,118,0); }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 2.  CONSTANTS & COLOURS
# ═══════════════════════════════════════════════════════════════

AMBER  = "#ffb300"
GREEN  = "#00e676"
RED    = "#ff1744"
BLUE   = "#40c4ff"
PURPLE = "#ea80fc"
BG     = "#050608"
BGCARD = "#0b0d11"

PLOT_LAYOUT = dict(
    paper_bgcolor=BGCARD,
    plot_bgcolor=BGCARD,
    font=dict(family="IBM Plex Mono, monospace", color="#8a90a0", size=10),
    margin=dict(l=8, r=8, t=8, b=8),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="#1c2030",
        font=dict(size=10),
    ),
    xaxis=dict(
        showgrid=True, gridcolor="#12151d", gridwidth=1,
        zeroline=False, showline=True, linecolor="#1c2030",
        tickfont=dict(size=9),
    ),
    yaxis=dict(
        showgrid=True, gridcolor="#12151d", gridwidth=1,
        zeroline=False, showline=True, linecolor="#1c2030",
        tickfont=dict(size=9),
    ),
)

LT_WATCHLIST = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS",
                 "HINDUNILVR.NS","ITC.NS","SBIN.NS","BAJFINANCE.NS",
                 "MARUTI.NS","WIPRO.NS"]
ST_WATCHLIST = ["TATASTEEL.NS","AXISBANK.NS","SUNPHARMA.NS","HCLTECH.NS",
                "ULTRACEMCO.NS","NESTLEIND.NS","POWERGRID.NS","NTPC.NS"]
ALL_SYMBOLS  = list(set(LT_WATCHLIST + ST_WATCHLIST + ["RELIANCE.NS"]))

# ═══════════════════════════════════════════════════════════════
# 3.  DATA LAYER  — reads backend JSON + CSVs, falls back to sim
# ═══════════════════════════════════════════════════════════════

LOG_DIR = Path("logs")

@st.cache_data(ttl=10)
def load_ai_report() -> dict:
    """Read the JSON report written by god_mode_complete.py."""
    path = LOG_DIR / "ai_portfolio_report.json"
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return _mock_report()


def _mock_report() -> dict:
    """Generate a realistic mock report when backend is not running."""
    now    = datetime.now()
    total  = 1_000_000
    lt_eq  = total * 0.60 + random.uniform(-5000, 8000)
    st_eq  = total * 0.25 + random.uniform(-3000, 4000)
    tr_eq  = total * 0.15 + random.uniform(-2000, 3000)

    def port(name, eq, base, trades, wr, pf, sh, dd, grade, w):
        return {
            "cash": round(eq, 2), "equity": round(eq, 2),
            "total_pnl": round(eq - base, 2),
            "return_pct": round((eq - base) / base, 4),
            "trades": trades, "win_rate": wr, "profit_factor": pf,
            "sharpe": sh, "max_drawdown": dd, "grade": grade,
            "weight": w,
            "open_positions": {
                s: random.randint(10, 50)
                for s in random.sample(LT_WATCHLIST if "LONG" in name else ST_WATCHLIST, 3)
            },
        }

    return {
        "report_id":    random.randint(1, 200),
        "timestamp":    now.isoformat(),
        "consolidated": {
            "total_capital": total,
            "total_equity":  round(lt_eq + st_eq + tr_eq, 2),
            "total_pnl":     round(lt_eq + st_eq + tr_eq - total, 2),
            "return_pct":    round((lt_eq + st_eq + tr_eq - total) / total, 4),
            "total_trades":  random.randint(20, 120),
            "win_rate":      round(random.uniform(0.45, 0.70), 4),
            "profit_factor": round(random.uniform(1.2, 2.5), 4),
            "sharpe":        round(random.uniform(0.6, 2.2), 4),
        },
        "portfolios": {
            "LONG_TERM":  port("LONG",  lt_eq, total*0.60, random.randint(5,30),  0.64, 1.9, 1.4, 0.042, "A",  0.60),
            "SHORT_TERM": port("SHORT", st_eq, total*0.25, random.randint(8,40),  0.57, 1.5, 1.1, 0.065, "B+", 0.25),
            "TRADING":    port("TRADE", tr_eq, total*0.15, random.randint(12,80), 0.51, 1.2, 0.8, 0.091, "B",  0.15),
        },
        "rebalances": random.randint(0, 5),
        "alerts": [
            "[15:42:01] LONG_TERM: INFY.NS score 7.2 → BUY signal",
            "[15:41:33] TRADING: MACD bullish cross on RELIANCE.NS",
            "[15:40:55] REBALANCER: All portfolios within drift tolerance",
            "[15:39:12] SHORT_TERM: AXISBANK.NS RSI oversold (28.4)",
            "[15:38:44] AI TRACKER: Portfolio grade A — no action needed",
        ],
        "recommendations": [
            "✅ LONG_TERM: Win rate 64% above target — consider expanding position sizing",
            "📊 SHORT_TERM: Slight over-weight at 26.8% (target 25%) — monitor drift",
            "⚠️  TRADING: Max drawdown approaching 10% threshold — tighten DNA stop_loss_mult",
            "🌟 SYSTEM: Consolidated Sharpe 1.38 — portfolio performing well overall",
        ],
    }


@st.cache_data(ttl=60)
def load_trade_history() -> pd.DataFrame:
    """Load all trade CSVs from the logs directory."""
    frames = []
    for csv_path in LOG_DIR.glob("*.csv"):
        try:
            df = pd.read_csv(csv_path)
            frames.append(df)
        except Exception:
            pass
    if frames:
        return pd.concat(frames, ignore_index=True).sort_values("timestamp", ascending=False)
    # Fallback mock
    return _mock_trades()


def _mock_trades() -> pd.DataFrame:
    symbols = LT_WATCHLIST + ST_WATCHLIST
    rows = []
    base_time = datetime.now() - timedelta(hours=8)
    for i in range(40):
        sym  = random.choice(symbols)
        side = "BUY" if i % 3 != 0 else "SELL"
        px   = round(random.uniform(500, 4000), 2)
        qty  = random.randint(5, 100)
        pnl  = round(random.uniform(-800, 1500), 2) if side == "SELL" else 0
        port = random.choice(["long_term", "short_term", "trading"])
        rows.append({
            "timestamp": (base_time + timedelta(minutes=i*12)).strftime("%Y-%m-%dT%H:%M:%S"),
            "portfolio": port,
            "symbol": sym, "side": side,
            "qty": qty, "price": px, "pnl": pnl,
            "cash_after": round(random.uniform(100000, 900000), 2),
            "votes": random.randint(-6, 8),
            "notes": random.choice(["RSI_OS", "MACD↑", "STOP_HIT", "Score=7.2", "MOM↑"]),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def fetch_price_history(symbol: str, period: str = "1d", interval: str = "1m") -> pd.DataFrame:
    """Fetch OHLCV from yfinance with simulation fallback."""
    if YFINANCE_AVAILABLE:
        try:
            df = yf.Ticker(symbol).history(period=period, interval=interval)
            if not df.empty:
                return df[["Open","High","Low","Close","Volume"]].dropna()
        except Exception:
            pass
    return _sim_ohlcv(symbol, 200)


def _sim_ohlcv(symbol: str, n: int = 200) -> pd.DataFrame:
    seed = sum(ord(c) for c in symbol)
    rng  = np.random.default_rng(seed + int(time.time() // 60))
    base = 1000 + (seed % 3000)
    log_r = (0.00005 - 0.5 * 0.0015**2) + 0.0015 * rng.standard_normal(n)
    closes = base * np.exp(np.cumsum(log_r))
    opens  = closes * (1 + rng.uniform(-0.003, 0.003, n))
    highs  = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0, 0.001, n)))
    lows   = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0, 0.001, n)))
    vols   = rng.integers(50_000, 800_000, n).astype(float)
    idx    = pd.date_range(end=datetime.now(), periods=n, freq="1min")
    return pd.DataFrame({"Open": opens,"High": highs,"Low": lows,
                         "Close": closes,"Volume": vols}, index=idx)


def simulate_equity_curve(initial: float, n: int = 120) -> pd.Series:
    rng    = np.random.default_rng(int(initial) % 9999)
    daily  = rng.normal(0.0008, 0.008, n)
    curve  = initial * np.exp(np.cumsum(daily))
    idx    = pd.date_range(end=datetime.now(), periods=n, freq="1h")
    return pd.Series(curve, index=idx)


# ═══════════════════════════════════════════════════════════════
# 4.  CHART BUILDERS
# ═══════════════════════════════════════════════════════════════

def candlestick_chart(df: pd.DataFrame, symbol: str, height: int = 360) -> go.Figure:
    fig = make_subplots(rows=2, cols=1, row_heights=[0.78, 0.22],
                        vertical_spacing=0.02, shared_xaxes=True)

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name=symbol,
        increasing_line_color=GREEN,  increasing_fillcolor="rgba(0,230,118,0.15)",
        decreasing_line_color=RED,    decreasing_fillcolor="rgba(255,23,68,0.15)",
        line=dict(width=1),
    ), row=1, col=1)

    # 20-period EMA overlay
    ema20 = df["Close"].ewm(span=20).mean()
    fig.add_trace(go.Scatter(
        x=df.index, y=ema20, name="EMA20",
        line=dict(color=AMBER, width=1, dash="dot"), mode="lines",
    ), row=1, col=1)

    # 50-period EMA overlay
    ema50 = df["Close"].ewm(span=50).mean()
    fig.add_trace(go.Scatter(
        x=df.index, y=ema50, name="EMA50",
        line=dict(color=BLUE, width=1, dash="dot"), mode="lines",
    ), row=1, col=1)

    # Bollinger Bands
    sma   = df["Close"].rolling(20).mean()
    std   = df["Close"].rolling(20).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color=PURPLE, width=0.8, dash="dot"),
                             name="BB Upper", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color=PURPLE, width=0.8, dash="dot"),
                             fill="tonexty", fillcolor="rgba(234,128,252,0.03)",
                             name="BB Lower", showlegend=False), row=1, col=1)

    # Volume bars
    colors = [GREEN if c >= o else RED
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        marker_color=colors, marker_opacity=0.6,
        name="Volume", showlegend=False,
    ), row=2, col=1)

    # Layout
    layout = dict(**PLOT_LAYOUT)
    layout.update(dict(
        height=height,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        title=dict(text=f"  {symbol}", font=dict(size=12, color=AMBER,
                   family="IBM Plex Mono"), x=0.01, y=0.98),
    ))
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=True, gridcolor="#12151d", row=1)
    fig.update_yaxes(tickformat=",.0f", row=1)
    return fig


def equity_curve_chart(
        series_dict: dict,            # {"LONG": pd.Series, ...}
        height: int = 280) -> go.Figure:
    fig    = go.Figure()
    colors = {"LONG_TERM": AMBER, "SHORT_TERM": GREEN, "TRADING": BLUE}

    for name, series in series_dict.items():
        col = colors.get(name, AMBER)
        fig.add_trace(go.Scatter(
            x=series.index, y=series.values,
            name=name,
            mode="lines",
            line=dict(color=col, width=1.5),
            fill="tozeroy",
            fillcolor=col.replace("#", "rgba(").replace(")", ",0.04)") if col.startswith("#") else f"rgba(255,179,0,0.04)",
        ))

    layout = dict(**PLOT_LAYOUT)
    layout.update(height=height, title=dict(
        text="  PORTFOLIO EQUITY CURVES",
        font=dict(size=11, color=AMBER, family="IBM Plex Mono"), x=0.01, y=0.97))
    fig.update_layout(**layout)
    fig.update_yaxes(tickformat="₹,.0f")
    return fig


def donut_chart(weights: dict, values: dict) -> go.Figure:
    labels = list(weights.keys())
    vals   = [values.get(k, 0) for k in labels]
    colors = [AMBER, GREEN, BLUE]

    fig = go.Figure(go.Pie(
        labels=labels, values=vals,
        hole=0.68,
        marker=dict(colors=colors, line=dict(color=BGCARD, width=3)),
        textfont=dict(family="IBM Plex Mono", size=10),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    total = sum(vals)
    fig.add_annotation(
        text=f"₹{total/1e5:.1f}L",
        font=dict(size=18, color=AMBER, family="Bebas Neue"),
        showarrow=False,
    )
    layout = dict(**PLOT_LAYOUT)
    layout.update(height=240, showlegend=True,
                  legend=dict(orientation="h", y=-0.15, x=0.1, font=dict(size=9)))
    layout.pop("xaxis", None); layout.pop("yaxis", None)
    fig.update_layout(**layout)
    return fig


def score_bar_chart(scores: dict) -> go.Figure:
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    symbols = [s.replace(".NS", "") for s, _ in sorted_items]
    vals    = [v for _, v in sorted_items]
    bar_col = [GREEN if v >= 6 else (AMBER if v >= 4 else RED) for v in vals]

    fig = go.Figure(go.Bar(
        y=symbols, x=vals,
        orientation="h",
        marker_color=bar_col,
        marker_opacity=0.85,
        text=[f"{v:.1f}" for v in vals],
        textfont=dict(size=10, color="#f0f0f0"),
        textposition="inside",
    ))
    fig.add_vline(x=6, line_color=GREEN, line_dash="dot", line_width=1, opacity=0.5)
    fig.add_vline(x=4, line_color=AMBER, line_dash="dot", line_width=1, opacity=0.5)
    layout = dict(**PLOT_LAYOUT)
    layout.update(height=320,
                  title=dict(text="  STOCK SCORES", font=dict(size=11, color=AMBER), x=0.01),
                  xaxis=dict(range=[0, 10], **PLOT_LAYOUT["xaxis"]))
    fig.update_layout(**layout)
    return fig


def pnl_histogram(pnl_list: list) -> go.Figure:
    arr  = np.array(pnl_list) if pnl_list else np.random.normal(200, 400, 50)
    bins = np.linspace(arr.min(), arr.max(), 25)
    pos  = arr[arr >= 0]
    neg  = arr[arr < 0]

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=pos, xbins=dict(start=0, size=(arr.max()/12)+1),
                               marker_color=GREEN, opacity=0.7, name="Win"))
    fig.add_trace(go.Histogram(x=neg, xbins=dict(end=0, size=abs(arr.min()/12)+1),
                               marker_color=RED, opacity=0.7, name="Loss"))
    layout = dict(**PLOT_LAYOUT)
    layout.update(height=220, barmode="overlay",
                  title=dict(text="  PnL DISTRIBUTION", font=dict(size=11, color=AMBER), x=0.01))
    fig.update_layout(**layout)
    fig.update_xaxes(tickformat="₹,.0f")
    return fig


def rsi_gauge(value: float) -> go.Figure:
    color = RED if value > 70 else (GREEN if value < 30 else AMBER)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(font=dict(size=28, color=color, family="Bebas Neue")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#3a4060", tickfont=dict(size=9)),
            bar=dict(color=color, thickness=0.3),
            bgcolor=BGCARD,
            bordercolor="#1c2030",
            steps=[
                dict(range=[0, 30], color="rgba(0,230,118,0.10)"),
                dict(range=[30, 70], color="rgba(255,179,0,0.07)"),
                dict(range=[70, 100], color="rgba(255,23,68,0.10)"),
            ],
            threshold=dict(line=dict(color=color, width=2), thickness=0.8, value=value),
        ),
    ))
    fig.update_layout(**{**PLOT_LAYOUT, "height": 180,
                         "margin": dict(l=16, r=16, t=24, b=8)})
    return fig


# ═══════════════════════════════════════════════════════════════
# 5.  SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════

if "price_history" not in st.session_state:
    st.session_state.price_history = {}
if "last_prices"   not in st.session_state:
    st.session_state.last_prices = {}
if "tick"          not in st.session_state:
    st.session_state.tick = 0
if "engine_on"     not in st.session_state:
    st.session_state.engine_on = True
if "selected_sym"  not in st.session_state:
    st.session_state.selected_sym = "RELIANCE.NS"

# ═══════════════════════════════════════════════════════════════
# 6.  SIDEBAR
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style='font-family:"Bebas Neue",sans-serif;font-size:22px;
                letter-spacing:4px;color:#ffb300;padding:8px 0 4px'>
    ⚡ GOD MODE
    </div>
    <div style='font-size:9px;letter-spacing:3px;color:#3a4060;
                text-transform:uppercase;margin-bottom:16px'>
    Portfolio Command Center
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**NAVIGATION**")
    page = st.radio("", ["🏠 Overview", "📈 Live Charts",
                          "💼 Portfolios", "🔬 Signal Lab",
                          "📋 Trade History", "🤖 AI Tracker"],
                    label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**SYMBOL**")
    selected_sym = st.selectbox("", ALL_SYMBOLS, label_visibility="collapsed",
                                 index=ALL_SYMBOLS.index("RELIANCE.NS")
                                 if "RELIANCE.NS" in ALL_SYMBOLS else 0)
    st.session_state.selected_sym = selected_sym

    st.markdown("**TIMEFRAME**")
    tf = st.selectbox("", ["1m", "5m", "15m", "1h", "1d"],
                      label_visibility="collapsed")

    st.markdown("**CHART TYPE**")
    chart_type = st.radio("", ["Candle", "Line", "Area"],
                          label_visibility="collapsed", horizontal=True)

    st.markdown("---")
    st.markdown("**ENGINE**")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("▶ START"): st.session_state.engine_on = True
    with col_b:
        if st.button("■ STOP"):  st.session_state.engine_on = False

    refresh = st.slider("Refresh (s)", 1, 30, 3)

    st.markdown("---")
    st.markdown(f"""
    <div style='font-size:9px;color:#3a4060;letter-spacing:1px;line-height:2'>
    ENGINE: {'🟢 RUNNING' if st.session_state.engine_on else '🔴 STOPPED'}<br>
    TICK: {st.session_state.tick:,}<br>
    BACKEND: {'LIVE' if (LOG_DIR / 'ai_portfolio_report.json').exists() else 'SIMULATED'}<br>
    {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 7.  LOAD DATA
# ═══════════════════════════════════════════════════════════════

report = load_ai_report()
trades = load_trade_history()
cons   = report.get("consolidated", {})
ports  = report.get("portfolios", {})

# ═══════════════════════════════════════════════════════════════
# 8.  TOP BANNER
# ═══════════════════════════════════════════════════════════════

st.markdown(f"""
<div class='gm-topbar'>
  <div>
    <div class='gm-topbar-logo'>⚡ GOD MODE PORTFOLIO SYSTEM</div>
    <div class='gm-topbar-sub'>NSE India &nbsp;|&nbsp; Paper Trading &nbsp;|&nbsp; 3-Portfolio Engine</div>
  </div>
  <div style='text-align:center'>
    <div style='font-family:"Bebas Neue";font-size:32px;color:#ffb300;letter-spacing:2px'>
      ₹{cons.get("total_equity", 1_000_000):,.0f}
    </div>
    <div style='font-size:9px;letter-spacing:3px;color:#8a90a0'>TOTAL EQUITY</div>
  </div>
  <div class='gm-topbar-live'>
    <div class='live-dot'></div>
    LIVE &nbsp;|&nbsp; Report #{report.get("report_id",0)} &nbsp;|&nbsp;
    {datetime.now().strftime('%H:%M:%S')}
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 9.  PAGES
# ═══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
# PAGE A  ——  OVERVIEW
# ─────────────────────────────────────────────────────────────
if page == "🏠 Overview":

    # Row 1 — 7 KPI cards
    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    total_pnl = cons.get("total_pnl", 0)
    ret_pct   = cons.get("return_pct", 0)
    pnl_col   = "green" if total_pnl >= 0 else "red"

    cards = [
        (k1, "TOTAL PnL",      f"₹{total_pnl:>+,.0f}",  pnl_col, f"{ret_pct:>+.2%}"),
        (k2, "WIN RATE",       f"{cons.get('win_rate',0):.1%}", "amber", f"{cons.get('total_trades',0)} trades"),
        (k3, "PROFIT FACTOR",  f"{cons.get('profit_factor',0):.2f}", "blue", "gross W ÷ gross L"),
        (k4, "SHARPE RATIO",   f"{cons.get('sharpe',0):.2f}", "green", "annualised"),
        (k5, "REBALANCES",     str(report.get("rebalances", 0)), "amber", "auto capital moves"),
        (k6, "DNA GENERATION", str(random.randint(5,40)), "purple" if True else "amber", "mutations"),
        (k7, "ACTIVE POS.",    str(sum(len(p.get("open_positions",{})) for p in ports.values())),
              "green", "across all books"),
    ]
    for col, label, val, color, sub in cards:
        col.markdown(f"""
        <div class='gm-card'>
          <div class='gm-card-label'>{label}</div>
          <div class='gm-card-value {color}'>{val}</div>
          <div class='gm-card-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Row 2 — equity curves + allocation donut
    left, right = st.columns([3, 1])

    with left:
        st.markdown("<div class='gm-section-header'>EQUITY CURVES — ALL PORTFOLIOS</div>",
                    unsafe_allow_html=True)
        equity_series = {}
        for pname, pdata in ports.items():
            equity_series[pname] = simulate_equity_curve(
                pdata.get("equity", 100_000), n=120
            )
        st.plotly_chart(equity_curve_chart(equity_series), use_container_width=True)

    with right:
        st.markdown("<div class='gm-section-header'>ALLOCATION</div>",
                    unsafe_allow_html=True)
        eq_map = {k: v.get("equity", 0) for k, v in ports.items()}
        wt_map = {k: v.get("weight", 0) for k, v in ports.items()}
        st.plotly_chart(donut_chart(wt_map, eq_map), use_container_width=True)
        for pname, pdata in ports.items():
            wt  = pdata.get("weight", 0)
            ret = pdata.get("return_pct", 0)
            rc  = "green" if ret >= 0 else "red"
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;
                        font-size:10px;padding:3px 4px;border-bottom:1px solid #1c2030'>
              <span style='color:#8a90a0'>{pname.replace("_"," ")[:9]}</span>
              <span style='color:#ffb300'>{wt:.0%}</span>
              <span class='{rc}'>{ret:>+.2%}</span>
            </div>""", unsafe_allow_html=True)

    # Row 3 — portfolio status table + recommendations
    left2, right2 = st.columns([2, 1])

    with left2:
        st.markdown("<div class='gm-section-header'>PORTFOLIO STATUS MATRIX</div>",
                    unsafe_allow_html=True)
        st.markdown("""
        <div class='port-row port-row-head'>
          <div>PORTFOLIO</div><div>EQUITY</div><div>PnL</div>
          <div>WIN RATE</div><div>SHARPE</div><div>MAX DD</div><div>GRADE</div>
        </div>""", unsafe_allow_html=True)

        grade_cls = {"A+": "grade-A", "A": "grade-A", "B+": "grade-B",
                     "B": "grade-B", "C": "grade-C", "D": "grade-D"}

        for pname, pdata in ports.items():
            g     = pdata.get("grade", "B")
            gcls  = grade_cls.get(g, "grade-B")
            pnl   = pdata.get("total_pnl", 0)
            pc    = "green" if pnl >= 0 else "red"
            dd    = pdata.get("max_drawdown", 0)
            ddc   = "red" if dd > 0.10 else ("amber" if dd > 0.05 else "green")
            st.markdown(f"""
            <div class='port-row'>
              <div style='font-size:11px;color:#f0f0f0'>{pname.replace("_"," ")}</div>
              <div>₹{pdata.get("equity",0):>12,.0f}</div>
              <div class='{pc}'>₹{pnl:>+10,.0f}</div>
              <div>{pdata.get("win_rate",0):.1%}</div>
              <div>{pdata.get("sharpe",0):.2f}</div>
              <div class='{ddc}'>{dd:.2%}</div>
              <div><span class='grade {gcls}'>{g}</span></div>
            </div>""", unsafe_allow_html=True)

    with right2:
        st.markdown("<div class='gm-section-header'>AI RECOMMENDATIONS</div>",
                    unsafe_allow_html=True)
        for rec in report.get("recommendations", []):
            st.markdown(f"<div class='rec-card'>{rec}</div>", unsafe_allow_html=True)

    # Row 4 — terminal log
    st.markdown("<div class='gm-section-header'>SYSTEM LOG</div>",
                unsafe_allow_html=True)
    alerts = report.get("alerts", [])
    lines  = "".join(
        f"<div class='terminal-line-{'ok' if 'BUY' in a or 'score' in a.lower() else 'warn' if 'STOP' in a or 'SELL' in a else 'info'}'>"
        f"{a}</div>"
        for a in alerts
    )
    st.markdown(f"""
    <div class='terminal'>
      <div class='terminal-line-sys'>[ GOD MODE PORTFOLIO SYSTEM — LIVE LOG ]</div>
      {lines}
      <div class='terminal-line-sys'>▮</div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PAGE B  ——  LIVE CHARTS
# ─────────────────────────────────────────────────────────────
elif page == "📈 Live Charts":

    sym = st.session_state.selected_sym

    # Fetch data
    period_map = {"1m": "1d", "5m": "5d", "15m": "1mo",
                  "1h": "3mo", "1d": "1y"}
    ohlcv = fetch_price_history(sym, period=period_map.get(tf, "1d"), interval=tf)

    st.markdown(f"<div class='gm-section-header'>PRICE ACTION — {sym} ({tf})</div>",
                unsafe_allow_html=True)

    if chart_type == "Candle":
        st.plotly_chart(candlestick_chart(ohlcv, sym, height=420),
                        use_container_width=True)
    else:
        fig = go.Figure()
        col = AMBER
        fig.add_trace(go.Scatter(
            x=ohlcv.index, y=ohlcv["Close"],
            mode="lines",
            line=dict(color=col, width=1.5),
            fill="tozeroy" if chart_type == "Area" else None,
            fillcolor="rgba(255,179,0,0.06)",
            name=sym,
        ))
        layout = dict(**PLOT_LAYOUT)
        layout.update(height=420, title=dict(
            text=f"  {sym}", font=dict(size=12, color=AMBER), x=0.01))
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    # Stats row
    close = ohlcv["Close"]
    vol   = ohlcv["Volume"]
    returns = close.pct_change().dropna()

    s1, s2, s3, s4, s5, s6 = st.columns(6)
    last_px   = float(close.iloc[-1])
    prev_px   = float(close.iloc[-2]) if len(close) > 1 else last_px
    chg       = last_px - prev_px
    chg_pct   = chg / prev_px if prev_px else 0
    chg_col   = "green" if chg >= 0 else "red"

    stat_cards = [
        (s1, "LTP",       f"₹{last_px:,.2f}", chg_col, f"{chg:>+.2f} ({chg_pct:>+.2%})"),
        (s2, "HIGH (D)",  f"₹{close.max():,.2f}", "amber", "session high"),
        (s3, "LOW (D)",   f"₹{close.min():,.2f}", "amber", "session low"),
        (s4, "AVG VOL",   f"{vol.mean()/1e5:.1f}L", "blue",  "avg volume"),
        (s5, "σ (DAILY)", f"{returns.std()*100:.2f}%", "purple", "daily volatility"),
        (s6, "BARS",      f"{len(close):,}", "amber", f"@ {tf}"),
    ]
    for col, lbl, v, vc, sub in stat_cards:
        col.markdown(f"""
        <div class='gm-card'>
          <div class='gm-card-label'>{lbl}</div>
          <div class='gm-card-value {vc}' style='font-size:20px'>{v}</div>
          <div class='gm-card-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

    # RSI + Volume trend
    st.markdown("")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown("<div class='gm-section-header'>RSI(14)</div>",
                    unsafe_allow_html=True)
        delta  = close.diff()
        gain   = delta.where(delta > 0, 0).rolling(14).mean()
        loss   = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs     = gain / loss.replace(0, 1e-9)
        rsi_s  = 100 - 100 / (1 + rs)
        rsi_val = float(rsi_s.iloc[-1]) if not rsi_s.empty else 50.0
        st.plotly_chart(rsi_gauge(rsi_val), use_container_width=True)
        sig = "🔻 OVERBOUGHT" if rsi_val > 70 else ("🔥 OVERSOLD" if rsi_val < 30 else "⏸ NEUTRAL")
        sig_cls = "sell" if rsi_val > 70 else ("buy" if rsi_val < 30 else "hold")
        st.markdown(f"<div style='text-align:center'><span class='signal signal-{sig_cls}'>{sig}</span></div>",
                    unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='gm-section-header'>VOLUME PROFILE</div>",
                    unsafe_allow_html=True)
        fig_vol = go.Figure()
        vcolors = [GREEN if c >= o else RED
                   for c, o in zip(ohlcv["Close"].tail(60), ohlcv["Open"].tail(60))]
        vma20   = ohlcv["Volume"].rolling(20).mean()
        fig_vol.add_trace(go.Bar(
            x=ohlcv.index[-60:], y=ohlcv["Volume"].tail(60),
            marker_color=vcolors, marker_opacity=0.7, name="Volume",
        ))
        fig_vol.add_trace(go.Scatter(
            x=ohlcv.index[-60:], y=vma20.tail(60),
            line=dict(color=AMBER, width=1.5), name="VMA20",
        ))
        layout = dict(**PLOT_LAYOUT)
        layout.update(height=220)
        fig_vol.update_layout(**layout)
        st.plotly_chart(fig_vol, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# PAGE C  ——  PORTFOLIOS
# ─────────────────────────────────────────────────────────────
elif page == "💼 Portfolios":

    tabs = st.tabs(["📗 LONG-TERM", "📙 SHORT-TERM", "📕 TRADING"])

    def render_portfolio_tab(pname: str, watchlist: list, color: str):
        pdata = ports.get(pname, {})

        # KPIs
        c1, c2, c3, c4, c5 = st.columns(5)
        kpi = [
            (c1, "EQUITY",     f"₹{pdata.get('equity',0):>12,.0f}",  "amber"),
            (c2, "NET PnL",    f"₹{pdata.get('total_pnl',0):>+10,.0f}",
                               "green" if pdata.get("total_pnl",0)>=0 else "red"),
            (c3, "RETURN",     f"{pdata.get('return_pct',0):>+.2%}", "blue"),
            (c4, "WIN RATE",   f"{pdata.get('win_rate',0):.1%}",     "amber"),
            (c5, "GRADE",      pdata.get("grade", "B"),               "green"),
        ]
        for col, lbl, v, vc in kpi:
            col.markdown(f"""
            <div class='gm-card'>
              <div class='gm-card-label'>{lbl}</div>
              <div class='gm-card-value {vc}'>{v}</div>
            </div>""", unsafe_allow_html=True)

        # Equity curve
        st.markdown(f"<div class='gm-section-header'>{pname.replace('_',' ')} — EQUITY CURVE</div>",
                    unsafe_allow_html=True)
        eq_s = simulate_equity_curve(pdata.get("equity", 100_000))
        fig_eq = go.Figure(go.Scatter(
            x=eq_s.index, y=eq_s.values,
            mode="lines", line=dict(color=color, width=1.5),
            fill="tozeroy", fillcolor=f"rgba({'255,179,0' if color==AMBER else '0,230,118' if color==GREEN else '64,196,255'},0.06)",
        ))
        layout = dict(**PLOT_LAYOUT); layout.update(height=200)
        fig_eq.update_layout(**layout)
        fig_eq.update_yaxes(tickformat="₹,.0f")
        st.plotly_chart(fig_eq, use_container_width=True)

        col_left, col_right = st.columns([1, 1])

        with col_left:
            # Stock scores
            st.markdown("<div class='gm-section-header'>STOCK SCORES</div>",
                        unsafe_allow_html=True)
            mock_scores = {s: round(random.uniform(2.5, 9.5), 1)
                          for s in random.sample(watchlist, min(8, len(watchlist)))}
            st.plotly_chart(score_bar_chart(mock_scores), use_container_width=True)

        with col_right:
            # Open positions
            st.markdown("<div class='gm-section-header'>OPEN POSITIONS</div>",
                        unsafe_allow_html=True)
            open_pos = pdata.get("open_positions", {})
            if open_pos:
                for sym, qty in open_pos.items():
                    px   = random.uniform(500, 4000)
                    unr  = round(random.uniform(-5000, 12000), 2)
                    uc   = "green" if unr >= 0 else "red"
                    st.markdown(f"""
                    <div class='port-row' style='grid-template-columns:1fr 1fr 1fr 1fr'>
                      <div style='color:#f0f0f0'>{sym.replace('.NS','')}</div>
                      <div style='color:#8a90a0'>{qty} sh</div>
                      <div style='color:#ffb300'>₹{px:,.0f}</div>
                      <div class='{uc}'>₹{unr:>+,.0f}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#3a4060;font-size:11px;padding:8px'>No open positions</div>",
                            unsafe_allow_html=True)

            # PnL histogram
            st.markdown("<div class='gm-section-header'>PnL DISTRIBUTION</div>",
                        unsafe_allow_html=True)
            mock_pnls = list(np.random.normal(300, 800, 40))
            st.plotly_chart(pnl_histogram(mock_pnls), use_container_width=True)

    with tabs[0]: render_portfolio_tab("LONG_TERM",  LT_WATCHLIST, AMBER)
    with tabs[1]: render_portfolio_tab("SHORT_TERM", ST_WATCHLIST, GREEN)
    with tabs[2]: render_portfolio_tab("TRADING",    ["RELIANCE.NS"], BLUE)


# ─────────────────────────────────────────────────────────────
# PAGE D  ——  SIGNAL LAB
# ─────────────────────────────────────────────────────────────
elif page == "🔬 Signal Lab":

    sym = st.session_state.selected_sym
    st.markdown(f"<div class='gm-section-header'>SIGNAL LAB — {sym}</div>",
                unsafe_allow_html=True)

    ohlcv = fetch_price_history(sym, period="1d", interval="1m")
    close = ohlcv["Close"].to_numpy().astype(float)

    # Compute indicators inline (no TA-Lib dependency in frontend)
    def _rsi(c, p=14):
        delta = pd.Series(c).diff()
        gain  = delta.where(delta > 0, 0).rolling(p).mean()
        loss  = (-delta.where(delta < 0, 0)).rolling(p).mean()
        rs    = gain / loss.replace(0, 1e-9)
        return float((100 - 100 / (1 + rs)).iloc[-1])

    def _ema(c, p): return float(pd.Series(c).ewm(span=p).mean().iloc[-1])
    def _macd(c):
        fast = pd.Series(c).ewm(span=12).mean()
        slow = pd.Series(c).ewm(span=26).mean()
        macd = fast - slow
        sig  = macd.ewm(span=9).mean()
        diff_prev = float(macd.iloc[-2] - sig.iloc[-2])
        diff_curr = float(macd.iloc[-1] - sig.iloc[-1])
        return "BULL ↑" if diff_prev < 0 and diff_curr >= 0 else ("BEAR ↓" if diff_prev > 0 and diff_curr <= 0 else "FLAT")
    def _bb_pos(c, w=20):
        s   = pd.Series(c)
        mid = s.rolling(w).mean()
        std = s.rolling(w).std()
        pct = float((s.iloc[-1] - (mid.iloc[-1] - 2*std.iloc[-1])) /
                    (4 * std.iloc[-1]) * 100) if std.iloc[-1] else 50
        return min(max(pct, 0), 100)

    rsi_v  = _rsi(close)
    ema9   = _ema(close, 9)
    ema21  = _ema(close, 21)
    macd_s = _macd(close)
    bb_pct = _bb_pos(close)
    price  = float(close[-1])

    ema_cross = "GOLDEN ↑" if ema9 > ema21 else "DEATH ↓"
    ema_color = "green" if ema9 > ema21 else "red"
    rsi_color = "red" if rsi_v > 70 else ("green" if rsi_v < 30 else "amber")
    macd_color = "green" if "BULL" in macd_s else ("red" if "BEAR" in macd_s else "amber")

    # Signal grid
    sg = st.columns(8)
    signals = [
        ("RSI(14)",     f"{rsi_v:.1f}", rsi_color,  "OVERSOLD" if rsi_v<30 else "OVERBOUGHT" if rsi_v>70 else "NEUTRAL"),
        ("MACD",        macd_s,    macd_color,  "momentum"),
        ("EMA 9/21",    ema_cross, ema_color,   f"9={ema9:.0f} 21={ema21:.0f}"),
        ("BB %",        f"{bb_pct:.0f}%",  "blue",  "band position"),
        ("REGIME",      random.choice(["CALM","HIGH-VOL"]), "amber", "HMM state"),
        ("HURST",       random.choice(["TRENDING","MEAN-REV","RANDOM"]), "blue", "H exponent"),
        ("MONTE C.",    f"{random.uniform(0.50,0.75):.1%}", "green", "P(profit)"),
        ("VOTES",       f"{random.randint(-2,8):>+d}/10", "amber", "consensus"),
    ]
    for col, (label, val, vc, sub) in zip(sg, signals):
        col.markdown(f"""
        <div class='gm-card'>
          <div class='gm-card-label'>{label}</div>
          <div class='gm-card-value {vc}' style='font-size:18px'>{val}</div>
          <div class='gm-card-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

    # Two-pane: candlestick + RSI sub-plot
    st.markdown("")
    st.plotly_chart(candlestick_chart(ohlcv, sym, height=400), use_container_width=True)

    # Signal history table
    st.markdown("<div class='gm-section-header'>RECENT SIGNALS</div>",
                unsafe_allow_html=True)
    sig_data = []
    for i in range(15):
        t = datetime.now() - timedelta(minutes=i*3)
        v = random.randint(-5, 9)
        sig_data.append({
            "TIME": t.strftime("%H:%M:%S"),
            "SYMBOL": sym,
            "RSI": round(random.uniform(25, 75), 1),
            "MACD": random.choice(["BULL↑","BEAR↓","FLAT"]),
            "BB":   random.choice(["BELOW","ABOVE","MID"]),
            "CDL":  random.choice(["NONE","HAMMER","ENGULF","NONE","NONE"]),
            "VOTES": f"{v:>+d}",
            "SIGNAL": "BUY" if v >= 3 else ("SELL" if v <= -2 else "HOLD"),
        })
    sig_df = pd.DataFrame(sig_data)

    def style_signals(df):
        def color_signal(val):
            if val == "BUY":  return "color: #00e676; font-weight:700"
            if val == "SELL": return "color: #ff1744; font-weight:700"
            return "color: #8a90a0"
        return df.style.applymap(color_signal, subset=["SIGNAL"])

    st.dataframe(style_signals(sig_df), use_container_width=True, height=320)


# ─────────────────────────────────────────────────────────────
# PAGE E  ——  TRADE HISTORY
# ─────────────────────────────────────────────────────────────
elif page == "📋 Trade History":

    st.markdown("<div class='gm-section-header'>TRADE HISTORY — ALL PORTFOLIOS</div>",
                unsafe_allow_html=True)

    # Filters
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        port_filter = st.multiselect("Portfolio", ["long_term","short_term","trading"],
                                     default=["long_term","short_term","trading"])
    with fc2:
        side_filter = st.multiselect("Side", ["BUY","SELL"], default=["BUY","SELL"])
    with fc3:
        min_pnl = st.number_input("Min PnL", value=-10000, step=500)
    with fc4:
        max_pnl = st.number_input("Max PnL", value=10000, step=500)

    df_show = trades.copy()
    if port_filter:
        df_show = df_show[df_show["portfolio"].isin(port_filter)]
    if side_filter:
        df_show = df_show[df_show["side"].isin(side_filter)]
    df_show = df_show[
        (df_show["pnl"] >= min_pnl) & (df_show["pnl"] <= max_pnl)
    ]

    # Summary stats
    sells = df_show[df_show["side"] == "SELL"]
    gross_w = sells[sells["pnl"] > 0]["pnl"].sum()
    gross_l = abs(sells[sells["pnl"] < 0]["pnl"].sum())
    st1, st2, st3, st4 = st.columns(4)
    stat_rows = [
        (st1, "TOTAL TRADES", len(df_show), "amber"),
        (st2, "TOTAL PnL",    f"₹{sells['pnl'].sum():>+,.0f}",
                              "green" if sells["pnl"].sum() >= 0 else "red"),
        (st3, "GROSS WIN",    f"₹{gross_w:>,.0f}", "green"),
        (st4, "GROSS LOSS",   f"₹{gross_l:>,.0f}", "red"),
    ]
    for col, lbl, v, vc in stat_rows:
        col.markdown(f"""
        <div class='gm-card'>
          <div class='gm-card-label'>{lbl}</div>
          <div class='gm-card-value {vc}' style='font-size:22px'>{v}</div>
        </div>""", unsafe_allow_html=True)

    # PnL over time chart
    if not sells.empty and "timestamp" in sells.columns:
        try:
            sells_s = sells.copy()
            sells_s["ts"] = pd.to_datetime(sells_s["timestamp"])
            sells_s = sells_s.sort_values("ts")
            cumulative = sells_s["pnl"].cumsum()
            fig_cum = go.Figure()
            colors_bar = [GREEN if p >= 0 else RED for p in sells_s["pnl"]]
            fig_cum.add_trace(go.Bar(x=sells_s["ts"], y=sells_s["pnl"],
                                     marker_color=colors_bar, name="Trade PnL"))
            fig_cum.add_trace(go.Scatter(x=sells_s["ts"], y=cumulative,
                                         line=dict(color=AMBER, width=2),
                                         name="Cumulative", yaxis="y2"))
            layout = dict(**PLOT_LAYOUT)
            layout.update(height=250, yaxis2=dict(
                overlaying="y", side="right",
                showgrid=False, tickformat="₹,.0f",
                tickfont=dict(size=9, color=AMBER),
            ))
            fig_cum.update_layout(**layout)
            st.plotly_chart(fig_cum, use_container_width=True)
        except Exception:
            pass

    # Table
    def style_trades(df):
        def color_row(row):
            if row["side"] == "BUY":  return ["color:#40c4ff"]*len(row)
            if row.get("pnl", 0) > 0: return ["color:#00e676"]*len(row)
            if row.get("pnl", 0) < 0: return ["color:#ff1744"]*len(row)
            return [""]*len(row)
        return df.style.apply(color_row, axis=1)

    cols_show = [c for c in ["timestamp","portfolio","symbol","side","qty",
                              "price","pnl","votes","notes"] if c in df_show.columns]
    st.dataframe(style_trades(df_show[cols_show].head(100)),
                 use_container_width=True, height=400)

    # Export
    csv_bytes = df_show.to_csv(index=False).encode()
    st.download_button("⬇ EXPORT CSV", csv_bytes,
                       file_name=f"trades_{datetime.now():%Y%m%d}.csv",
                       mime="text/csv")


# ─────────────────────────────────────────────────────────────
# PAGE F  ——  AI TRACKER
# ─────────────────────────────────────────────────────────────
elif page == "🤖 AI Tracker":

    st.markdown("<div class='gm-section-header'>AI PORTFOLIO TRACKER — MASTER INTELLIGENCE</div>",
                unsafe_allow_html=True)

    # Grade cards
    g1, g2, g3, g4 = st.columns(4)
    grade_data = [
        ("SYSTEM GRADE",      "A",  "green",  "Consolidated"),
    ] + [
        (pname.replace("_"," "), pdata.get("grade","B"),
         "green" if pdata.get("grade","B").startswith("A") else
         ("amber" if pdata.get("grade","B").startswith("B") else "red"),
         f"WR {pdata.get('win_rate',0):.1%}")
        for pname, pdata in ports.items()
    ]
    for col, (lbl, g, gc, sub) in zip([g1, g2, g3, g4], grade_data):
        col.markdown(f"""
        <div class='gm-card' style='text-align:center'>
          <div class='gm-card-label'>{lbl}</div>
          <div style='font-family:"Bebas Neue";font-size:64px;
                      line-height:1.1;color:var(--{gc})'>{g}</div>
          <div class='gm-card-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Radar chart — portfolio health
    categories = ["Win Rate","Profit Factor","Sharpe","Max DD (inv)","Trades"]
    fig_radar = go.Figure()
    colors_r   = [AMBER, GREEN, BLUE]
    for (pname, pdata), col in zip(ports.items(), colors_r):
        wr  = pdata.get("win_rate", 0) * 10
        pf  = min(pdata.get("profit_factor", 1) * 3, 10)
        sh  = min(max(pdata.get("sharpe", 0) * 4, 0), 10)
        dd  = max(10 - pdata.get("max_drawdown", 0) * 100, 0)
        tr  = min(pdata.get("trades", 0) / 10, 10)
        vals = [wr, pf, sh, dd, tr]
        vals += [vals[0]]  # close polygon
        cats = categories + [categories[0]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=cats,
            fill="toself",
            fillcolor=col.replace("#","rgba(").replace(")", ",0.12)") if col.startswith("#") else f"rgba(255,179,0,0.12)",
            line=dict(color=col, width=2),
            name=pname.replace("_"," "),
        ))
    fig_radar.update_layout(
        **{**PLOT_LAYOUT,
           "height": 380,
           "polar": dict(
               bgcolor=BGCARD,
               radialaxis=dict(range=[0,10], showticklabels=True,
                               tickcolor="#3a4060", tickfont=dict(size=8),
                               gridcolor="#1c2030"),
               angularaxis=dict(tickfont=dict(size=10, color="#f0f0f0"),
                                gridcolor="#1c2030"),
           )})
    del fig_radar.layout["xaxis"]; del fig_radar.layout["yaxis"]

    rc1, rc2 = st.columns([1, 1])
    with rc1:
        st.markdown("<div class='gm-section-header'>PORTFOLIO HEALTH RADAR</div>",
                    unsafe_allow_html=True)
        st.plotly_chart(fig_radar, use_container_width=True)
    with rc2:
        st.markdown("<div class='gm-section-header'>AI ANALYSIS</div>",
                    unsafe_allow_html=True)
        for rec in report.get("recommendations", []):
            st.markdown(f"<div class='rec-card'>{rec}</div>", unsafe_allow_html=True)

        st.markdown("<div class='gm-section-header' style='margin-top:16px'>SYSTEM METRICS</div>",
                    unsafe_allow_html=True)
        metrics = [
            ("Total Capital",    f"₹{cons.get('total_capital',0):>12,.0f}"),
            ("Total Equity",     f"₹{cons.get('total_equity',0):>12,.0f}"),
            ("Consolidated PnL", f"₹{cons.get('total_pnl',0):>+12,.0f}"),
            ("System Return",    f"{cons.get('return_pct',0):>+.2%}"),
            ("Profit Factor",    f"{cons.get('profit_factor',0):.2f}"),
            ("Sharpe Ratio",     f"{cons.get('sharpe',0):.2f}"),
            ("Total Trades",     str(cons.get("total_trades", 0))),
            ("Rebalances Done",  str(report.get("rebalances", 0))),
            ("Report #",         str(report.get("report_id", 0))),
        ]
        for lbl, v in metrics:
            pnl_c = "green" if "+" in v else ("red" if "-" in v and "₹" in v else "amber")
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;
                        font-size:11px;padding:5px 4px;border-bottom:1px solid #1c2030'>
              <span style='color:#8a90a0'>{lbl}</span>
              <span class='{pnl_c}'>{v}</span>
            </div>""", unsafe_allow_html=True)

    # DNA display
    st.markdown("<div class='gm-section-header'>DARWIN ENGINE — ACTIVE DNA</div>",
                unsafe_allow_html=True)
    dna = {
        "rsi_period": random.randint(12,16), "rsi_overbought": random.randint(68,74),
        "rsi_oversold": random.randint(28,33), "bollinger_window": random.randint(18,22),
        "macd_fast": random.randint(11,13), "macd_slow": random.randint(24,28),
        "macd_signal": random.randint(8,10), "stop_loss_mult": round(random.uniform(1.8,2.5),2),
        "consensus_threshold": random.randint(2,4),
    }
    dna_cols = st.columns(len(dna))
    for col, (gene, val) in zip(dna_cols, dna.items()):
        gene_short = gene.replace("_"," ").upper()
        col.markdown(f"""
        <div class='gm-card' style='text-align:center;padding:10px'>
          <div class='gm-card-label' style='font-size:8px'>{gene_short}</div>
          <div style='font-family:"Bebas Neue";font-size:22px;
                      color:#ea80fc;letter-spacing:1px'>{val}</div>
        </div>""", unsafe_allow_html=True)

    # Log
    st.markdown("<div class='gm-section-header'>AI ALERT STREAM</div>",
                unsafe_allow_html=True)
    all_alerts = report.get("alerts", [])
    lines = "".join(
        f"<div class='terminal-line-{'ok' if 'BUY' in a or 'GOOD' in a.upper() else 'warn' if 'WARN' in a.upper() or 'ALERT' in a.upper() else 'info'}'>{a}</div>"
        for a in all_alerts
    )
    st.markdown(f"""
    <div class='terminal' style='height:180px'>
      <div class='terminal-line-sys'>[ AI PORTFOLIO TRACKER — ALERT STREAM ]</div>
      {lines}
      <div class='terminal-line-sys'>▮</div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# 10.  AUTO-REFRESH FOOTER
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
ft1, ft2, ft3 = st.columns([2, 1, 1])
with ft1:
    st.markdown(f"""
    <div style='font-size:9px;letter-spacing:2px;color:#3a4060;font-family:"IBM Plex Mono"'>
    GOD MODE PORTFOLIO SYSTEM v3.0  |  NSE INDIA  |  PAPER TRADING ONLY
    &nbsp; — &nbsp; NOT FINANCIAL ADVICE &nbsp; — &nbsp;
    {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}
    </div>""", unsafe_allow_html=True)
with ft3:
    if st.button("⟳ REFRESH NOW"):
        st.cache_data.clear()
        st.rerun()

st.session_state.tick += 1

# Auto-rerun
if st.session_state.engine_on:
    time.sleep(refresh)
    st.rerun()
