import numpy as np
import pandas as pd
from scipy import stats

print("Loading 15-minute dataset (2017-2026)...")
df = pd.read_csv('data/nifty50_15min_full_2017-04-03_2026-10-26.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

c = df['close']
o = df['open']
h = df['high']
l = df['low']
v = df['n_1min']
N = len(df)

tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
atr = tr.ewm(span=20, adjust=False).mean() + 1e-4

# We test rolling windows representing ~3 to 5 trading days (75 to 125 bars of 15m)
W = 75 

# Metric 1: Path Efficiency (Kaufman ER)
net_disp = (c - c.shift(W)).abs()
gross_travel = (c - c.shift(1)).abs().rolling(W).sum() + 1e-6
kaufman_er = net_disp / gross_travel

# Metric 2: Effort Without Result (Wyckoff Absorption Divergence)
# High gross travel / volume relative to net price progress
v_mean = v.rolling(W).mean() + 1e-4
norm_vol = v.rolling(W).sum() / (v_mean * W)
# Effort / Result ratio:
effort_result_ratio = (gross_travel / atr) / (net_disp / atr + 0.1)

# Metric 3: Trap Density (Failed Breakout Rate)
h50 = h.rolling(50).max().shift(1)
l25 = l.rolling(25).min().shift(1)

# Breakout events:
brk_up = (c > h50)
brk_down = (c < l25)

# A breakout is "trapped" if 6 bars later, price is below breakout level (for up) or above (for down)
trap_up = brk_up & (c.shift(-6) <= h50)
trap_down = brk_down & (c.shift(-6) >= l25)

# Rolling rate over 100 bars
total_brk = (brk_up | brk_down).rolling(W).sum()
trapped_brk = (trap_up | trap_down).rolling(W).sum()
trap_rate = np.where(total_brk >= 5, trapped_brk / total_brk, np.nan)

# Metric 4: Realized Range vs Directional Variance Divergence (Intraday Spread vs Drift)
gk_var = 0.5 * (np.log(h / l))**2 - (2 * np.log(2) - 1) * (np.log(c / o))**2
gk_vol = np.sqrt(np.maximum(0, gk_var)).rolling(W).mean()
drift_vol = (c.pct_change(W).abs()) + 1e-6
range_drift_divergence = gk_vol / drift_vol

# Metric 5: Multi-Day Variance Ratio VR(5)
ret_1 = c.pct_change()
var_1 = ret_1.rolling(W).var() + 1e-12
ret_5 = c.pct_change(5)
var_5 = ret_5.rolling(W).var() + 1e-12
variance_ratio = var_5 / (5.0 * var_1)

df['kaufman_er'] = kaufman_er
df['effort_ratio'] = effort_result_ratio
df['trap_rate'] = trap_rate
df['range_drift_div'] = range_drift_divergence
df['variance_ratio'] = variance_ratio

# Define the Known Ground-Truth Major Regime Transitions:
# 1. Jan 2018 Peak (Jan 15 - Feb 15, 2018): Transition from 2017 smooth bull to 2018 volatile chop
# 2. Feb 2020 COVID Onset (Feb 15 - Mar 15, 2020): Transition from steady grinding to panic freefall
# 3. Oct 2021 Peak (Oct 01 - Nov 15, 2021): Transition from massive post-COVID bull to 2022 chop/whipsaw
# 4. March 2023 Bottom/Breakout (Mar 15 - Apr 15, 2023): Transition from 18-month chop to explosive bull run
# 5. June 2024 Election Shock (May 25 - Jun 10, 2024): Transition into extreme high-volatility distribution

transitions = [
    ('Jan 2018 Peak (Bull -> Chop)', '2018-01-15', '2018-02-15'),
    ('Feb 2020 COVID (Grind -> Crash)', '2020-02-15', '2020-03-15'),
    ('Oct 2021 Peak (Bull -> 2022 Chop)', '2021-10-01', '2021-11-15'),
    ('Mar 2023 Inflection (Chop -> Bull)', '2023-03-15', '2023-04-15'),
    ('Jun 2024 Election (Shock Transition)', '2024-05-25', '2024-06-10')
]

print("\n" + "="*85)
print("EVALUATION AT GROUND-TRUTH REGIME TRANSITIONS:")
print("="*85)
for name, start, end in transitions:
    sub = df[(df['datetime'] >= start) & (df['datetime'] <= end)]
    print(f"\n[{name}] ({start} to {end}):")
    print(f"  Kaufman ER:           {sub['kaufman_er'].mean():.4f} (Min: {sub['kaufman_er'].min():.4f})")
    print(f"  Effort/Result Ratio:  {sub['effort_ratio'].mean():.2f} (Max: {sub['effort_ratio'].max():.2f})")
    print(f"  Trap Rate (Fails):    {sub['trap_rate'].mean()*100:.1f}% (Max: {sub['trap_rate'].max()*100:.1f}%)")
    print(f"  Range/Drift Div:      {sub['range_drift_div'].mean():.2f} (Max: {sub['range_drift_div'].max():.2f})")
    print(f"  Variance Ratio:       {sub['variance_ratio'].mean():.2f} (Min: {sub['variance_ratio'].min():.2f})")

