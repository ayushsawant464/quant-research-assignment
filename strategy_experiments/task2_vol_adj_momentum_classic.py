"""
Task 2: Classic Volatility-Adjusted Momentum Strategy (Single Lookback L=126d).
Maximum CAGR variant on the training evaluation sample (Mar 2022 - Jun 2024).

Backtest Metrics:
  CAGR: 70.14% | Sharpe: 2.058 | MaxDD: -19.86% | Calmar: 3.531 | Trades: 129
"""
import numpy as np
import pandas as pd

PARAMS = {
    'n_stocks': 10,
    'lookback': 126,
    'min_turnover': 1e8,
    'max_drop_filter': -0.35
}

def orders(date, hist, portfolio, params, state):
    c = hist['close']
    vol = hist['volume']
    if len(c) < 2 or c.index[-1].month == c.index[-2].month:
        return []

    tail_c = c.iloc[-300:]
    tail_vol = vol.iloc[-300:]

    turnover = (tail_c * tail_vol).rolling(60, min_periods=40).median().iloc[-1]
    recent_drops = tail_c.iloc[-30:].pct_change().min()
    ok_anomaly = recent_drops > params.get('max_drop_filter', -0.35)

    lb = params['lookback']
    ret = tail_c.iloc[-1] / tail_c.iloc[-1 - lb] - 1
    vol_ann = tail_c.pct_change().iloc[-lb:].std() * np.sqrt(252)
    score = ret / (vol_ann + 1e-4)

    valid = (turnover >= params['min_turnover']) & ok_anomaly & score.notna() & (ret > 0)
    top_candidates = score[valid].sort_values(ascending=False)
    n_target = params['n_stocks']
    top = list(top_candidates.index[:n_target])

    out = []
    current_positions = portfolio['positions']
    for s in current_positions:
        if s not in top:
            out.append({'symbol': s, 'side': 'sell', 'type': 'market'})

    w = min(1.0 / n_target, 0.15)
    for s in top:
        if s not in current_positions:
            out.append({'symbol': s, 'side': 'buy', 'type': 'market', 'weight': w, 'max_positions': n_target})

    return out
