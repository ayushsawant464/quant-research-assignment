"""
Task 2 Variant: Granular Selective Persistence Engine (Sub-15% Max DD Mandate).
Architecture:
  - 12 stocks (8.33% position weight each) to suppress single-name idiosyncratic shocks.
  - Rs 10 Cr to Rs 25 Cr agile mid-cap corridor to avoid top-heavy drawdown contagion.
  - Multi-Scale Harmonic EMA Ribbon (EMA20 > EMA50 with forward slopes s20>0, s50>0, s100>0).
  - Anti-Parabolic Entry Filter (ret_20d < 60% and dist_50 < 35%).
  - 18% Trailing Stop from 20-day high + Climax Exhaustion Exit.
  - Breadth-Gated Macro Bear Governor.
  - Persistence Rebalance: Positions only rotated out if they fall out of top 25 momentum ranks.
"""
import numpy as np
import pandas as pd

PARAMS = {
    'n_stocks': 12,              # 12 stocks (8.33% weight each)
    'min_turnover': 1e8,         # Rs 10 Cr daily liquidity floor
    'max_turnover': 2.5e8,       # Rs 25 Cr agile mid-cap ceiling
    'max_drop_filter': -0.35,    # Anomaly crash protection
    'stop_loss_pct': 0.18,       # 18% trailing stop
    'corr_thresh': 0.65          # Max 2 stocks per industry/factor cluster
}


def orders(date, hist, portfolio, params, state):
    c = hist['close']
    vol = hist['volume']
    nifty = hist['nifty']['close']
    if len(c) < 265:
        return []

    is_month_start = (len(c) >= 2) and (c.index[-1].month != c.index[-2].month)
    tail_c = c.iloc[-300:]
    tail_vol = vol.iloc[-300:]

    if 'turnover' not in state or is_month_start:
        state['turnover'] = (tail_c.iloc[-60:] * tail_vol.iloc[-60:]).median()
    turnover = state['turnover']

    recent_min_ret = (tail_c.iloc[-20:] / tail_c.iloc[-21:-1].values - 1).min()
    ok_anomaly = recent_min_ret > params.get('max_drop_filter', -0.35)

    e20 = tail_c.ewm(span=20, adjust=False).mean()
    e50 = tail_c.ewm(span=50, adjust=False).mean()
    e100 = tail_c.ewm(span=100, adjust=False).mean()

    s20 = e20.iloc[-1] - e20.iloc[-2]
    s50 = e50.iloc[-1] - e50.iloc[-2]
    s100 = e100.iloc[-1] - e100.iloc[-2]

    ema_aligned = (tail_c.iloc[-1] > e20.iloc[-1]) & (e20.iloc[-1] > e50.iloc[-1]) & (s20 > 0) & (s50 > 0) & (s100 > 0)

    scores = []
    for lb in [50, 90, 180, 252]:
        r = tail_c.iloc[-1] / tail_c.iloc[-1 - lb] - 1
        v = tail_c.iloc[-lb:].pct_change().std() * np.sqrt(252)
        scores.append((r / (v + 1e-4)).rank(pct=True))
    score = pd.concat(scores, axis=1).mean(axis=1)
    ret_annual = tail_c.iloc[-1] / tail_c.iloc[-253] - 1

    min_to = params.get('min_turnover', 1e8)
    max_to = params.get('max_turnover', 2.5e8)
    is_midcap = (turnover >= min_to) & (turnover <= max_to)

    # Anti-Parabolic Entry Filter
    ret_20d = tail_c.iloc[-1] / tail_c.iloc[-21] - 1.0
    dist_50_cand = tail_c.iloc[-1] / e50.iloc[-1] - 1.0
    not_overextended = (ret_20d < 0.60) & (dist_50_cand < 0.35)

    valid = is_midcap & ok_anomaly & ema_aligned & score.notna() & (ret_annual > 0) & not_overextended
    sorted_candidates = score[valid].sort_values(ascending=False)

    current_positions = portfolio['positions']
    out = []
    keep = set()

    nifty_200_sma = nifty.iloc[-200:].mean()
    breadth = (tail_c.iloc[-1] > e20.iloc[-1]).mean()
    breadth_thrust = breadth > 0.55
    nifty_bear = (nifty.iloc[-1] < nifty_200_sma) and (not breadth_thrust)

    stop_pct = params.get('stop_loss_pct', 0.18)
    vol_sma20 = tail_vol.iloc[-20:].mean()
    vol_ratio = tail_vol.iloc[-1] / (vol_sma20 + 1e-4)
    dist_50 = tail_c.iloc[-1] / e50.iloc[-1] - 1.0
    daily_ret = tail_c.iloc[-1] / tail_c.iloc[-2] - 1.0

    for s in current_positions:
        should_sell = False
        if not ok_anomaly.get(s, True):
            should_sell = True
        else:
            curr_p = tail_c[s].iloc[-1]
            h20 = tail_c[s].iloc[-20:].max()
            if curr_p < h20 * (1.0 - stop_pct):
                should_sell = True
            elif (vol_ratio.get(s, 0) > 3.0) and (dist_50.get(s, 0) > 0.30) and (daily_ret.get(s, 0) < -0.04):
                should_sell = True
        if should_sell:
            out.append({'symbol': s, 'side': 'sell', 'type': 'market'})
        else:
            keep.add(s)

    target_n = (params['n_stocks'] // 2) if nifty_bear else params['n_stocks']

    # Persistence Mode: Only rotate out if dropped out of top 25 candidates
    if is_month_start:
        top25 = set(sorted_candidates.index[:25])
        for s in list(keep):
            if s not in top25:
                out.append({'symbol': s, 'side': 'sell', 'type': 'market'})
                keep.remove(s)

    corr_thresh = params.get('corr_thresh', 0.65)
    slots = target_n - len(keep)
    if slots > 0 and len(sorted_candidates) > 0:
        ret_60 = tail_c.iloc[-60:].pct_change().dropna()
        w = min(1.0 / params['n_stocks'], 0.15)
        for s in sorted_candidates.index:
            if s in keep:
                continue
            if len(keep) > 0:
                corrs = ret_60[list(keep)].apply(lambda col: ret_60[s].corr(col))
                n_high = (corrs > corr_thresh).sum()
            else:
                n_high = 0
            if n_high < 2:
                out.append({'symbol': s, 'side': 'buy', 'type': 'market', 'weight': w, 'max_positions': target_n})
                keep.add(s)
                slots -= 1
                if slots == 0:
                    break
    return out
