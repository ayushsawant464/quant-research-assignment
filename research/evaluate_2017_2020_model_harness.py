import os, sys
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar

# Import harness utilities directly
import harness_public as harness

# Load Bars and Expiries
bars_full = harness.load_bars('data/nifty50_15min_full_2017-04-03_2026-10-26.csv')
expiries_full = harness.load_expiries('data/nifty_monthly_expiries_2017-01_2026-10.csv')

def fit_and_run(train_end='2020-12-31', test_start='2022-02-01', title='Train 2017-2020'):
    print("\n" + "="*80)
    print(f"CALIBRATION: {title} (Train <= {train_end}, Test >= {test_start})")
    print("="*80)

    # 1. Feature Engineering
    c = bars_full['close']
    h = bars_full['high']
    l = bars_full['low']
    N = len(bars_full)

    tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=20, adjust=False).mean() + 1e-4

    h50 = h.rolling(50).max().shift(1)
    l25 = l.rolling(25).min().shift(1)
    e20 = c.ewm(span=20, adjust=False).mean()
    e50 = c.ewm(span=50, adjust=False).mean()
    e_trend = c.ewm(span=150, adjust=False).mean()

    brk_l = ((c - h50) / atr).values
    brk_s = ((c - l25) / atr).values
    trend_fast = ((e20 - e50) / atr).values
    trend_macro = ((c - e_trend) / atr).values
    ret_1 = (100.0 * (c / c.shift(1) - 1.0)).values
    ret_3 = (100.0 * (c / c.shift(3) - 1.0)).values
    ret_10 = (100.0 * (c / c.shift(10) - 1.0)).values
    rng_norm = ((h - l) / atr).values

    raw_features = np.column_stack([
        brk_l, brk_s, trend_fast, trend_macro, ret_1, ret_3, ret_10, rng_norm
    ])

    fwd_ret_5 = (100.0 * (c.shift(-5) / c - 1.0)).values

    # Train Split
    train_mask = (bars_full.index <= train_end)
    train_idx = np.where(train_mask)[0]
    valid_train = train_idx[~np.isnan(raw_features[train_idx]).any(axis=1) & ~np.isnan(fwd_ret_5[train_idx])]

    # Target Dynamic Kurtosis
    y_raw_tr = fwd_ret_5[valid_train]
    med_val = np.median(y_raw_tr)
    mad_val = stats.median_abs_deviation(y_raw_tr)

    def kurt_obj(m):
        clipped = np.clip(y_raw_tr, med_val - m * mad_val, med_val + m * mad_val)
        return (pd.Series(clipped).kurtosis() - 3.0)**2

    res = minimize_scalar(kurt_obj, bounds=(1.0, 15.0), method='bounded')
    opt_m = res.x
    target_lower = med_val - opt_m * mad_val
    target_upper = med_val + opt_m * mad_val
    y_clipped = np.clip(y_raw_tr, target_lower, target_upper)
    y_train = y_clipped - np.mean(y_clipped)

    print(f"Optimal MAD multiplier: {opt_m:.3f} -> Kurtosis Bounds: [{target_lower:.3f}, {target_upper:.3f}]")

    # Feature Winsorization and Scaling strictly on training data
    feat_bounds = []
    feat_means = []
    feat_stds = []
    X_train_raw = raw_features[valid_train]
    X_train_scaled = np.zeros_like(X_train_raw)

    for j in range(8):
        lb = np.percentile(X_train_raw[:, j], 0.1)
        ub = np.percentile(X_train_raw[:, j], 99.9)
        feat_bounds.append((lb, ub))
        clipped_col = np.clip(X_train_raw[:, j], lb, ub)
        m = np.mean(clipped_col)
        s = np.std(clipped_col) + 1e-8
        feat_means.append(m)
        feat_stds.append(s)
        X_train_scaled[:, j] = (clipped_col - m) / s

    # 2-Component PLS in pure NumPy
    X = X_train_scaled.copy()
    Y = y_train.copy().reshape(-1, 1)
    n_components = 2
    n_features = 8
    W = np.zeros((n_features, n_components))
    P = np.zeros((n_features, n_components))
    Q = np.zeros((1, n_components))

    for a in range(n_components):
        w = X.T @ Y
        w = w / (np.linalg.norm(w) + 1e-12)
        t = X @ w
        norm_t = np.linalg.norm(t) + 1e-12
        p = (X.T @ t) / (norm_t**2)
        q = (Y.T @ t) / (norm_t**2)
        X = X - (t @ p.T)
        Y = Y - (t @ q.T)
        W[:, a] = w.ravel()
        P[:, a] = p.ravel()
        Q[:, a] = q.ravel()

    beta_pls = (W @ np.linalg.pinv(P.T @ W) @ Q.T).ravel()
    print("PLS Beta Weights:", np.round(beta_pls, 6))

    # Modulator statistics strictly on training data
    m1_tr = np.nan_to_num(X_train_raw[:, 0] * X_train_raw[:, 7])
    m1_mean, m1_std = np.mean(m1_tr), np.std(m1_tr) + 1e-8

    relu_r1 = np.maximum(0.0, np.nan_to_num(X_train_raw[:, 4]))
    relu_r3 = np.maximum(0.0, np.nan_to_num(X_train_raw[:, 5]))
    m2_tr = 0.5 * (relu_r1**2) * (relu_r3**2)
    m2_mean, m2_std = np.mean(m2_tr), np.std(m2_tr) + 1e-8

    tf_tr = np.nan_to_num(X_train_raw[:, 2])
    tm_tr = np.nan_to_num(X_train_raw[:, 3])
    m3_tr = (np.sign(tf_tr) * (tf_tr**2)) - (np.sign(tm_tr) * (tm_tr**2))
    m3_mean, m3_std = np.mean(m3_tr), np.std(m3_tr) + 1e-8

    MOD1_C = -0.46857
    MOD2_C = -0.15092
    MOD3_C = 0.06037
    ASYM_POS_SCALE = 1.1

    # Project globally
    X_full_scaled = np.zeros_like(raw_features)
    for j in range(8):
        lb, ub = feat_bounds[j]
        clipped_col = np.clip(np.nan_to_num(raw_features[:, j]), lb, ub)
        X_full_scaled[:, j] = (clipped_col - feat_means[j]) / feat_stds[j]

    base_pred = X_full_scaled @ beta_pls

    m1_raw = np.nan_to_num(raw_features[:, 0] * raw_features[:, 7])
    m1 = (m1_raw - m1_mean) / m1_std

    relu_r1 = np.maximum(0.0, np.nan_to_num(raw_features[:, 4]))
    relu_r3 = np.maximum(0.0, np.nan_to_num(raw_features[:, 5]))
    m2_raw = 0.5 * (relu_r1**2) * (relu_r3**2)
    m2 = (m2_raw - m2_mean) / m2_std

    tf = np.nan_to_num(raw_features[:, 2])
    tm = np.nan_to_num(raw_features[:, 3])
    m3_raw = (np.sign(tf) * (tf**2)) - (np.sign(tm) * (tm**2))
    m3 = (m3_raw - m3_mean) / m3_std

    adj_pred = base_pred * (1.0 + MOD1_C * m1) * (1.0 + MOD2_C * m2) * (1.0 + MOD3_C * m3)
    pos_mask = adj_pred > 0
    adj_pred[pos_mask] = adj_pred[pos_mask] * ASYM_POS_SCALE
    final_pred = np.clip(adj_pred, target_lower, target_upper)

    # Position function for harness
    def gen_positions(allow_short=1, thresh=0.05, stall_limit=6):
        pos_arr = np.zeros(N)
        cur = 0.0
        stall = 0
        entry_px = 0.0
        cv = c.values
        h50v = h50.values
        l25v = l25.values
        etrendv = e_trend.values

        for i in range(N):
            if np.isnan(h50v[i]) or np.isnan(etrendv[i]) or np.isnan(l25v[i]):
                pos_arr[i] = 0.0
                continue
            p_val = final_pred[i]

            if cur == 1.0:
                if cv[i] <= entry_px: stall += 1
                else: stall = 0
                if p_val < -thresh * 0.5 or cv[i] < etrendv[i] or (stall_limit > 0 and stall >= stall_limit):
                    cur = 0.0
                    stall = 0
            elif cur == -1.0:
                if cv[i] >= entry_px: stall += 1
                else: stall = 0
                if p_val > thresh * 0.5 or cv[i] > etrendv[i] or (stall_limit > 0 and stall >= stall_limit):
                    cur = 0.0
                    stall = 0

            if cur == 0.0:
                if p_val > thresh and cv[i] > h50v[i] and cv[i] > etrendv[i]:
                    cur = 1.0
                    entry_px = cv[i]
                    stall = 0
                elif allow_short and p_val < -thresh and cv[i] < l25v[i] and cv[i] < etrendv[i]:
                    cur = -1.0
                    entry_px = cv[i]
                    stall = 0
            pos_arr[i] = cur
        return pd.Series(pos_arr, index=bars_full.index)

    # Run for both Long/Short and Long-Only
    for mode_name, allow_short in [('Long/Short (allow_short=1)', 1), ('Long-Only (allow_short=0)', 0)]:
        print(f"\n>>> Running Harness for {mode_name} <<<")
        want = gen_positions(allow_short=allow_short)
        
        # Backtest through official harness engine
        bt_res = harness.task1_backtest(bars_full, want, expiries_full)
        
        # 1. In-Sample
        is_stats, _ = harness.task1_stats(bt_res, end=train_end)
        harness.print_stats(f"IN-SAMPLE (2017 to {train_end}) [{mode_name}]", is_stats)

        # 2. Out-of-Sample (2022 to 2026)
        oos_stats, _ = harness.task1_stats(bt_res, start=test_start)
        harness.print_stats(f"OUT-OF-SAMPLE ({test_start} to 2026-10-26) [{mode_name}]", oos_stats)

        # 3. Full Horizon (2017 to 2026)
        full_stats, eq_full = harness.task1_stats(bt_res)
        harness.print_stats(f"FULL HORIZON (2017 to 2026) [{mode_name}]", full_stats)

# Run 1: Trained strictly 2017 to 2020 (end of 2020)
fit_and_run(train_end='2020-12-31', test_start='2022-02-01', title='Train 2017-2020 Full')

# Run 2: Trained strictly 2017 to Jan 2020 (Pre-COVID only)
fit_and_run(train_end='2020-01-31', test_start='2022-02-01', title='Train 2017-Jan 2020 Pre-COVID')
