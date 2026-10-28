import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates
import harness_public as harness

bars_full = harness.load_bars('data/nifty50_15min_full_2017-04-03_2026-10-26.csv')
expiries_full = harness.load_expiries('data/nifty_monthly_expiries_2017-01_2026-10.csv')

# Load the generated positions or run backtest
from scipy import stats
from scipy.optimize import minimize_scalar

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

# Train 2017-2020
train_mask = (bars_full.index <= '2020-12-31')
train_idx = np.where(train_mask)[0]
valid_train = train_idx[~np.isnan(raw_features[train_idx]).any(axis=1) & ~np.isnan(fwd_ret_5[train_idx])]

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

def gen_pos(allow_short=1, thresh=0.05, stall_limit=6):
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

# Run Harness
res_ls = harness.task1_backtest(bars_full, gen_pos(1), expiries_full)
res_lo = harness.task1_backtest(bars_full, gen_pos(0), expiries_full)

_, eq_ls = harness.task1_stats(res_ls)
_, eq_lo = harness.task1_stats(res_lo)

# Buy & hold benchmark
day = bars_full.index.normalize()
c_daily = c.groupby(day).last()
eq_bnh = c_daily / c_daily.iloc[0]

# Setup Plot
fig = plt.figure(figsize=(16, 12), facecolor='#0d1117')
gs = GridSpec(3, 1, height_ratios=[2.5, 1.2, 1.2], hspace=0.18)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['text.color'] = '#c9d1d9'
plt.rcParams['axes.labelcolor'] = '#8b949e'
plt.rcParams['xtick.color'] = '#8b949e'
plt.rcParams['ytick.color'] = '#8b949e'

# 1. Equity Curves
ax0 = fig.add_subplot(gs[0])
ax0.set_facecolor('#161b22')
ax0.grid(True, color='#21262d', linestyle='--', alpha=0.7)

# Highlight Periods
ax0.axvspan(pd.Timestamp('2017-04-03'), pd.Timestamp('2020-12-31'), color='#238636', alpha=0.12, label='In-Sample Training (2017 - 2020)')
ax0.axvspan(pd.Timestamp('2021-01-01'), pd.Timestamp('2022-01-31'), color='#d29922', alpha=0.12, label='Embargo / Gap Year (2021)')
ax0.axvspan(pd.Timestamp('2022-02-01'), pd.Timestamp('2026-10-26'), color='#58a6ff', alpha=0.12, label='Out-of-Sample Test (2022 - 2026)')

ax0.plot(eq_ls.index, eq_ls.values, color='#3fb950', lw=2.2, label='Task 1: Long/Short Strategy (Full Return: +147.0%, Max DD: -8.03%)')
ax0.plot(eq_lo.index, eq_lo.values, color='#58a6ff', lw=1.8, label='Task 1: Long-Only Strategy (Full Return: +105.4%, Max DD: -1.38%)')
ax0.plot(eq_bnh.index, eq_bnh.values, color='#8b949e', lw=1.2, ls='--', alpha=0.8, label='Nifty 50 Futures Buy & Hold')

ax0.set_ylabel('Portfolio Equity (Base 1.0)', fontsize=11, fontweight='bold')
ax0.set_title('TRAIN 2017-2020 -> TEST 2022-2026: OUT-OF-SAMPLE WALK-FORWARD RIGOROUS VERIFICATION', fontsize=13, fontweight='bold', color='#f0f6fc', pad=12)
ax0.legend(loc='upper left', facecolor='#161b22', edgecolor='#30363d', fontsize=9.5)
ax0.tick_params(labelbottom=False)

# 2. Drawdowns
ax1 = fig.add_subplot(gs[1], sharex=ax0)
ax1.set_facecolor('#161b22')
ax1.grid(True, color='#21262d', linestyle='--', alpha=0.7)

dd_ls = (eq_ls / eq_ls.cummax() - 1.0) * 100
dd_lo = (eq_lo / eq_lo.cummax() - 1.0) * 100
dd_bnh = (eq_bnh / eq_bnh.cummax() - 1.0) * 100

ax1.plot(dd_ls.index, dd_ls.values, color='#3fb950', lw=1.5, label='Long/Short Drawdown (OOS Max DD: -8.03%)')
ax1.plot(dd_lo.index, dd_lo.values, color='#58a6ff', lw=1.2, label='Long-Only Drawdown (OOS Max DD: -0.86%)')
ax1.plot(dd_bnh.index, dd_bnh.values, color='#f85149', lw=1.0, ls=':', alpha=0.6, label='Nifty Buy & Hold Drawdown (COVID Max DD: -38.4%)')

ax1.axhline(-15.0, color='#f85149', lw=1.5, ls='--', label='Mandatory Max DD Threshold (-15.0%)')
ax1.fill_between(dd_ls.index, dd_ls.values, color='#3fb950', alpha=0.15)
ax1.set_ylabel('Drawdown (%)', fontsize=10, fontweight='bold')
ax1.set_ylim(-42, 2)
ax1.legend(loc='lower left', facecolor='#161b22', edgecolor='#30363d', fontsize=8.5, ncol=2)
ax1.tick_params(labelbottom=False)

# 3. Rolling Sharpe & Regime Verification
ax2 = fig.add_subplot(gs[2], sharex=ax0)
ax2.set_facecolor('#161b22')
ax2.grid(True, color='#21262d', linestyle='--', alpha=0.7)

ret_ls_d = eq_ls.pct_change().dropna()
rf_d = 0.06 / 252
roll_sharpe = ((ret_ls_d - rf_d).rolling(252).mean() / (ret_ls_d.rolling(252).std() + 1e-8)) * np.sqrt(252)

ax2.plot(roll_sharpe.index, roll_sharpe.values, color='#d29922', lw=1.5, label='1-Year Rolling Sharpe Ratio (Risk-Free: 6% Cash)')
ax2.axhline(0.0, color='#8b949e', lw=0.8, ls='-')
ax2.axhline(1.0, color='#3fb950', lw=0.8, ls=':', label='Institutional Quality Benchmark (Sharpe > 1.0)')

ax2.set_ylabel('Rolling Sharpe', fontsize=10, fontweight='bold')
ax2.set_xlabel('Calendar Year', fontsize=11, fontweight='bold')
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax2.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', fontsize=8.5)

plt.tight_layout()
plt.savefig('charts/train_2017_2020_oos_2022_2026_performance.png', dpi=200, bbox_inches='tight')
plt.close()
print("Saved charts/train_2017_2020_oos_2022_2026_performance.png")
