import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as anim
from matplotlib.gridspec import GridSpec

# Ensure output directory
os.makedirs('charts', exist_ok=True)

# 1. Load Data
print("Loading Task 1 dataset...")
df = pd.read_csv('data/nifty50_15min_train_2017-04-03_2022-01-31.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

# Select COVID Crash Window: 2020-02-17 to 2020-03-27 (~600 bars)
mask = (df['datetime'] >= '2020-02-17 09:15:00') & (df['datetime'] <= '2020-03-27 15:15:00')
# To compute rolling features properly, take window with 200 bars warmup
start_idx = df[mask].index[0]
end_idx = df[mask].index[-1]
warmup_start = max(0, start_idx - 200)

sub_full = df.loc[warmup_start:end_idx].copy().reset_index(drop=True)

# Compute Features
c = sub_full['close']
h = sub_full['high']
l = sub_full['low']
N_full = len(sub_full)

tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
atr = tr.ewm(span=20, adjust=False).mean() + 1e-4

h50 = h.rolling(50).max().shift(1)
l25 = l.rolling(25).min().shift(1)

e20 = c.ewm(span=20, adjust=False).mean()
e50 = c.ewm(span=50, adjust=False).mean()
trend_fast = ((e20 - e50) / atr).values

e_trend = c.ewm(span=150, adjust=False).mean().values
trend_macro = ((c - e_trend) / atr).values

brk_l = ((c - h50) / atr).values
brk_s = ((c - l25) / atr).values

ret_1 = (100.0 * (c / c.shift(1) - 1.0)).values
ret_3 = (100.0 * (c / c.shift(3) - 1.0)).values
ret_10 = (100.0 * (c / c.shift(10) - 1.0)).values
rng_norm = ((h - l) / atr).values

# Kinematics
# Velocity (v): Price velocity in ATR units per bar
vel_1 = ((c - c.shift(1)) / atr).values
# Acceleration (a): Change in velocity (curvature)
acc_1 = (pd.Series(vel_1) - pd.Series(vel_1).shift(1)).values
# Jerk (j): Third derivative / micro-shock
jerk = (pd.Series(acc_1) - pd.Series(acc_1).shift(1)).values

# Model Parameters (from task1_pls_modulator_submission.py)
FEAT_BOUNDS = [
    (-17.0366, 2.7660),   # Brk_Long
    (-2.4453, 14.2059),   # Brk_Short
    (-3.9022, 4.7975),    # Trend_Fast
    (-12.8261, 15.3480),  # Trend_Macro
    (-1.4955, 1.3542),    # Ret_1
    (-2.8188, 2.5833),    # Ret_3
    (-5.5919, 4.5793),    # Ret_10
    (0.0, 3.5201)         # Range_Norm
]
FEATURE_MEANS = np.array([-3.71338, 3.49222, 0.35692, 1.60763, 0.00292, 0.00823, 0.02486, 0.94942])
FEATURE_STDS = np.array([3.22822, 2.72515, 1.53133, 5.13995, 0.18555, 0.34452, 0.67309, 0.42250])
BETA_PLS = np.array([0.002992, 0.011505, -0.002990, -0.002069, 0.003463, 0.005331, 0.014422, 0.006145])

TARGET_LOWER = -1.413996
TARGET_UPPER = 1.449388
MOD1_C = -0.46857
MOD2_C = -0.15092
MOD3_C = 0.06037
ASYM_POS_SCALE = 1.1

MOD1_MEAN, MOD1_STD = -3.566091, 3.758124
MOD2_MEAN, MOD2_STD = 0.009019, 0.160442
MOD3_MEAN, MOD3_STD = -11.994227, 40.421061

raw_matrix = np.column_stack([
    brk_l, brk_s, trend_fast, trend_macro, ret_1, ret_3, ret_10, rng_norm
])

X_scaled = np.zeros_like(raw_matrix)
for j in range(8):
    lb, ub = FEAT_BOUNDS[j]
    col = np.clip(np.nan_to_num(raw_matrix[:, j]), lb, ub)
    X_scaled[:, j] = (col - FEATURE_MEANS[j]) / (FEATURE_STDS[j] + 1e-8)

base_pred = X_scaled @ BETA_PLS

m1_raw = np.nan_to_num(raw_matrix[:, 0] * raw_matrix[:, 7])
m1 = (m1_raw - MOD1_MEAN) / MOD1_STD

relu_r1 = np.maximum(0.0, np.nan_to_num(raw_matrix[:, 4]))
relu_r3 = np.maximum(0.0, np.nan_to_num(raw_matrix[:, 5]))
m2_raw = 0.5 * (relu_r1**2) * (relu_r3**2)
m2 = (m2_raw - MOD2_MEAN) / MOD2_STD

tf = np.nan_to_num(raw_matrix[:, 2])
tm = np.nan_to_num(raw_matrix[:, 3])
m3_raw = (np.sign(tf) * (tf**2)) - (np.sign(tm) * (tm**2))
m3 = (m3_raw - MOD3_MEAN) / MOD3_STD

adj_pred = base_pred * (1.0 + MOD1_C * m1) * (1.0 + MOD2_C * m2) * (1.0 + MOD3_C * m3)
pos_mask = adj_pred > 0
adj_pred[pos_mask] = adj_pred[pos_mask] * ASYM_POS_SCALE
final_pred = np.clip(adj_pred, TARGET_LOWER, TARGET_UPPER)

# Simulate Strategy Execution
thresh = 0.05
stall_limit = 6
pos = np.zeros(N_full)
stall_arr = np.zeros(N_full)
cur = 0.0
stall = 0
entry_px = 0.0
cv = c.values
h50v = h50.values
l25v = l25.values

for i in range(N_full):
    if np.isnan(h50v[i]) or np.isnan(e_trend[i]) or np.isnan(l25v[i]):
        pos[i] = 0.0
        stall_arr[i] = 0
        continue

    p_val = final_pred[i]

    if cur == 1.0:
        if cv[i] <= entry_px:
            stall += 1
        else:
            stall = 0
        if p_val < -thresh * 0.5 or cv[i] < e_trend[i] or (stall_limit > 0 and stall >= stall_limit):
            cur = 0.0
            stall = 0

    elif cur == -1.0:
        if cv[i] >= entry_px:
            stall += 1
        else:
            stall = 0
        if p_val > thresh * 0.5 or cv[i] > e_trend[i] or (stall_limit > 0 and stall >= stall_limit):
            cur = 0.0
            stall = 0

    if cur == 0.0:
        if p_val > thresh and cv[i] > h50v[i] and cv[i] > e_trend[i]:
            cur = 1.0
            entry_px = cv[i]
            stall = 0
        elif p_val < -thresh and cv[i] < l25v[i] and cv[i] < e_trend[i]:
            cur = -1.0
            entry_px = cv[i]
            stall = 0

    pos[i] = cur
    stall_arr[i] = stall

# Slice strictly to the evaluation window
eval_offset = start_idx - warmup_start
eval_len = end_idx - start_idx + 1

times = sub_full['datetime'].iloc[eval_offset:eval_offset + eval_len].values
close_vals = c.iloc[eval_offset:eval_offset + eval_len].values
high_vals = h.iloc[eval_offset:eval_offset + eval_len].values
low_vals = l.iloc[eval_offset:eval_offset + eval_len].values
atr_vals = atr.iloc[eval_offset:eval_offset + eval_len].values
h50_vals = h50.iloc[eval_offset:eval_offset + eval_len].values
l25_vals = l25.iloc[eval_offset:eval_offset + eval_len].values
etrend_vals = e_trend[eval_offset:eval_offset + eval_len]
vel_vals = vel_1[eval_offset:eval_offset + eval_len]
acc_vals = acc_1[eval_offset:eval_offset + eval_len]
jerk_vals = jerk[eval_offset:eval_offset + eval_len]
base_preds = base_pred[eval_offset:eval_offset + eval_len]
final_preds = final_pred[eval_offset:eval_offset + eval_len]
m1_vals = m1[eval_offset:eval_offset + eval_len]
m2_vals = m2[eval_offset:eval_offset + eval_len]
m3_vals = m3[eval_offset:eval_offset + eval_len]
pos_vals = pos[eval_offset:eval_offset + eval_len]
stall_vals = stall_arr[eval_offset:eval_offset + eval_len]

# Neuron Excitation Bars [0.0 - 1.0]
e_vel = np.clip(np.abs(vel_vals) / 2.5, 0.0, 1.0)
e_acc = np.clip(np.maximum(0.0, -acc_vals) / 2.5, 0.0, 1.0)
e_jerk = np.clip(np.abs(jerk_vals) / 3.0, 0.0, 1.0)
e_vol = np.clip(rng_norm[eval_offset:eval_offset + eval_len] / 2.5, 0.0, 1.0)
e_macro = np.clip(np.abs(trend_macro[eval_offset:eval_offset + eval_len]) / 3.5, 0.0, 1.0)
e_mod2 = np.clip(m2_vals / 2.0, 0.0, 1.0)
e_stall = np.clip(stall_vals / 6.0, 0.0, 1.0)
e_crash = np.clip(0.35 * e_acc + 0.25 * e_jerk + 0.20 * e_vol + 0.20 * e_stall, 0.0, 1.0)

# Cumulative Strategy Return vs Buy & Hold
bar_ret = np.zeros(eval_len)
bar_ret[1:] = (close_vals[1:] / close_vals[:-1]) - 1.0
strat_bar_ret = pos_vals[:-1] * bar_ret[1:]
strat_cum = np.cumprod(1.0 + np.insert(strat_bar_ret, 0, 0.0)) - 1.0
bnh_cum = np.cumprod(1.0 + bar_ret) - 1.0

print(f"Data prepared: {eval_len} bars from {pd.to_datetime(times[0])} to {pd.to_datetime(times[-1])}")
print(f"Nifty return: {bnh_cum[-1]*100:.2f}%, Strategy return: {strat_cum[-1]*100:.2f}%")

# Save JSON data for standalone Interactive HTML Dashboard
records = []
for i in range(eval_len):
    t_str = pd.to_datetime(times[i]).strftime('%Y-%m-%d %H:%M')
    records.append({
        'i': i,
        'time': t_str,
        'close': round(float(close_vals[i]), 1),
        'high': round(float(high_vals[i]), 1),
        'low': round(float(low_vals[i]), 1),
        'atr': round(float(atr_vals[i]), 1),
        'h50': round(float(h50_vals[i]), 1),
        'l25': round(float(l25_vals[i]), 1),
        'etrend': round(float(etrend_vals[i]), 1),
        'vel': round(float(vel_vals[i]), 3),
        'acc': round(float(acc_vals[i]), 3),
        'jerk': round(float(jerk_vals[i]), 3),
        'base': round(float(base_preds[i]), 4),
        'final': round(float(final_preds[i]), 4),
        'm1': round(float(m1_vals[i]), 3),
        'm2': round(float(m2_vals[i]), 3),
        'm3': round(float(m3_vals[i]), 3),
        'pos': int(pos_vals[i]),
        'stall': int(stall_vals[i]),
        'strat_cum': round(float(strat_cum[i] * 100), 2),
        'bnh_cum': round(float(bnh_cum[i] * 100), 2),
        'e_vel': round(float(e_vel[i]), 3),
        'e_acc': round(float(e_acc[i]), 3),
        'e_jerk': round(float(e_jerk[i]), 3),
        'e_vol': round(float(e_vol[i]), 3),
        'e_macro': round(float(e_macro[i]), 3),
        'e_mod2': round(float(e_mod2[i]), 3),
        'e_stall': round(float(e_stall[i]), 3),
        'e_crash': round(float(e_crash[i]), 3)
    })

with open('charts/crash_forensics_data.json', 'w') as f:
    json.dump(records, f)
print("Saved charts/crash_forensics_data.json")
