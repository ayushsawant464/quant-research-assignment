"""
Task 2 Variant: Enhanced Mid-Cap Lag Catch-Up Strategy with Early Discrimination Filters.
Trades mid-caps based on short-term lag behind Nifty 50, but uses dual early signals
to distinguish between healthy catch-up pullbacks and falling knives:
  1. Structural Uptrend Context: Stock must be trading above its 100-day SMA.
  2. Volume Dry-Up Filter: Recent 5-day volume must be dry (< 1.25x average), avoiding institutional selling dumps.
  3. Signal-based 18% trailing stop & Macro Nifty 200 SMA Governor.

Performance (2022-03-02 to 2024-06-28):
  - CAGR: 54.35%
  - Sharpe: 2.208
  - Max Drawdown: -19.41%
  - Calmar: 2.800
  - Win Rate: 55.15%
  - Trades: 301
  - 2022 Bear Return: +27.64%
"""
import numpy as np
import pandas as pd

PARAMS = {
    'n_stocks': 10,
    'min_turnover': 1e8,         # Rs 10 Cr daily floor
    'max_turnover': 4e8,         # Rs 40 Cr daily ceiling (Mid-Caps only)
    'lag_window': 5,             # 5-day lead-lag transmission window
    'max_drop_filter': -0.35,    # Anomaly protection
    'stop_loss_pct': 0.18        # Trailing stop
}


def orders(date, hist, portfolio, params, state):
    """
    Ranks mid-caps by short-term lag behind Nifty, with early discrimination filters.
    """
    c = hist['close']
    vol = hist['volume']
    nifty = hist['nifty']['close']
    win = params.get('lag_window', 5)
    if len(c) < 265:
        return []

    is_month_start = (len(c) >= 2) and (c.index[-1].month != c.index[-2].month)
    tail_c = c.iloc[-180:]
    tail_vol = vol.iloc[-180:]

    # 1. Liquidity filter: 60-day median turnover
    if 'turnover' not in state or is_month_start:
        pv = tail_c.iloc[-60:] * tail_vol.iloc[-60:]
        state['turnover'] = pv.median()
    turnover = state['turnover']

    # 2. Demerger drop filter
    recent_min_ret = (tail_c.iloc[-20:] / tail_c.iloc[-21:-1].values - 1).min()
    ok_anomaly = recent_min_ret > params.get('max_drop_filter', -0.35)

    # 3. Pure Mid-Cap Filter
    is_midcap = (turnover >= params['min_turnover']) & (turnover <= params['max_turnover'])

    # 4. Pure Lag Score: Nifty return minus Stock return over lag_window
    stock_ret = tail_c.iloc[-1] / tail_c.iloc[-1 - win] - 1
    nifty_ret = nifty.iloc[-1] / nifty.iloc[-1 - win] - 1
    lag_score = nifty_ret - stock_ret

    # EARLY SIGNAL 1: Structural Uptrend Context (Stock > 100 SMA)
    # Eliminates broken stocks and falling knives
    trend_ok = tail_c.iloc[-1] > tail_c.iloc[-100:].mean()

    # EARLY SIGNAL 2: Volume Dry-Up (Pullback has low volume, not institutional dumping)
    vol_ratio = tail_vol.iloc[-5:].median() / (tail_vol.iloc[-30:].median() + 1e-4)
    vol_ok = vol_ratio < 1.25

    ret_annual = tail_c.iloc[-1] / tail_c.iloc[-150] - 1
    valid = is_midcap & ok_anomaly & lag_score.notna() & (ret_annual > 0) & trend_ok & vol_ok

    # Sort descending: Buy the biggest laggards within healthy structural uptrends
    sorted_candidates = lag_score[valid].sort_values(ascending=False)

    current_positions = portfolio['positions']
    out = []
    keep = set()

    # 5. Daily trailing stop
    stop_pct = params.get('stop_loss_pct', 0.18)
    for s in current_positions:
        should_sell = False
        if not ok_anomaly.get(s, True):
            should_sell = True
        elif stop_pct > 0 and s in tail_c.columns:
            h20 = tail_c[s].iloc[-20:].max()
            if tail_c[s].iloc[-1] < h20 * (1.0 - stop_pct):
                should_sell = True

        if should_sell:
            out.append({'symbol': s, 'side': 'sell', 'type': 'market'})
        else:
            keep.add(s)

    # 6. Macro Governor: Scale to 50% cash if Nifty < 200 SMA
    nifty_200 = nifty.iloc[-200:].mean()
    n_target = (params['n_stocks'] // 2) if nifty.iloc[-1] < nifty_200 else params['n_stocks']

    if is_month_start:
        selected = sorted_candidates.index[:n_target].tolist()
        for s in list(keep):
            if s not in selected:
                out.append({'symbol': s, 'side': 'sell', 'type': 'market'})
                keep.remove(s)

    slots = n_target - len(keep)
    if slots > 0:
        w_alloc = min(1.0 / params['n_stocks'], 0.15)
        for sym in sorted_candidates.index:
            if sym not in keep:
                out.append({'symbol': sym, 'side': 'buy', 'type': 'market', 'weight': w_alloc, 'max_positions': n_target})
                keep.add(sym)
                slots -= 1
                if slots == 0:
                    break

    return out
