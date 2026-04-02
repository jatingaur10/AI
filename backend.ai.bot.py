"""
╔══════════════════════════════════════════════════════════════════════╗
║        GOD MODE COMPLETE PORTFOLIO SYSTEM  —  ULTIMATE EDITION      ║
║        NSE / Indian Market  |  Full Paper Trading                    ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ── CORE ENGINE ──────────────────────────────────────────────────  ║
║  01. MasterConfig        All parameters in one place                 ║
║  02. DarwinEngine        Genetic parameter evolution                 ║
║  03. QuantMath           Kalman·HMM·Hurst·RSI·BB·MACD·OBV·Stoch    ║
║  04. SniperEngine        12 TA-Lib candlestick patterns              ║
║  05. MonteCarloEngine    GBM probability risk gate (1000 sims)       ║
║  06. PaperBroker         Multi-symbol order book + trailing stops    ║
║  07. PerformanceTracker  Sharpe · PF · WinRate · Drawdown           ║
║  08. TradeLogger         Auto date-stamped CSV per portfolio         ║
║  09. RiskGuard           Daily loss limit + cooldown circuit breaker ║
║  10. LiveDataFeed        yfinance multi-timeframe OHLCV              ║
║  11. Backtester          Pre-live historical validation              ║
║                                                                      ║
║  ── PORTFOLIO LAYER ───────────────────────────────────────────────  ║
║  12. LongTermPortfolio   Blue-chip basket, weekly evaluation         ║
║  13. ShortTermPortfolio  Swing trades, daily evaluation              ║
║  14. TradingPortfolio    Intraday scalp, 1-min candles               ║
║                                                                      ║
║  ── AI OVERSIGHT ──────────────────────────────────────────────────  ║
║  15. PortfolioRebalancer Target-weight drift rebalancing             ║
║  16. AIPortfolioTracker  Master AI dashboard + letter grades + recs  ║
║  17. Master Orchestrator Async co-ordinator of all loops            ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  CAPITAL SPLIT:  Long-Term 60%  |  Short-Term 25%  |  Trading 15%  ║
╠══════════════════════════════════════════════════════════════════════╣
║  INSTALL:                                                            ║
║    pip install numpy pandas yfinance talib-binary hmmlearn hurst     ║
║               colorama                                               ║
║  RUN:                                                                ║
║    python god_mode_complete.py                                       ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ── Standard Library ──────────────────────────────────────────────────
import asyncio
import csv
import json
import math
import os
import random
import sys
import time
import traceback
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Third-party ───────────────────────────────────────────────────────
import numpy as np
import pandas as pd
import talib
import yfinance as yf
from colorama import Back, Fore, Style, init
from hmmlearn.hmm import GaussianHMM
from hurst import compute_Hc

init(autoreset=True)


# ═══════════════════════════════════════════════════════════════════════
# 01  MASTER CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class MasterConfig:
    """Single source of truth for the entire system."""

    # ── Capital ─────────────────────────────────────────────────────
    TOTAL_CAPITAL:     float = 1_000_000.0   # ₹10 lakh total
    CURRENCY:          str   = "₹"

    # Portfolio target weights (must sum to 1.0)
    WEIGHT_LONG:       float = 0.60   # 60% → long-term basket
    WEIGHT_SHORT:      float = 0.25   # 25% → swing trades
    WEIGHT_TRADING:    float = 0.15   # 15% → intraday scalping

    REBALANCE_DRIFT:   float = 0.05   # Rebalance when any bucket drifts >5%
    REBALANCE_INTERVAL_HRS: int = 24  # Check rebalance every 24 h

    # ── Risk ────────────────────────────────────────────────────────
    MAX_RISK_PER_TRADE: float = 0.05
    DAILY_LOSS_LIMIT:   float = 0.03
    MAX_CONSEC_LOSSES:  int   = 3
    COOLDOWN_SECS:      int   = 300
    ATR_PERIOD:         int   = 14

    # ── Long-Term Settings ──────────────────────────────────────────
    LT_WATCHLIST: List[str] = field(default_factory=lambda: [
        "RELIANCE.NS", "TCS.NS",     "HDFCBANK.NS", "INFY.NS",
        "HINDUNILVR.NS", "ITC.NS",   "SBIN.NS",     "BAJFINANCE.NS",
        "MARUTI.NS",     "WIPRO.NS",
    ])
    LT_MAX_POSITIONS:   int   = 8        # Max stocks held at once
    LT_EVAL_INTERVAL:   int   = 3600     # Re-score every 1 hour (secs)
    LT_MIN_SCORE:       float = 3.0      # Min score to open a position
    LT_CANDLE_PERIOD:   str   = "1d"     # Daily candles
    LT_CANDLE_LOOKBACK: str   = "6mo"    # 6 months of history

    # ── Short-Term Settings ─────────────────────────────────────────
    ST_WATCHLIST: List[str] = field(default_factory=lambda: [
        "TATASTEEL.NS", "AXISBANK.NS",  "SUNPHARMA.NS", "HCLTECH.NS",
        "ULTRACEMCO.NS","NESTLEIND.NS", "POWERGRID.NS", "NTPC.NS",
    ])
    ST_MAX_POSITIONS:   int   = 4
    ST_EVAL_INTERVAL:   int   = 1800     # Re-score every 30 minutes
    ST_MIN_SCORE:       float = 2.5
    ST_CANDLE_PERIOD:   str   = "1d"
    ST_CANDLE_LOOKBACK: str   = "3mo"
    ST_HOLD_DAYS_MAX:   int   = 10       # Force-exit after 10 calendar days

    # ── Trading (Intraday) Settings ─────────────────────────────────
    TR_SYMBOL:          str   = "RELIANCE.NS"
    TR_LOOP_INTERVAL:   int   = 60       # Seconds per tick
    TR_MIN_HISTORY:     int   = 100
    TR_CANDLE_PERIOD:   str   = "1m"
    TR_FETCH_THROTTLE:  int   = 30

    # ── Backtester ──────────────────────────────────────────────────
    BT_MIN_WIN_RATE:    float = 0.35
    BT_MUTATIONS:       int   = 5

    # ── AI Tracker ──────────────────────────────────────────────────
    AI_REPORT_INTERVAL: int   = 600      # Full AI report every 10 minutes
    LOG_DIR:            str   = "logs"


# ═══════════════════════════════════════════════════════════════════════
# 02  DARWIN ENGINE  — Genetic Evolution
# ═══════════════════════════════════════════════════════════════════════

class DarwinEngine:
    """Adaptive strategy DNA with bounded mutation and rollback."""

    GENE_BOUNDS: Dict[str, Tuple] = {
        "rsi_period":          (5,  30),
        "rsi_overbought":      (60, 85),
        "rsi_oversold":        (15, 40),
        "bollinger_window":    (10, 50),
        "macd_fast":           (5,  20),
        "macd_slow":           (15, 40),
        "macd_signal":         (5,  15),
        "stop_loss_mult":      (1.0, 4.0),
        "consensus_threshold": (2,  6),
    }

    def __init__(self) -> None:
        self.dna: Dict = {
            "rsi_period": 14, "rsi_overbought": 70, "rsi_oversold": 30,
            "bollinger_window": 20, "macd_fast": 12, "macd_slow": 26,
            "macd_signal": 9, "stop_loss_mult": 2.0, "consensus_threshold": 3,
        }
        self.generation: int  = 1
        self._prev_dna: Dict  = dict(self.dna)
        self._prev_pnl: float = 0.0

    def mutate(self, current_pnl: float) -> None:
        if current_pnl < self._prev_pnl:
            self.dna = dict(self._prev_dna)
        self._prev_dna = dict(self.dna)
        self._prev_pnl = current_pnl
        gene = random.choice(list(self.dna.keys()))
        lo, hi = self.GENE_BOUNDS[gene]
        old = self.dna[gene]
        f   = random.uniform(0.88, 1.12)
        self.dna[gene] = (int(np.clip(round(old * f), lo, hi))
                          if isinstance(old, int)
                          else round(float(np.clip(old * f, lo, hi)), 4))
        print(f"{Fore.MAGENTA}  🧬 Gen{self.generation:>3} | '{gene}': {old} → {self.dna[gene]}")
        self.generation += 1

    def display(self) -> None:
        print(f"{Fore.MAGENTA}  DNA Gen-{self.generation-1}: "
              + "  ".join(f"{k}={v}" for k, v in self.dna.items()))


# ═══════════════════════════════════════════════════════════════════════
# 03  QUANT MATH ENGINE
# ═══════════════════════════════════════════════════════════════════════

class QuantMath:
    """All signal math: Kalman · HMM · Hurst · RSI · BB · MACD · OBV · Stoch · EMA."""

    def __init__(self) -> None:
        self._kf_x, self._kf_p = 0.0, 1.0
        self._kf_q, self._kf_r = 1e-5, 0.01
        self._hmm = GaussianHMM(n_components=2, covariance_type="diag",
                                n_iter=100, random_state=42)
        self._hmm_trained = False

    # ── Kalman ─────────────────────────────────────────────────────
    def kalman_update(self, price: float) -> float:
        p_pred     = self._kf_p + self._kf_q
        k          = p_pred / (p_pred + self._kf_r)
        self._kf_x = self._kf_x + k * (price - self._kf_x)
        self._kf_p = (1 - k) * p_pred
        return self._kf_x

    # ── HMM ────────────────────────────────────────────────────────
    def market_regime(self, returns: np.ndarray) -> int:
        if len(returns) < 50: return 0
        data = returns.reshape(-1, 1)
        if not self._hmm_trained:
            try:    self._hmm.fit(data); self._hmm_trained = True
            except: return 0
        try:    return int(self._hmm.predict(data)[-1])
        except: return 0

    # ── Hurst ──────────────────────────────────────────────────────
    def chaos_state(self, prices: np.ndarray) -> str:
        if len(prices) < 100: return "UNKNOWN"
        try:
            H, _, _ = compute_Hc(prices, kind="price", simplified=True)
            return "TRENDING" if H > 0.6 else ("MEAN_REVERTING" if H < 0.4 else "RANDOM")
        except: return "UNKNOWN"

    # ── RSI ────────────────────────────────────────────────────────
    def rsi(self, closes: np.ndarray, period: int) -> float:
        if len(closes) < period + 1: return 50.0
        v = talib.RSI(closes.astype(float), timeperiod=period)[-1]
        return float(v) if not np.isnan(v) else 50.0

    # ── Bollinger Bands ────────────────────────────────────────────
    def bollinger_signal(self, closes: np.ndarray, window: int) -> int:
        if len(closes) < window: return 0
        upper, _, lower = talib.BBANDS(closes.astype(float), timeperiod=window)
        if np.isnan(upper[-1]): return 0
        p = closes[-1]
        return 1 if p < lower[-1] else (-1 if p > upper[-1] else 0)

    def bollinger_bandwidth(self, closes: np.ndarray, window: int) -> float:
        """Bandwidth as % of middle band — measures volatility squeeze."""
        if len(closes) < window: return 0.0
        upper, mid, lower = talib.BBANDS(closes.astype(float), timeperiod=window)
        if np.isnan(mid[-1]) or mid[-1] == 0: return 0.0
        return float((upper[-1] - lower[-1]) / mid[-1] * 100)

    # ── MACD ───────────────────────────────────────────────────────
    def macd_signal(self, closes: np.ndarray, fast: int, slow: int, sig: int) -> int:
        if len(closes) < slow + sig + 1: return 0
        macd, signal, _ = talib.MACD(closes.astype(float),
                                     fastperiod=fast, slowperiod=slow, signalperiod=sig)
        if np.isnan(macd[-1]) or np.isnan(macd[-2]): return 0
        prev = macd[-2] - signal[-2];  curr = macd[-1] - signal[-1]
        return 1 if (prev < 0 and curr >= 0) else (-1 if (prev > 0 and curr <= 0) else 0)

    # ── OBV ────────────────────────────────────────────────────────
    def obv_signal(self, closes: np.ndarray, volumes: np.ndarray, lb: int = 10) -> int:
        n = min(len(closes), len(volumes))
        if n < lb + 1: return 0
        obv = talib.OBV(closes[:n].astype(float), volumes[:n].astype(float))
        return (1 if obv[-1] - obv[-lb] > 0 and closes[-1] - closes[-lb] < 0
                else (-1 if obv[-1] - obv[-lb] < 0 and closes[-1] - closes[-lb] > 0
                      else 0))

    # ── Stochastic ─────────────────────────────────────────────────
    def stochastic_signal(self, h: np.ndarray, l: np.ndarray, c: np.ndarray,
                          k: int = 14, d: int = 3) -> int:
        if len(c) < k + d: return 0
        try:
            sk, sd = talib.STOCH(h.astype(float), l.astype(float), c.astype(float),
                                 fastk_period=k, slowk_period=d, slowd_period=d)
            if np.isnan(sk[-1]) or np.isnan(sk[-2]): return 0
            prev = sk[-2] - sd[-2]; curr = sk[-1] - sd[-1]
            return (1 if prev < 0 and curr >= 0 and sk[-1] < 20
                    else (-1 if prev > 0 and curr <= 0 and sk[-1] > 80 else 0))
        except: return 0

    # ── EMA Cross ──────────────────────────────────────────────────
    def ema_cross(self, closes: np.ndarray, fast: int = 9, slow: int = 21) -> int:
        if len(closes) < slow + 1: return 0
        fe = talib.EMA(closes.astype(float), timeperiod=fast)
        se = talib.EMA(closes.astype(float), timeperiod=slow)
        if np.isnan(fe[-1]) or np.isnan(fe[-2]): return 0
        prev = fe[-2] - se[-2]; curr = fe[-1] - se[-1]
        return 1 if (prev < 0 and curr >= 0) else (-1 if (prev > 0 and curr <= 0) else 0)

    # ── EMA200 Price Position ──────────────────────────────────────
    def price_vs_ema200(self, closes: np.ndarray) -> int:
        """+1 = price above EMA200 (bullish), -1 = below, 0 = too short."""
        if len(closes) < 200: return 0
        ema200 = talib.EMA(closes.astype(float), timeperiod=200)
        if np.isnan(ema200[-1]): return 0
        return 1 if closes[-1] > ema200[-1] else -1

    # ── ATR Trailing Stop ──────────────────────────────────────────
    def atr_trailing_stop(self, highs: np.ndarray, lows: np.ndarray,
                          closes: np.ndarray, period: int, mult: float) -> float:
        atr = talib.ATR(highs.astype(float), lows.astype(float),
                        closes.astype(float), timeperiod=period)
        val = atr[-1] if not np.isnan(atr[-1]) else (highs[-1] - lows[-1])
        return float(closes[-1] - val * mult)

    # ── Volume Trend ───────────────────────────────────────────────
    @staticmethod
    def volume_trend(volumes: np.ndarray, window: int = 20) -> float:
        """Ratio of recent avg volume to longer avg volume. >1 = rising."""
        if len(volumes) < window * 2: return 1.0
        recent = np.mean(volumes[-window:])
        older  = np.mean(volumes[-window * 2:-window])
        return float(recent / older) if older > 0 else 1.0

    # ── 52-Week Proximity ──────────────────────────────────────────
    @staticmethod
    def proximity_to_high(closes: np.ndarray, window: int = 252) -> float:
        """0.0 = at 52w low, 1.0 = at 52w high."""
        n = min(len(closes), window)
        if n < 2: return 0.5
        lo, hi = np.min(closes[-n:]), np.max(closes[-n:])
        return float((closes[-1] - lo) / (hi - lo)) if hi != lo else 0.5

    # ── Helpers ────────────────────────────────────────────────────
    @staticmethod
    def rolling_vol(returns: np.ndarray, w: int = 20) -> float:
        return float(np.std(returns[-w:])) if len(returns) >= w else 0.02

    @staticmethod
    def rolling_drift(returns: np.ndarray, w: int = 20) -> float:
        return float(np.mean(returns[-w:])) if len(returns) >= w else 0.0


# ═══════════════════════════════════════════════════════════════════════
# 04  SNIPER ENGINE — Candlestick Patterns
# ═══════════════════════════════════════════════════════════════════════

class SniperEngine:
    _BULL = [
        (talib.CDLENGULFING, 100, "BULL_ENGULF"),
        (talib.CDLHAMMER, 100, "HAMMER"),
        (talib.CDLMORNINGSTAR, 100, "MORNING_STAR"),
        (talib.CDLPIERCING, 100, "PIERCING"),
        (talib.CDL3WHITESOLDIERS, 100, "3_SOLDIERS"),
        (talib.CDLDRAGONFLYDOJI, 100, "DRAGONFLY"),
    ]
    _BEAR = [
        (talib.CDLENGULFING, -100, "BEAR_ENGULF"),
        (talib.CDLSHOOTINGSTAR, -100, "SHOOT_STAR"),
        (talib.CDLEVENINGSTAR, -100, "EVENING_STAR"),
        (talib.CDLDARKCLOUDCOVER, -100, "DARK_CLOUD"),
        (talib.CDL3BLACKCROWS, -100, "3_CROWS"),
        (talib.CDLGRAVESTONEDOJI, -100, "GRAVESTONE"),
    ]

    def detect(self, o: np.ndarray, h: np.ndarray,
               l: np.ndarray, c: np.ndarray) -> Tuple[int, str]:
        if len(c) < 10: return 0, "NONE"
        o, h, l, c = (a.astype(float) for a in (o, h, l, c))
        for fn, exp, lbl in self._BULL:
            try:
                if fn(o, h, l, c)[-1] == exp: return 1, lbl
            except: pass
        for fn, exp, lbl in self._BEAR:
            try:
                if fn(o, h, l, c)[-1] == exp: return -1, lbl
            except: pass
        return 0, "NONE"


# ═══════════════════════════════════════════════════════════════════════
# 05  MONTE CARLO ENGINE
# ═══════════════════════════════════════════════════════════════════════

class MonteCarloEngine:
    def __init__(self, simulations: int = 1000) -> None:
        self.simulations = simulations

    def is_safe(self, price: float, vol: float,
                drift: float = 0.0, threshold: float = 0.55) -> Tuple[bool, float]:
        z = np.random.standard_normal(self.simulations)
        future = price * np.exp((drift - 0.5 * vol**2) + vol * z)
        prob = float(np.mean(future > price))
        return prob >= threshold, round(prob, 4)


# ═══════════════════════════════════════════════════════════════════════
# 06  PAPER BROKER  — Multi-Symbol
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class TradeRecord:
    timestamp:  str
    portfolio:  str
    symbol:     str
    side:       str
    qty:        int
    price:      float
    pnl:        float = 0.0


class PaperBroker:
    """Multi-symbol paper broker. Each portfolio gets its own instance."""

    def __init__(self, name: str, capital: float) -> None:
        self.name            = name
        self.cash            = capital
        self.initial_capital = capital
        self.positions:     Dict[str, int]   = {}
        self.entry_prices:  Dict[str, float] = {}
        self.active_stops:  Dict[str, float] = {}
        self.entry_dates:   Dict[str, datetime] = {}
        self.history:       List[TradeRecord] = []

    # ── Properties ─────────────────────────────────────────────────
    @property
    def equity(self) -> float:
        return self.cash   # mark-to-market excluded

    @property
    def total_pnl(self) -> float:
        return sum(t.pnl for t in self.history if t.side == "SELL")

    @property
    def last_pnl(self) -> Optional[float]:
        sells = [t for t in self.history if t.side == "SELL"]
        return sells[-1].pnl if sells else None

    @property
    def return_pct(self) -> float:
        return (self.equity - self.initial_capital) / self.initial_capital

    # ── Orders ─────────────────────────────────────────────────────
    def buy(self, symbol: str, qty: int, price: float) -> bool:
        if qty <= 0 or qty * price > self.cash:
            return False
        self.cash                    -= qty * price
        self.positions[symbol]        = self.positions.get(symbol, 0) + qty
        self.entry_prices[symbol]     = price
        self.entry_dates[symbol]      = datetime.now()
        self.history.append(TradeRecord(
            datetime.now().isoformat(timespec="seconds"),
            self.name, symbol, "BUY", qty, price))
        print(f"{Fore.GREEN}  [{self.name}] ✅ BUY  {qty:>4} {symbol} @ "
              f"₹{price:>10,.2f}  cash→₹{self.cash:>12,.2f}")
        return True

    def sell(self, symbol: str, qty: int, price: float) -> bool:
        held = self.positions.get(symbol, 0)
        if qty <= 0 or held < qty: return False
        self.cash                   += qty * price
        self.positions[symbol]       = held - qty
        if self.positions[symbol] == 0:
            self.entry_prices.pop(symbol, None)
            self.active_stops.pop(symbol, None)
            self.entry_dates.pop(symbol, None)
        ep  = self.entry_prices.get(symbol, price)
        pnl = (price - ep) * qty
        self.history.append(TradeRecord(
            datetime.now().isoformat(timespec="seconds"),
            self.name, symbol, "SELL", qty, price, pnl))
        col = Fore.GREEN if pnl >= 0 else Fore.RED
        print(f"{col}  [{self.name}] {'💰' if pnl >= 0 else '💸'} SELL "
              f"{qty:>4} {symbol} @ ₹{price:>10,.2f}  "
              f"PnL ₹{pnl:>+10,.2f}  Total ₹{self.total_pnl:>+10,.2f}")
        return True

    def force_close_all(self, price_map: Dict[str, float]) -> None:
        for sym, qty in list(self.positions.items()):
            if qty > 0:
                px = price_map.get(sym, self.entry_prices.get(sym, 0))
                if px > 0:
                    self.sell(sym, qty, px)

    def top_up(self, amount: float) -> None:
        """Receive capital from rebalancer."""
        self.cash += amount

    def withdraw(self, amount: float) -> float:
        """Return capital to rebalancer. Returns actual withdrawn."""
        actual = min(amount, self.cash)
        self.cash -= actual
        return actual

    def summary_line(self) -> str:
        open_pos = sum(1 for q in self.positions.values() if q > 0)
        return (f"[{self.name:<8}] Cash ₹{self.cash:>12,.2f} | "
                f"Pos={open_pos} | Ret={self.return_pct:>+.2%} | "
                f"PnL ₹{self.total_pnl:>+10,.2f}")


# ═══════════════════════════════════════════════════════════════════════
# 07  PERFORMANCE TRACKER
# ═══════════════════════════════════════════════════════════════════════

class PerformanceTracker:
    def __init__(self, name: str) -> None:
        self.name          = name
        self.pnls:         List[float] = []
        self.equity_curve: List[float] = []
        self.peak_equity   = 0.0
        self.max_drawdown  = 0.0
        self.consec_losses = 0

    def record(self, pnl: float, equity: float) -> None:
        self.pnls.append(pnl)
        self.equity_curve.append(equity)
        self.peak_equity = max(self.peak_equity, equity)
        if self.peak_equity > 0:
            self.max_drawdown = max(self.max_drawdown,
                                    (self.peak_equity - equity) / self.peak_equity)
        self.consec_losses = (self.consec_losses + 1) if pnl < 0 else 0

    @property
    def win_rate(self) -> float:
        return sum(1 for p in self.pnls if p > 0) / len(self.pnls) if self.pnls else 0.0

    @property
    def profit_factor(self) -> float:
        w = sum(p for p in self.pnls if p > 0)
        l = abs(sum(p for p in self.pnls if p < 0))
        return round(w / l, 4) if l else float("inf")

    @property
    def sharpe(self) -> float:
        if len(self.pnls) < 2: return 0.0
        arr = np.array(self.pnls)
        std = np.std(arr)
        return round(float(np.mean(arr) / std * math.sqrt(252 * 375)), 4) if std else 0.0

    @property
    def total_pnl(self) -> float:
        return sum(self.pnls)

    def letter_grade(self) -> str:
        """AI-style A–F grade based on weighted metric score."""
        score = 0.0
        score += min(self.win_rate * 5, 2.0)                  # max 2 pts
        score += min(self.profit_factor * 0.5, 2.0)           # max 2 pts
        score += min(max(self.sharpe * 0.5, 0), 2.0)          # max 2 pts
        score -= min(self.max_drawdown * 10, 2.0)              # penalty
        if   score >= 5.0: return "A+"
        elif score >= 4.0: return "A"
        elif score >= 3.0: return "B+"
        elif score >= 2.0: return "B"
        elif score >= 1.0: return "C"
        else:              return "D"

    def one_liner(self) -> str:
        return (f"Trades={len(self.pnls)}  WR={self.win_rate:.1%}  "
                f"PF={self.profit_factor:.2f}  Sharpe={self.sharpe:.2f}  "
                f"MaxDD={self.max_drawdown:.2%}  Grade={self.letter_grade()}")


# ═══════════════════════════════════════════════════════════════════════
# 08  TRADE LOGGER
# ═══════════════════════════════════════════════════════════════════════

class TradeLogger:
    FIELDS = ["timestamp", "portfolio", "symbol", "side", "qty",
              "price", "pnl", "cash_after", "generation", "votes", "notes"]

    def __init__(self, log_dir: str, portfolio_name: str) -> None:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        fname     = f"{datetime.now():%Y-%m-%d}_{portfolio_name}.csv"
        self.path = Path(log_dir) / fname
        if not self.path.exists():
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=self.FIELDS).writeheader()

    def log(self, **kw) -> None:
        row = {k: kw.get(k, "") for k in self.FIELDS}
        row.setdefault("timestamp", datetime.now().isoformat(timespec="seconds"))
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self.FIELDS).writerow(row)


# ═══════════════════════════════════════════════════════════════════════
# 09  RISK GUARD
# ═══════════════════════════════════════════════════════════════════════

class RiskGuard:
    def __init__(self, cfg: MasterConfig, tracker: PerformanceTracker) -> None:
        self._cfg             = cfg
        self._tracker         = tracker
        self._start_equity:   Optional[float] = None
        self._cooldown_until: float = 0.0
        self._halted:         bool  = False

    def set_start(self, equity: float) -> None:
        if self._start_equity is None:
            self._start_equity = equity

    def check(self, equity: float) -> Tuple[bool, str]:
        if self._halted:
            return False, "Daily limit hit — halted."
        if time.time() < self._cooldown_until:
            return False, f"Cooldown {int(self._cooldown_until - time.time())}s"
        if self._start_equity and self._start_equity > 0:
            loss = (self._start_equity - equity) / self._start_equity
            if loss >= self._cfg.DAILY_LOSS_LIMIT:
                self._halted = True
                return False, f"Daily loss {loss:.2%} ≥ limit {self._cfg.DAILY_LOSS_LIMIT:.2%}"
        if self._tracker.consec_losses >= self._cfg.MAX_CONSEC_LOSSES:
            self._cooldown_until = time.time() + self._cfg.COOLDOWN_SECS
            return False, f"{self._cfg.MAX_CONSEC_LOSSES} consec losses — cooling down"
        return True, "OK"


# ═══════════════════════════════════════════════════════════════════════
# 10  LIVE DATA FEED  — Multi-Symbol, Multi-Timeframe
# ═══════════════════════════════════════════════════════════════════════

class LiveDataFeed:
    COLS = ["Open", "High", "Low", "Close", "Volume"]

    def __init__(self, throttle_secs: int = 30) -> None:
        self._throttle  = throttle_secs
        self._cache:    Dict[str, pd.DataFrame] = {}
        self._last:     Dict[str, float]        = {}
        self._sim_px:   Dict[str, float]        = {}

    def fetch(self, symbol: str, period: str = "1d",
              interval: str = "1d", bars: int = 300) -> Optional[pd.DataFrame]:
        key = f"{symbol}|{interval}"
        now = time.time()
        if now - self._last.get(key, 0) < self._throttle and key in self._cache:
            return self._cache[key]
        try:
            df = yf.Ticker(symbol).history(period=period, interval=interval)
            if df is None or df.empty or len(df) < 10:
                raise ValueError("Insufficient data")
            df = df[self.COLS].dropna().tail(bars)
            self._cache[key]    = df
            self._last[key]     = now
            self._sim_px[symbol] = float(df["Close"].iloc[-1])
            return df
        except Exception as e:
            return self._simulate(symbol, bars)

    def _simulate(self, symbol: str, bars: int) -> pd.DataFrame:
        base   = self._sim_px.get(symbol, 1000.0 + random.uniform(0, 3000))
        mu, sig = 0.00005, 0.0015
        z      = np.random.standard_normal(bars)
        closes = base * np.exp(np.cumsum((mu - 0.5 * sig**2) + sig * z))
        spread = 0.003
        opens  = closes * (1 + np.random.uniform(-spread, spread, bars))
        highs  = np.maximum(opens, closes) * (1 + np.abs(np.random.normal(0, spread/2, bars)))
        lows   = np.minimum(opens, closes) * (1 - np.abs(np.random.normal(0, spread/2, bars)))
        vols   = np.random.randint(50_000, 800_000, bars).astype(float)
        idx    = pd.date_range(end=datetime.now(), periods=bars, freq="1min")
        df     = pd.DataFrame(
            {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
            index=idx)
        self._sim_px[symbol] = float(closes[-1])
        key = f"{symbol}|sim"
        self._cache[key] = df
        return df

    def last_price(self, symbol: str) -> float:
        return self._sim_px.get(symbol, 0.0)


# ═══════════════════════════════════════════════════════════════════════
# 11  BACKTESTER
# ═══════════════════════════════════════════════════════════════════════

class Backtester:
    def __init__(self, cfg: MasterConfig, darwin: DarwinEngine,
                 quant: QuantMath, sniper: SniperEngine,
                 mc: MonteCarloEngine) -> None:
        self._cfg = cfg; self._darwin = darwin
        self._quant = quant; self._sniper = sniper; self._mc = mc

    def run(self, df: pd.DataFrame, label: str = "") -> Dict:
        closes, highs  = df["Close"].to_numpy(), df["High"].to_numpy()
        lows,   opens  = df["Low"].to_numpy(),   df["Open"].to_numpy()
        volumes        = df["Volume"].to_numpy()
        cash, pos, ep  = self._cfg.TOTAL_CAPITAL * self._cfg.WEIGHT_TRADING, 0, 0.0
        stop, trades   = 0.0, []
        d              = self._darwin.dna

        for i in range(self._cfg.TR_MIN_HISTORY, len(closes)):
            c = closes[:i+1]; h = highs[:i+1]
            l = lows[:i+1];   o = opens[:i+1]
            v = volumes[:i+1]
            px      = float(c[-1])
            returns = np.diff(c)
            votes   = 0

            sm = self._quant.kalman_update(px)
            if px < sm * 0.999: votes += 1
            rsi = self._quant.rsi(c, d["rsi_period"])
            if rsi < d["rsi_oversold"]:    votes += 2
            elif rsi > d["rsi_overbought"]: votes -= 2
            votes += self._quant.bollinger_signal(c, d["bollinger_window"])
            votes += self._quant.macd_signal(c, d["macd_fast"], d["macd_slow"], d["macd_signal"])
            votes += self._quant.obv_signal(c, v)
            votes += self._quant.stochastic_signal(h, l, c)
            votes += self._quant.ema_cross(c)
            ps, _ = self._sniper.detect(o, h, l, c)
            votes += ps * 2
            vol   = QuantMath.rolling_vol(returns)
            drift = QuantMath.rolling_drift(returns)
            safe, prob = self._mc.is_safe(px, vol, drift)
            if not safe: votes -= 3

            thresh = d["consensus_threshold"]
            if votes >= thresh and pos == 0:
                qty = int((cash * self._cfg.MAX_RISK_PER_TRADE * min(prob*2, 1.0)) / px)
                if qty > 0:
                    cash -= qty * px; pos = qty; ep = px
                    stop = self._quant.atr_trailing_stop(h, l, c, self._cfg.ATR_PERIOD,
                                                         d["stop_loss_mult"])
            elif pos > 0:
                ns = self._quant.atr_trailing_stop(h, l, c, self._cfg.ATR_PERIOD,
                                                   d["stop_loss_mult"])
                if ns > stop: stop = ns
                if px < stop or votes <= -thresh:
                    pnl = (px - ep) * pos; cash += pos * px
                    trades.append(pnl); pos = 0

        if pos > 0:
            pnl = (closes[-1] - ep) * pos; cash += pos * closes[-1]; trades.append(pnl)

        wins   = [p for p in trades if p > 0]
        losses = [p for p in trades if p <= 0]
        wr     = len(wins) / len(trades) if trades else 0.0
        pf     = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else float("inf")
        total  = sum(trades)

        w = 58
        print(f"\n{Fore.CYAN}{'═'*w}")
        print(f"{Fore.CYAN}  🔬 BACKTEST {label} — {len(df)} bars")
        print(f"{Fore.CYAN}{'─'*w}")
        print(f"  Trades: {len(trades)} ({len(wins)}W/{len(losses)}L)  "
              f"WR: {wr:.1%}  PF: {pf:.2f}  PnL: ₹{total:>+,.2f}")
        print(f"{Fore.CYAN}{'═'*w}\n")
        return {"win_rate": wr, "total_pnl": total, "trades": len(trades)}


# ═══════════════════════════════════════════════════════════════════════
# 12  LONG-TERM PORTFOLIO
# ═══════════════════════════════════════════════════════════════════════

class LongTermPortfolio:
    """
    Blue-chip buy-and-hold basket using daily candles.

    Scoring system (max 10 points per stock):
      • 2 pts — Price above EMA200 (long-term uptrend)
      • 2 pts — RSI(14) between 40–65 (healthy momentum, not overbought)
      • 2 pts — Volume trend > 1.1 (accumulation)
      • 2 pts — Price within top 30% of 52-week range (strength)
      • 1 pt  — MACD bullish crossover on daily
      • 1 pt  — OBV rising while price pulls back (accumulation signal)

    Open position if score ≥ LT_MIN_SCORE.
    Close position if score falls below (LT_MIN_SCORE - 1.5).
    """

    def __init__(self, cfg: MasterConfig, quant: QuantMath,
                 feed: LiveDataFeed, broker: PaperBroker,
                 tracker: PerformanceTracker, logger: TradeLogger) -> None:
        self.cfg     = cfg
        self.quant   = quant
        self.feed    = feed
        self.broker  = broker
        self.tracker = tracker
        self.logger  = logger
        self._last_eval: float = 0.0
        self.scores: Dict[str, float] = {}

    def _score_stock(self, symbol: str) -> Tuple[float, Dict]:
        """Download daily data and compute fundamental+technical score."""
        df = self.feed.fetch(symbol, period=self.cfg.LT_CANDLE_LOOKBACK,
                             interval=self.cfg.LT_CANDLE_PERIOD, bars=300)
        if df is None or len(df) < 50:
            return 0.0, {}

        c = df["Close"].to_numpy()
        h = df["High"].to_numpy()
        l = df["Low"].to_numpy()
        v = df["Volume"].to_numpy()
        o = df["Open"].to_numpy()

        detail: Dict[str, Any] = {}
        score  = 0.0

        # 1. EMA200 (long-term trend)
        ema_v = self.quant.price_vs_ema200(c)
        if ema_v == 1: score += 2; detail["EMA200"] = "ABOVE ✅"
        else:          detail["EMA200"] = "BELOW ❌"

        # 2. RSI health zone
        rsi = self.quant.rsi(c, 14)
        detail["RSI"] = f"{rsi:.1f}"
        if 40 <= rsi <= 65: score += 2; detail["RSI_zone"] = "HEALTHY ✅"
        elif rsi < 30:      score += 1; detail["RSI_zone"] = "OVERSOLD"
        else:               detail["RSI_zone"] = "OB/NEUTRAL"

        # 3. Volume trend
        vtrd = QuantMath.volume_trend(v, 20)
        detail["VolTrend"] = f"{vtrd:.2f}"
        if vtrd > 1.1: score += 2; detail["Vol"] = "ACCUMULATING ✅"
        elif vtrd > 0.9: score += 1; detail["Vol"] = "NEUTRAL"
        else:            detail["Vol"] = "DECLINING ❌"

        # 4. 52-week proximity
        prox = QuantMath.proximity_to_high(c, 252)
        detail["52W_prox"] = f"{prox:.2f}"
        if prox > 0.70: score += 2; detail["52W"] = "STRONG ✅"
        elif prox > 0.40: score += 1; detail["52W"] = "MID"
        else:              detail["52W"] = "WEAK ❌"

        # 5. MACD daily
        macd_v = self.quant.macd_signal(c, 12, 26, 9)
        if macd_v == 1:  score += 1; detail["MACD"] = "BULL_CROSS ✅"
        elif macd_v == -1: detail["MACD"] = "BEAR_CROSS ❌"
        else:               detail["MACD"] = "FLAT"

        # 6. OBV accumulation
        obv_v = self.quant.obv_signal(c, v)
        if obv_v == 1:   score += 1; detail["OBV"] = "ACCUMULATE ✅"
        elif obv_v == -1: detail["OBV"] = "DISTRIBUTE ❌"
        else:              detail["OBV"] = "NEUTRAL"

        detail["price"] = float(c[-1])
        detail["score"] = round(score, 2)
        return score, detail

    async def evaluate(self) -> None:
        """Score all watchlist stocks and manage positions."""
        now = time.time()
        if now - self._last_eval < self.cfg.LT_EVAL_INTERVAL:
            return
        self._last_eval = now

        print(f"\n{Fore.BLUE}{'─'*60}")
        print(f"{Fore.BLUE}  📈 LONG-TERM PORTFOLIO  |  Evaluating {len(self.cfg.LT_WATCHLIST)} stocks")
        print(f"{Fore.BLUE}{'─'*60}")

        ranked: List[Tuple[str, float, Dict]] = []
        for sym in self.cfg.LT_WATCHLIST:
            score, detail = self._score_stock(sym)
            self.scores[sym] = score
            ranked.append((sym, score, detail))
            grade_col = Fore.GREEN if score >= self.cfg.LT_MIN_SCORE else Fore.YELLOW
            print(f"  {grade_col}{sym:<18} Score: {score:.1f}/10  "
                  f"RSI={detail.get('RSI','?')} Vol={detail.get('VolTrend','?')} "
                  f"52W={detail.get('52W_prox','?')}{Fore.RESET}")

        ranked.sort(key=lambda x: x[1], reverse=True)
        top = [s for s, sc, _ in ranked if sc >= self.cfg.LT_MIN_SCORE][:self.cfg.LT_MAX_POSITIONS]

        # EXIT positions that fell out of top or score degraded
        for sym in list(self.broker.positions.keys()):
            if self.broker.positions.get(sym, 0) > 0:
                if sym not in top or self.scores.get(sym, 0) < self.cfg.LT_MIN_SCORE - 1.5:
                    px  = self.feed.last_price(sym)
                    qty = self.broker.positions[sym]
                    if px > 0 and self.broker.sell(sym, qty, px):
                        last_pnl = self.broker.last_pnl or 0.0
                        self.tracker.record(last_pnl, self.broker.equity)
                        self.logger.log(portfolio="LONG_TERM", symbol=sym,
                                        side="SELL", qty=qty, price=px,
                                        pnl=last_pnl, cash_after=self.broker.cash,
                                        notes=f"Score dropped to {self.scores.get(sym,0):.1f}")

        # ENTER new top-ranked positions
        current_pos_count = sum(1 for q in self.broker.positions.values() if q > 0)
        slots = self.cfg.LT_MAX_POSITIONS - current_pos_count

        for sym in top:
            if slots <= 0: break
            if self.broker.positions.get(sym, 0) > 0: continue  # already held

            px = self.feed.last_price(sym)
            if px <= 0: continue

            # Equal-weight allocation across max positions
            alloc = self.broker.cash / max(slots, 1) * self.cfg.MAX_RISK_PER_TRADE * 3
            qty   = int(alloc / px)
            if qty > 0 and self.broker.buy(sym, qty, px):
                self.logger.log(portfolio="LONG_TERM", symbol=sym,
                                side="BUY", qty=qty, price=px,
                                cash_after=self.broker.cash,
                                notes=f"Score={self.scores[sym]:.1f}")
                slots -= 1

        print(f"{Fore.BLUE}  Positions: {sum(1 for q in self.broker.positions.values() if q>0)}"
              f"/{self.cfg.LT_MAX_POSITIONS}  "
              f"Cash: ₹{self.broker.cash:,.2f}{Fore.RESET}")


# ═══════════════════════════════════════════════════════════════════════
# 13  SHORT-TERM PORTFOLIO  — Swing Trades
# ═══════════════════════════════════════════════════════════════════════

class ShortTermPortfolio:
    """
    Swing-trade engine. Holds positions for 2–10 calendar days.

    Entry conditions (votes ≥ ST_MIN_SCORE):
      • RSI oversold bounce (≤35)                   +2
      • BB lower band touch                          +1
      • MACD bullish crossover                       +2
      • Stochastic oversold cross                    +1
      • EMA9/21 golden cross                         +1
      • Bullish candlestick pattern                  +2

    Exit conditions:
      • Votes swing negative (≤-2)
      • ATR trailing stop hit
      • Max hold time exceeded (ST_HOLD_DAYS_MAX)
    """

    def __init__(self, cfg: MasterConfig, quant: QuantMath, sniper: SniperEngine,
                 mc: MonteCarloEngine, feed: LiveDataFeed, broker: PaperBroker,
                 tracker: PerformanceTracker, logger: TradeLogger,
                 darwin: DarwinEngine) -> None:
        self.cfg     = cfg;     self.quant   = quant
        self.sniper  = sniper;  self.mc      = mc
        self.feed    = feed;    self.broker  = broker
        self.tracker = tracker; self.logger  = logger
        self.darwin  = darwin
        self._last_eval: float = 0.0

    def _score_swing(self, symbol: str) -> Tuple[float, float, Dict]:
        """Score a swing-trade candidate. Returns (votes, price, details)."""
        df = self.feed.fetch(symbol, period=self.cfg.ST_CANDLE_LOOKBACK,
                             interval=self.cfg.ST_CANDLE_PERIOD, bars=200)
        if df is None or len(df) < 50:
            return 0.0, 0.0, {}

        c = df["Close"].to_numpy()
        h = df["High"].to_numpy()
        l = df["Low"].to_numpy()
        v = df["Volume"].to_numpy()
        o = df["Open"].to_numpy()

        votes  = 0.0
        detail: Dict[str, Any] = {"price": float(c[-1])}

        rsi = self.quant.rsi(c, 14)
        detail["RSI"] = f"{rsi:.1f}"
        if rsi <= 35:
            votes += 2; detail["RSI_sig"] = "OVERSOLD ✅"
        elif rsi >= 70:
            votes -= 2; detail["RSI_sig"] = "OVERBOUGHT ❌"

        bb = self.quant.bollinger_signal(c, 20)
        if bb == 1:   votes += 1; detail["BB"] = "BELOW_LOWER ✅"
        elif bb == -1: votes -= 1; detail["BB"] = "ABOVE_UPPER ❌"

        macd_v = self.quant.macd_signal(c, 12, 26, 9)
        if macd_v == 1:   votes += 2; detail["MACD"] = "BULL ✅"
        elif macd_v == -1: votes -= 2; detail["MACD"] = "BEAR ❌"

        stoch = self.quant.stochastic_signal(h, l, c)
        if stoch == 1:   votes += 1; detail["STOCH"] = "OS_CROSS ✅"
        elif stoch == -1: votes -= 1; detail["STOCH"] = "OB_CROSS ❌"

        ema = self.quant.ema_cross(c, 9, 21)
        if ema == 1:   votes += 1; detail["EMA"] = "GOLDEN ✅"
        elif ema == -1: votes -= 1; detail["EMA"] = "DEATH ❌"

        pat_s, pat_l = self.sniper.detect(o, h, l, c)
        votes += pat_s * 2
        detail["CDL"] = pat_l

        returns = np.diff(c)
        vol     = QuantMath.rolling_vol(returns)
        drift   = QuantMath.rolling_drift(returns)
        safe, prob = self.mc.is_safe(float(c[-1]), vol, drift)
        if not safe: votes -= 3; detail["MC"] = f"UNSAFE {prob:.0%}"
        else:        detail["MC"] = f"SAFE {prob:.0%}"

        return votes, float(c[-1]), detail

    async def evaluate(self) -> None:
        now = time.time()
        if now - self._last_eval < self.cfg.ST_EVAL_INTERVAL:
            return
        self._last_eval = now

        print(f"\n{Fore.YELLOW}{'─'*60}")
        print(f"{Fore.YELLOW}  📊 SHORT-TERM PORTFOLIO  |  Swing Scan")
        print(f"{Fore.YELLOW}{'─'*60}")

        # Check & exit existing positions
        for sym in list(self.broker.positions.keys()):
            qty = self.broker.positions.get(sym, 0)
            if qty == 0: continue

            # Check max hold days
            entry_date = self.broker.entry_dates.get(sym)
            if entry_date:
                days_held = (datetime.now() - entry_date).days
                if days_held >= self.cfg.ST_HOLD_DAYS_MAX:
                    px = self.feed.last_price(sym)
                    if px > 0 and self.broker.sell(sym, qty, px):
                        pnl = self.broker.last_pnl or 0.0
                        self.tracker.record(pnl, self.broker.equity)
                        self.logger.log(portfolio="SHORT_TERM", symbol=sym,
                                        side="SELL", qty=qty, price=px,
                                        pnl=pnl, cash_after=self.broker.cash,
                                        notes=f"Max hold {days_held}d")
                        if pnl < 0: self.darwin.mutate(self.broker.total_pnl)
                    continue

            # Re-score for exit signal
            votes, px, _ = self._score_swing(sym)
            if votes <= -2 and px > 0:
                if self.broker.sell(sym, qty, px):
                    pnl = self.broker.last_pnl or 0.0
                    self.tracker.record(pnl, self.broker.equity)
                    self.logger.log(portfolio="SHORT_TERM", symbol=sym,
                                    side="SELL", qty=qty, price=px,
                                    pnl=pnl, cash_after=self.broker.cash,
                                    notes=f"Votes={votes:.0f}")
                    if pnl < 0: self.darwin.mutate(self.broker.total_pnl)

        # Scan watchlist for entries
        current = sum(1 for q in self.broker.positions.values() if q > 0)
        slots   = self.cfg.ST_MAX_POSITIONS - current

        candidates: List[Tuple[str, float, float, Dict]] = []
        for sym in self.cfg.ST_WATCHLIST:
            if self.broker.positions.get(sym, 0) > 0: continue
            votes, px, detail = self._score_swing(sym)
            col = Fore.GREEN if votes >= self.cfg.ST_MIN_SCORE else Fore.RESET
            print(f"  {col}{sym:<18} Votes={votes:>+.0f}  "
                  f"RSI={detail.get('RSI','?')} CDL={detail.get('CDL','?')}"
                  f"  MC={detail.get('MC','?')}{Fore.RESET}")
            if votes >= self.cfg.ST_MIN_SCORE:
                candidates.append((sym, votes, px, detail))

        candidates.sort(key=lambda x: x[1], reverse=True)

        for sym, votes, px, detail in candidates:
            if slots <= 0: break
            if px <= 0: continue
            alloc = self.broker.cash * self.cfg.MAX_RISK_PER_TRADE * 2
            qty   = int(alloc / px)
            if qty > 0 and self.broker.buy(sym, qty, px):
                self.logger.log(portfolio="SHORT_TERM", symbol=sym,
                                side="BUY", qty=qty, price=px,
                                cash_after=self.broker.cash,
                                votes=votes, notes=str(detail))
                slots -= 1

        print(f"{Fore.YELLOW}  Positions: {current}/{self.cfg.ST_MAX_POSITIONS}  "
              f"Cash: ₹{self.broker.cash:,.2f}{Fore.RESET}")


# ═══════════════════════════════════════════════════════════════════════
# 14  TRADING PORTFOLIO  — Intraday Scalp
# ═══════════════════════════════════════════════════════════════════════

class TradingPortfolio:
    """
    High-frequency intraday engine on 1-minute candles.
    Full 9-signal voting system + Monte Carlo gate + ATR trailing stop.
    Pre-validated by backtester before going live.
    """

    def __init__(self, cfg: MasterConfig, darwin: DarwinEngine,
                 quant: QuantMath, sniper: SniperEngine, mc: MonteCarloEngine,
                 feed: LiveDataFeed, broker: PaperBroker,
                 tracker: PerformanceTracker, logger: TradeLogger,
                 guard: RiskGuard) -> None:
        self.cfg     = cfg;     self.darwin  = darwin
        self.quant   = quant;   self.sniper  = sniper
        self.mc      = mc;      self.feed    = feed
        self.broker  = broker;  self.tracker = tracker
        self.logger  = logger;  self.guard   = guard
        self._tick   = 0
        self._backtest_done = False

    async def run_tick(self) -> None:
        self._tick += 1
        sym = self.cfg.TR_SYMBOL

        # ── Fetch ──────────────────────────────────────────────────
        df = self.feed.fetch(sym, period="1d",
                             interval=self.cfg.TR_CANDLE_PERIOD,
                             bars=300)
        if df is None or len(df) < self.cfg.TR_MIN_HISTORY:
            print(f"{Fore.YELLOW}  [TRADE] ⏳ Building history "
                  f"{0 if df is None else len(df)}/{self.cfg.TR_MIN_HISTORY}")
            return

        # ── Run backtest once on first tick ────────────────────────
        if not self._backtest_done:
            bt = Backtester(self.cfg, self.darwin, self.quant, self.sniper, self.mc)
            res = bt.run(df, label="TRADING")
            if res["win_rate"] < self.cfg.BT_MIN_WIN_RATE:
                for _ in range(self.cfg.BT_MUTATIONS):
                    self.darwin.mutate(0.0)
                self.darwin.display()
            self._backtest_done = True
            self.guard.set_start(self.broker.equity)

        closes  = df["Close"].to_numpy()
        highs   = df["High"].to_numpy()
        lows    = df["Low"].to_numpy()
        opens   = df["Open"].to_numpy()
        volumes = df["Volume"].to_numpy()
        price   = float(closes[-1])
        returns = np.diff(closes)

        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n{Fore.WHITE}  [TRADE #{self._tick}] {ts}  {sym}  "
              f"₹{price:>10,.2f}  Cash ₹{self.broker.cash:>12,.2f}")

        # ── Risk Guard ─────────────────────────────────────────────
        ok, reason = self.guard.check(self.broker.equity)
        if not ok:
            print(f"{Fore.RED}  [TRADE] 🚨 GUARD: {reason}"); return

        # ── Market Filters ─────────────────────────────────────────
        chaos  = self.quant.chaos_state(closes)
        regime = self.quant.market_regime(returns)
        cc = {"TRENDING": Fore.GREEN, "MEAN_REVERTING": Fore.CYAN,
              "RANDOM": Fore.YELLOW, "UNKNOWN": Fore.WHITE}.get(chaos, Fore.WHITE)
        print(f"  {cc}Chaos:{chaos}  "
              f"{'⚠️ HI-VOL' if regime==1 else '✅ CALM'}{Fore.RESET}")

        if chaos == "RANDOM":
            print(f"{Fore.YELLOW}  [TRADE] Skipping — random walk."); return

        # ── Signal Voting ──────────────────────────────────────────
        votes: int = 0; reasons: List[str] = []
        d = self.darwin.dna

        sm = self.quant.kalman_update(price)
        if price < sm * 0.999: votes += 1; reasons.append("Kalman↓")

        rsi_v = self.quant.rsi(closes, d["rsi_period"])
        if rsi_v < d["rsi_oversold"]:    votes += 2; reasons.append(f"RSI_OS({rsi_v:.0f})")
        elif rsi_v > d["rsi_overbought"]: votes -= 2; reasons.append(f"RSI_OB({rsi_v:.0f})")

        bb = self.quant.bollinger_signal(closes, d["bollinger_window"])
        if bb == 1:   votes += 1; reasons.append("BB↓")
        elif bb == -1: votes -= 1; reasons.append("BB↑")

        macd_v = self.quant.macd_signal(closes, d["macd_fast"], d["macd_slow"], d["macd_signal"])
        if macd_v == 1:   votes += 2; reasons.append("MACD↑")
        elif macd_v == -1: votes -= 2; reasons.append("MACD↓")

        obv_v = self.quant.obv_signal(closes, volumes)
        if obv_v == 1:   votes += 1; reasons.append("OBV+")
        elif obv_v == -1: votes -= 1; reasons.append("OBV-")

        stoch = self.quant.stochastic_signal(highs, lows, closes)
        if stoch == 1:   votes += 1; reasons.append("STOCH↑")
        elif stoch == -1: votes -= 1; reasons.append("STOCH↓")

        ema_v = self.quant.ema_cross(closes)
        if ema_v == 1:   votes += 1; reasons.append("EMA_gold")
        elif ema_v == -1: votes -= 1; reasons.append("EMA_death")

        ps, pl = self.sniper.detect(opens, highs, lows, closes)
        if ps != 0: votes += ps * 2; reasons.append(f"CDL:{pl}")

        if chaos == "TRENDING" and len(closes) >= 10:
            mom = closes[-1] - closes[-10]
            if mom > 0: votes += 1; reasons.append("MOM↑")
            else:       votes -= 1; reasons.append("MOM↓")

        vol   = QuantMath.rolling_vol(returns)
        drift = QuantMath.rolling_drift(returns)
        safe, prob = self.mc.is_safe(price, vol, drift)
        if not safe: votes -= 3; reasons.append(f"MC✗{prob:.0%}")

        vc = Fore.GREEN if votes >= 0 else Fore.RED
        print(f"  RSI={rsi_v:.0f} BB={bb:+d} MACD={macd_v:+d} OBV={obv_v:+d} "
              f"CDL={pl}  MC={'✅' if safe else '❌'} P={prob:.1%}")
        print(f"  {vc}VOTES={votes:+d}{Fore.RESET}  [{', '.join(reasons)}]")

        thresh = d["consensus_threshold"]
        held   = self.broker.positions.get(sym, 0)

        # ── Execution ──────────────────────────────────────────────
        if votes >= thresh and held == 0:
            print(f"{Fore.CYAN}  [TRADE] 🔥 BUY  Votes={votes:+d}")
            frac = self.cfg.MAX_RISK_PER_TRADE * min(prob * 2, 1.0)
            qty  = int((self.broker.cash * frac) / price)
            if self.broker.buy(sym, qty, price):
                stop = self.quant.atr_trailing_stop(
                    highs, lows, closes, self.cfg.ATR_PERIOD, d["stop_loss_mult"])
                self.broker.active_stops[sym] = stop
                print(f"  🛡️  Stop ₹{stop:,.2f}")
                self.logger.log(portfolio="TRADING", symbol=sym,
                                side="BUY", qty=qty, price=price,
                                cash_after=self.broker.cash,
                                generation=self.darwin.generation,
                                votes=votes, notes=str(reasons))

        elif held > 0:
            ns = self.quant.atr_trailing_stop(
                highs, lows, closes, self.cfg.ATR_PERIOD, d["stop_loss_mult"])
            cur_stop = self.broker.active_stops.get(sym, 0.0)
            if ns > cur_stop:
                self.broker.active_stops[sym] = ns
                print(f"  ☝️  Stop → ₹{ns:,.2f}")

            stop_hit  = price < self.broker.active_stops.get(sym, 0)
            sell_sig  = votes <= -thresh

            if stop_hit or sell_sig:
                tag = "STOP" if stop_hit else "SIGNAL"
                print(f"{Fore.RED}  [TRADE] 🛑 SELL ({tag})")
                if self.broker.sell(sym, held, price):
                    pnl = self.broker.last_pnl or 0.0
                    self.tracker.record(pnl, self.broker.equity)
                    self.logger.log(portfolio="TRADING", symbol=sym,
                                    side="SELL", qty=held, price=price,
                                    pnl=pnl, cash_after=self.broker.cash,
                                    generation=self.darwin.generation,
                                    votes=votes, notes=tag)
                    if pnl < 0:
                        self.darwin.mutate(self.broker.total_pnl)
            else:
                unr = (price - self.broker.entry_prices.get(sym, price)) * held
                uc  = Fore.GREEN if unr >= 0 else Fore.RED
                print(f"  📌 Holding {held}  Unrealised: {uc}₹{unr:>+,.2f}{Fore.RESET}")

        else:
            print(f"  ⏸️  Flat  ({votes:+d} vs ±{thresh})")

        # Periodic stats
        if self._tick % 10 == 0:
            print(f"\n{Fore.CYAN}  📊 [TRADE] {self.tracker.one_liner()}\n")


# ═══════════════════════════════════════════════════════════════════════
# 15  PORTFOLIO REBALANCER
# ═══════════════════════════════════════════════════════════════════════

class PortfolioRebalancer:
    """
    Monitors the three portfolio cash buckets vs their target weights.
    When any bucket drifts beyond REBALANCE_DRIFT, it moves capital
    from the overweight portfolio to the underweight ones.

    Capital is transferred as cash (positions are NOT force-sold).
    """

    def __init__(self, cfg: MasterConfig,
                 lt_broker: PaperBroker,
                 st_broker: PaperBroker,
                 tr_broker: PaperBroker) -> None:
        self.cfg       = cfg
        self.brokers   = {
            "LONG":    (lt_broker, cfg.WEIGHT_LONG),
            "SHORT":   (st_broker, cfg.WEIGHT_SHORT),
            "TRADING": (tr_broker, cfg.WEIGHT_TRADING),
        }
        self._last_rebalance: float = 0.0
        self.rebalance_count: int   = 0

    def total_equity(self) -> float:
        return sum(b.equity for b, _ in self.brokers.values())

    def current_weights(self) -> Dict[str, float]:
        total = self.total_equity()
        if total == 0: return {k: 0.0 for k in self.brokers}
        return {k: b.equity / total for k, (b, _) in self.brokers.items()}

    def check_and_rebalance(self) -> bool:
        """Returns True if a rebalance was performed."""
        now = time.time()
        if now - self._last_rebalance < self.cfg.REBALANCE_INTERVAL_HRS * 3600:
            return False

        weights = self.current_weights()
        total   = self.total_equity()
        drifts  = {
            k: abs(weights[k] - target)
            for k, (_, target) in self.brokers.items()
        }

        if max(drifts.values()) < self.cfg.REBALANCE_DRIFT:
            return False  # No rebalance needed

        self._last_rebalance = now
        self.rebalance_count += 1

        print(f"\n{Fore.MAGENTA}{'═'*60}")
        print(f"{Fore.MAGENTA}  ⚖️  REBALANCER #{self.rebalance_count}  |  Total Equity: ₹{total:,.2f}")
        print(f"{Fore.MAGENTA}{'─'*60}")

        for name, (broker, target) in self.brokers.items():
            current_w = weights[name]
            target_eq = total * target
            current_eq = broker.equity
            diff = target_eq - current_eq
            status = "OVER" if diff < 0 else "UNDER"
            col    = Fore.RED if status == "OVER" else Fore.GREEN
            print(f"  {col}{name:<8} Current={current_w:.1%}  "
                  f"Target={target:.1%}  Drift={drifts[name]:.1%}  "
                  f"Δ₹{diff:>+10,.2f}  [{status}]{Fore.RESET}")

        # Step 1: Withdraw from overweight portfolios
        pool = 0.0
        for name, (broker, target) in self.brokers.items():
            target_eq  = total * target
            current_eq = broker.equity
            if current_eq > target_eq + 100:
                excess   = current_eq - target_eq
                withdrawn = broker.withdraw(excess * 0.8)  # conservative 80%
                pool     += withdrawn
                print(f"  {Fore.RED}  → Withdrew ₹{withdrawn:,.2f} from [{name}]{Fore.RESET}")

        # Step 2: Top up underweight portfolios
        for name, (broker, target) in self.brokers.items():
            target_eq  = total * target
            current_eq = broker.equity
            if current_eq < target_eq - 100 and pool > 0:
                needed    = min(target_eq - current_eq, pool)
                broker.top_up(needed)
                pool     -= needed
                print(f"  {Fore.GREEN}  → Topped up ₹{needed:,.2f} to [{name}]{Fore.RESET}")

        print(f"{Fore.MAGENTA}{'═'*60}\n")
        return True


# ═══════════════════════════════════════════════════════════════════════
# 16  AI PORTFOLIO TRACKER  — Master Intelligence Dashboard
# ═══════════════════════════════════════════════════════════════════════

class AIPortfolioTracker:
    """
    Master AI oversight layer. Aggregates all three portfolios and:

    1. Computes consolidated P&L, return, Sharpe across all portfolios.
    2. Issues AI letter grades per portfolio and for the whole system.
    3. Detects anomalies: underperformance, over-concentration, drawdown spikes.
    4. Generates natural-language recommendations.
    5. Saves a JSON report to disk every AI_REPORT_INTERVAL seconds.
    6. Displays a colour-coded master dashboard in the terminal.
    """

    def __init__(self, cfg: MasterConfig,
                 lt_broker: PaperBroker, lt_tracker: PerformanceTracker,
                 st_broker: PaperBroker, st_tracker: PerformanceTracker,
                 tr_broker: PaperBroker, tr_tracker: PerformanceTracker,
                 rebalancer: PortfolioRebalancer) -> None:
        self.cfg        = cfg
        self.portfolios = {
            "LONG_TERM":  (lt_broker, lt_tracker),
            "SHORT_TERM": (st_broker, st_tracker),
            "TRADING":    (tr_broker, tr_tracker),
        }
        self.rebalancer       = rebalancer
        self._last_report:    float = 0.0
        self._report_count:   int   = 0
        self._pnl_history:    deque = deque(maxlen=100)
        self._alert_log:      List[str] = []

        Path(cfg.LOG_DIR).mkdir(parents=True, exist_ok=True)
        self._report_path = Path(cfg.LOG_DIR) / "ai_portfolio_report.json"

    # ── Consolidated Metrics ───────────────────────────────────────
    def _consolidated(self) -> Dict:
        total_capital = self.cfg.TOTAL_CAPITAL
        total_equity  = sum(b.equity for b, _ in self.portfolios.values())
        total_pnl     = sum(b.total_pnl for b, _ in self.portfolios.values())
        all_pnls      = []
        for _, t in self.portfolios.values():
            all_pnls.extend(t.pnls)

        ret_pct = (total_equity - total_capital) / total_capital
        sharpe  = 0.0
        if len(all_pnls) >= 2:
            arr = np.array(all_pnls)
            std = np.std(arr)
            sharpe = float(np.mean(arr) / std * math.sqrt(252 * 375)) if std else 0.0

        wins   = sum(1 for p in all_pnls if p > 0)
        wr     = wins / len(all_pnls) if all_pnls else 0.0
        gross_w = sum(p for p in all_pnls if p > 0)
        gross_l = abs(sum(p for p in all_pnls if p < 0))
        pf      = round(gross_w / gross_l, 4) if gross_l else float("inf")

        return {
            "total_capital":  total_capital,
            "total_equity":   round(total_equity,  2),
            "total_pnl":      round(total_pnl,     2),
            "return_pct":     round(ret_pct,        4),
            "total_trades":   len(all_pnls),
            "win_rate":       round(wr,             4),
            "profit_factor":  pf,
            "sharpe":         round(sharpe,         4),
        }

    # ── AI Recommendations ─────────────────────────────────────────
    def _generate_recommendations(self, cons: Dict) -> List[str]:
        recs: List[str] = []
        weights = self.rebalancer.current_weights()

        # Per-portfolio analysis
        for name, (broker, tracker) in self.portfolios.items():
            grade = tracker.letter_grade()
            wr    = tracker.win_rate
            dd    = tracker.max_drawdown

            if grade in ("D",) and len(tracker.pnls) >= 3:
                recs.append(f"⚠️  [{name}] Grade {grade} — consider reducing allocation "
                            f"(WR={wr:.1%}, DD={dd:.2%})")

            if dd > 0.15:
                recs.append(f"🔴 [{name}] MAX DRAWDOWN ALERT: {dd:.2%} — "
                            f"tighten stop-loss multiplier immediately.")

            if wr > 0.70 and len(tracker.pnls) >= 5:
                recs.append(f"✅ [{name}] Excellent win rate {wr:.1%} — "
                            f"consider increasing position sizing.")

        # Concentration check
        for name, wt in weights.items():
            _, target_wt = self.portfolios.get(name,
                            (None, None)) or (None, self.cfg.WEIGHT_LONG)
            targets = {"LONG_TERM": self.cfg.WEIGHT_LONG,
                       "SHORT_TERM": self.cfg.WEIGHT_SHORT,
                       "TRADING": self.cfg.WEIGHT_TRADING}
            target = targets.get(name, 0.33)
            if wt > target + 0.10:
                recs.append(f"📊 [{name}] Over-weight at {wt:.1%} "
                            f"(target {target:.1%}) — rebalance recommended.")

        # System-wide
        if cons["sharpe"] > 1.5:
            recs.append("🌟 SYSTEM: Sharpe > 1.5 — portfolio is performing very well overall.")
        elif cons["sharpe"] < 0.3 and len(recs) > 2:
            recs.append("⚠️  SYSTEM: Low Sharpe — consider reviewing DNA parameters "
                        "across all portfolios.")

        if not recs:
            recs.append("✅ SYSTEM: All portfolios within normal parameters. No action needed.")

        return recs

    # ── Dashboard Print ────────────────────────────────────────────
    def print_dashboard(self) -> None:
        cons = self._consolidated()
        w    = 64

        print(f"\n{Back.BLACK}{Fore.CYAN}{'═'*w}")
        print(f"{Back.BLACK}{Fore.WHITE}{'  🤖  AI PORTFOLIO TRACKER  —  MASTER DASHBOARD':^{w}}")
        print(f"{Back.BLACK}{Fore.CYAN}{'─'*w}")

        ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        print(f"{Back.BLACK}{Fore.WHITE}  ⏱  {ts}")
        print(f"{Back.BLACK}{Fore.CYAN}{'─'*w}")

        # Per-portfolio rows
        for name, (broker, tracker) in self.portfolios.items():
            grade     = tracker.letter_grade()
            grade_col = (Fore.GREEN  if grade.startswith("A")
                         else Fore.YELLOW if grade.startswith("B")
                         else Fore.RED)
            open_pos  = sum(1 for q in broker.positions.values() if q > 0)
            ret_col   = Fore.GREEN if broker.return_pct >= 0 else Fore.RED

            print(f"{Back.BLACK}{Fore.WHITE}  {name:<12} │ "
                  f"Cash ₹{broker.cash:>12,.2f}  │  "
                  f"Ret {ret_col}{broker.return_pct:>+.2%}{Fore.WHITE}  │  "
                  f"PnL ₹{broker.total_pnl:>+10,.2f}  │  "
                  f"Pos={open_pos}  │  Grade {grade_col}{grade}{Fore.WHITE}")
            print(f"{Back.BLACK}{Fore.WHITE}  {'':12}   "
                  f"{tracker.one_liner()}")

        print(f"{Back.BLACK}{Fore.CYAN}{'─'*w}")

        # Consolidated row
        ret_c = Fore.GREEN if cons["return_pct"] >= 0 else Fore.RED
        print(f"{Back.BLACK}{Fore.WHITE}  {'CONSOLIDATED':<12} │ "
              f"Capital ₹{cons['total_capital']:>12,.2f}  │  "
              f"Equity ₹{cons['total_equity']:>12,.2f}")
        print(f"{Back.BLACK}{Fore.WHITE}  {'':12}   "
              f"Total PnL ₹{cons['total_pnl']:>+12,.2f}  │  "
              f"Return {ret_c}{cons['return_pct']:>+.2%}{Fore.WHITE}  │  "
              f"Trades={cons['total_trades']}  WR={cons['win_rate']:.1%}  "
              f"Sharpe={cons['sharpe']:.2f}")

        # Rebalancer
        wts = self.rebalancer.current_weights()
        wt_str = "  ".join(
            f"{k[:3]}={v:.1%}" for k, v in wts.items()
        )
        print(f"{Back.BLACK}{Fore.WHITE}  {'ALLOCATION':<12}   "
              f"Weights: {wt_str}  │  "
              f"Rebalances: {self.rebalancer.rebalance_count}")

        print(f"{Back.BLACK}{Fore.CYAN}{'─'*w}")

        # AI Recommendations
        recs = self._generate_recommendations(cons)
        print(f"{Back.BLACK}{Fore.WHITE}  🤖  AI RECOMMENDATIONS:")
        for r in recs:
            print(f"{Back.BLACK}{Fore.YELLOW}     {r}")

        print(f"{Back.BLACK}{Fore.CYAN}{'═'*w}{Style.RESET_ALL}\n")

    # ── JSON Report Save ───────────────────────────────────────────
    def _save_report(self) -> None:
        self._report_count += 1
        cons     = self._consolidated()
        weights  = self.rebalancer.current_weights()
        per_port = {}
        for name, (broker, tracker) in self.portfolios.items():
            per_port[name] = {
                "cash":          round(broker.cash, 2),
                "equity":        round(broker.equity, 2),
                "total_pnl":     round(broker.total_pnl, 2),
                "return_pct":    round(broker.return_pct, 4),
                "trades":        len(tracker.pnls),
                "win_rate":      round(tracker.win_rate, 4),
                "profit_factor": tracker.profit_factor,
                "sharpe":        tracker.sharpe,
                "max_drawdown":  round(tracker.max_drawdown, 4),
                "grade":         tracker.letter_grade(),
                "weight":        round(weights.get(name, 0), 4),
                "open_positions": {k: v for k, v in broker.positions.items() if v > 0},
            }

        report = {
            "report_id":   self._report_count,
            "timestamp":   datetime.now().isoformat(),
            "consolidated": cons,
            "portfolios":   per_port,
            "rebalances":   self.rebalancer.rebalance_count,
            "alerts":       self._alert_log[-20:],
            "recommendations": self._generate_recommendations(cons),
        }

        with open(self._report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

    # ── Main Update ────────────────────────────────────────────────
    async def update(self) -> None:
        now = time.time()
        if now - self._last_report < self.cfg.AI_REPORT_INTERVAL:
            return
        self._last_report = now
        self.print_dashboard()
        self._save_report()


# ═══════════════════════════════════════════════════════════════════════
# 17  SESSION SUMMARY
# ═══════════════════════════════════════════════════════════════════════

def print_final_summary(
    cfg:        MasterConfig,
    lt_broker:  PaperBroker,  lt_tracker:  PerformanceTracker,
    st_broker:  PaperBroker,  st_tracker:  PerformanceTracker,
    tr_broker:  PaperBroker,  tr_tracker:  PerformanceTracker,
    rebalancer: PortfolioRebalancer,
    darwin:     DarwinEngine,
) -> None:
    w      = 64
    total  = lt_broker.equity + st_broker.equity + tr_broker.equity
    total_pnl = lt_broker.total_pnl + st_broker.total_pnl + tr_broker.total_pnl
    ret    = (total - cfg.TOTAL_CAPITAL) / cfg.TOTAL_CAPITAL

    print(f"\n{Back.BLACK}{Fore.CYAN}{'═'*w}")
    print(f"{Back.BLACK}{Fore.WHITE}{'  📋  FINAL SESSION SUMMARY':^{w}}")
    print(f"{Back.BLACK}{Fore.CYAN}{'─'*w}")

    rows = [
        ("Start Capital",   f"₹{cfg.TOTAL_CAPITAL:>14,.2f}"),
        ("Final Equity",    f"₹{total:>14,.2f}"),
        ("Net PnL",         f"₹{total_pnl:>+14,.2f}"),
        ("Total Return",    f"{ret:>+.2%}"),
        ("Rebalances",      str(rebalancer.rebalance_count)),
        ("DNA Generation",  str(darwin.generation - 1)),
    ]
    for label, val in rows:
        col = Fore.GREEN if "+" in val and "₹" in val else Fore.WHITE
        print(f"{Back.BLACK}{col}  {label:<18}: {val}")

    print(f"{Back.BLACK}{Fore.CYAN}{'─'*w}")
    for name, broker, tracker in [
        ("LONG-TERM",  lt_broker,  lt_tracker),
        ("SHORT-TERM", st_broker,  st_tracker),
        ("TRADING",    tr_broker,  tr_tracker),
    ]:
        pc = Fore.GREEN if broker.return_pct >= 0 else Fore.RED
        print(f"{Back.BLACK}{Fore.WHITE}  {name:<12}  "
              f"Cash ₹{broker.cash:>12,.2f}  "
              f"Ret {pc}{broker.return_pct:>+.2%}{Fore.WHITE}  "
              f"Grade {tracker.letter_grade()}  "
              f"Trades {len(tracker.pnls)}")

    print(f"{Back.BLACK}{Fore.CYAN}{'═'*w}{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}  📁 Logs → ./{cfg.LOG_DIR}/\n")


# ═══════════════════════════════════════════════════════════════════════
# 18  MASTER ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════

async def orchestrate(
    cfg:        MasterConfig,
    lt_broker:  PaperBroker,  lt_tracker:  PerformanceTracker,
    st_broker:  PaperBroker,  st_tracker:  PerformanceTracker,
    tr_broker:  PaperBroker,  tr_tracker:  PerformanceTracker,
    darwin:     DarwinEngine,
) -> None:
    """Runs all three portfolio loops + rebalancer + AI tracker concurrently."""

    # Shared infrastructure
    quant      = QuantMath()
    sniper     = SniperEngine()
    mc         = MonteCarloEngine(simulations=1000)
    feed       = LiveDataFeed(throttle_secs=cfg.TR_FETCH_THROTTLE)
    tr_guard   = RiskGuard(cfg, tr_tracker)
    rebalancer = PortfolioRebalancer(cfg, lt_broker, st_broker, tr_broker)
    ai_tracker = AIPortfolioTracker(
        cfg,
        lt_broker, lt_tracker,
        st_broker, st_tracker,
        tr_broker, tr_tracker,
        rebalancer,
    )

    # Per-portfolio loggers
    lt_log = TradeLogger(cfg.LOG_DIR, "long_term")
    st_log = TradeLogger(cfg.LOG_DIR, "short_term")
    tr_log = TradeLogger(cfg.LOG_DIR, "trading")

    lt_port = LongTermPortfolio(cfg, quant, feed, lt_broker, lt_tracker, lt_log)
    st_port = ShortTermPortfolio(cfg, quant, sniper, mc, feed, st_broker,
                                  st_tracker, st_log, darwin)
    tr_port = TradingPortfolio(cfg, darwin, quant, sniper, mc, feed,
                                tr_broker, tr_tracker, tr_log, tr_guard)

    # Initial AI dashboard
    ai_tracker.print_dashboard()

    tick = 0
    while True:
        try:
            tick_start = time.time()
            tick      += 1

            # ── Trading portfolio — every tick ──────────────────
            await tr_port.run_tick()

            # ── Short-term — every 30 minutes ──────────────────
            await st_port.evaluate()

            # ── Long-term — every hour ──────────────────────────
            await lt_port.evaluate()

            # ── Rebalancer — every 24 hours ─────────────────────
            rebalancer.check_and_rebalance()

            # ── AI Tracker report — every AI_REPORT_INTERVAL ───
            await ai_tracker.update()

            # ── Heartbeat every 50 ticks ────────────────────────
            if tick % 50 == 0:
                print(f"\n{Fore.WHITE}{'─'*40}")
                print(lt_broker.summary_line())
                print(st_broker.summary_line())
                print(tr_broker.summary_line())
                total_eq = lt_broker.equity + st_broker.equity + tr_broker.equity
                total_ret = (total_eq - cfg.TOTAL_CAPITAL) / cfg.TOTAL_CAPITAL
                rc = Fore.GREEN if total_ret >= 0 else Fore.RED
                print(f"{rc}  TOTAL EQUITY: ₹{total_eq:,.2f}  "
                      f"({total_ret:>+.2%}){Fore.RESET}")
                print(f"{Fore.WHITE}{'─'*40}\n")

            # ── Precise tick timing ──────────────────────────────
            elapsed   = time.time() - tick_start
            sleep_for = max(0.5, cfg.TR_LOOP_INTERVAL - elapsed)
            await asyncio.sleep(sleep_for)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"{Fore.RED}  ❌ Orchestrator error: {e}")
            traceback.print_exc()
            await asyncio.sleep(5)


# ═══════════════════════════════════════════════════════════════════════
# 19  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    cfg = MasterConfig()

    # ── Allocate capital to each portfolio ──────────────────────────
    lt_capital = cfg.TOTAL_CAPITAL * cfg.WEIGHT_LONG
    st_capital = cfg.TOTAL_CAPITAL * cfg.WEIGHT_SHORT
    tr_capital = cfg.TOTAL_CAPITAL * cfg.WEIGHT_TRADING

    lt_broker  = PaperBroker("LONG",    lt_capital)
    st_broker  = PaperBroker("SHORT",   st_capital)
    tr_broker  = PaperBroker("TRADING", tr_capital)

    lt_tracker = PerformanceTracker("LONG")
    st_tracker = PerformanceTracker("SHORT")
    tr_tracker = PerformanceTracker("TRADING")

    darwin = DarwinEngine()

    # ── Banner ──────────────────────────────────────────────────────
    w = 64
    print(f"\n{Back.BLACK}{Fore.CYAN}{'═'*w}")
    print(f"{Back.BLACK}{Fore.WHITE}{'  🚀  GOD MODE COMPLETE PORTFOLIO SYSTEM':^{w}}")
    print(f"{Back.BLACK}{Fore.CYAN}{'─'*w}")
    print(f"{Back.BLACK}{Fore.WHITE}  Total Capital  : ₹{cfg.TOTAL_CAPITAL:>14,.2f}")
    print(f"{Back.BLACK}{Fore.WHITE}  Long-Term (60%): ₹{lt_capital:>14,.2f}  "
          f"│  {len(cfg.LT_WATCHLIST)} stocks")
    print(f"{Back.BLACK}{Fore.WHITE}  Short-Term(25%): ₹{st_capital:>14,.2f}  "
          f"│  {len(cfg.ST_WATCHLIST)} stocks")
    print(f"{Back.BLACK}{Fore.WHITE}  Trading   (15%): ₹{tr_capital:>14,.2f}  "
          f"│  {cfg.TR_SYMBOL}")
    print(f"{Back.BLACK}{Fore.CYAN}{'─'*w}")
    print(f"{Back.BLACK}{Fore.WHITE}  Press Ctrl+C to stop and view final report")
    print(f"{Back.BLACK}{Fore.CYAN}{'═'*w}{Style.RESET_ALL}\n")

    try:
        asyncio.run(
            orchestrate(
                cfg,
                lt_broker, lt_tracker,
                st_broker, st_tracker,
                tr_broker, tr_tracker,
                darwin,
            )
        )

    except KeyboardInterrupt:
        # Force-close all open positions
        print(f"\n{Fore.YELLOW}  Closing all positions...")
        feed     = LiveDataFeed()
        price_map: Dict[str, float] = {}
        for sym in (cfg.LT_WATCHLIST + cfg.ST_WATCHLIST + [cfg.TR_SYMBOL]):
            price_map[sym] = feed.last_price(sym) or 0.0

        for broker in (lt_broker, st_broker, tr_broker):
            broker.force_close_all(price_map)

        # Update trackers for forced closes
        for broker, tracker in [
            (lt_broker, lt_tracker),
            (st_broker, st_tracker),
            (tr_broker, tr_tracker),
        ]:
            if broker.last_pnl is not None:
                tracker.record(broker.last_pnl, broker.equity)

        print_final_summary(
            cfg,
            lt_broker, lt_tracker,
            st_broker, st_tracker,
            tr_broker, tr_tracker,
            PortfolioRebalancer(cfg, lt_broker, st_broker, tr_broker),
            darwin,
        )

    except Exception as e:
        print(f"{Fore.RED}\n  💥 Fatal: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
