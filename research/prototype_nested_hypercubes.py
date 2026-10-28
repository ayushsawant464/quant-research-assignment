import numpy as np
import pandas as pd
from scipy import stats
import harness_public as harness

# Load strictly Task 1 In-Sample Data for calibration
bars_train = harness.load_bars('data/nifty50_15min_train_2017-04-03_2022-01-31.csv')
exp_train = harness.load_expiries('data/nifty_monthly_expiries_2017-01_2022-01.csv')

c = bars_train['close']
o = bars_train['open']
h = bars_train['high']
l = bars_train['low']
N_tr = len(bars_train)

# 1. Base Multi-Horizon Metrics
tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
atr_fast = tr.ewm(span=20, adjust=False).mean() + 1e-4
atr_macro = tr.ewm(span=100, adjust=False).mean() + 1e-4

h50 = h.rolling(50).max().shift(1)
l25 = l.rolling(25).min().shift(1)
e20 = c.ewm(span=20, adjust=False).mean()
e50 = c.ewm(span=50, adjust=False).mean()
e_trend = c.ewm(span=150, adjust=False).mean()

# =========================================================================
# LEVEL 1: MACRO-HYPERCUBE [0, 1]^3
# Dimensions:
#   1. Macro Trend Elevation: x_m = (c - e_trend) / atr_macro
#   2. Multi-Day Channel Position: x_ch = (c - l25) / (h50 - l25 + 1e-4)
#   3. Structural Volatility Regimes: x_vol = atr_fast / atr_macro
# =========================================================================
raw_xm = ((c - e_trend) / atr_macro).values
raw_xch = np.clip(((c - l25) / (h50 - l25 + 1e-4)).values, 0.0, 1.0)
raw_xvol = (atr_fast / atr_macro).values

# Fit ECDFs strictly on in-sample training data
def fit_ecdf(arr):
    clean = np.sort(arr[~np.isnan(arr)])
    def transform(x):
        r = np.searchsorted(clean, x) / float(len(clean))
        return np.clip(r, 0.0, 1.0)
    return transform

ecdf_xm = fit_ecdf(raw_xm)
ecdf_xvol = fit_ecdf(raw_xvol)

xm = ecdf_xm(raw_xm)
xch = raw_xch
xvol = ecdf_xvol(raw_xvol)

# Macro State Surface: Y_macro in [0, 1]
# Y_macro > 0.65 -> Macro Bull Expansion (Activate Bull Micro-Hypercube)
# Y_macro < 0.35 -> Macro Bear Cascade   (Activate Bear Micro-Hypercube)
# 0.35 <= Y_macro <= 0.65 -> Macro Chop  (Deactivate all entries, hold cash)
macro_energy = 1.4 * (2.0 * xm - 1.0) + 1.0 * (2.0 * xch - 1.0) - 0.4 * (2.0 * xvol - 1.0)
y_macro = 1.0 / (1.0 + np.exp(-macro_energy * 1.5))

# =========================================================================
# LEVEL 2: MICRO-HYPERCUBES [0, 1]^3 INSIDE THE MACRO DOMAINS
# Micro Dimensions:
#   1. 1-bar Intraday Impulse: x_p1 = (c - o) / atr_fast
#   2. 3-bar Return Momentum:  x_p3 = (c / c.shift(3) - 1.0) / atr_fast
#   3. 5-bar Kinematic Acceleration: x_acc = delta(vel)
# =========================================================================
raw_p1 = ((c - o) / atr_fast).values
raw_p3 = ((c - c.shift(3)) / (np.sqrt(3) * atr_fast)).values
vel = (c - c.shift(1)) / atr_fast
acc = vel - vel.shift(1)
raw_acc5 = acc.rolling(5).mean().values

ecdf_p1 = fit_ecdf(raw_p1)
ecdf_p3 = fit_ecdf(raw_p3)
ecdf_acc = fit_ecdf(raw_acc5)

xp1 = ecdf_p1(raw_p1)
xp3 = ecdf_p3(raw_p3)
xacc = ecdf_acc(raw_acc5)

# Micro Bull Surface: active inside Macro Bull
# Evaluates whether the immediate 15-min bar has clean acceleration or exhaustion sweep
micro_bull_energy = 0.8 * (2.0 * xp1 - 1.0) + 0.8 * (2.0 * xp3 - 1.0) + 1.2 * (2.0 * xacc - 1.0)
y_micro_bull = 1.0 / (1.0 + np.exp(-micro_bull_energy * 2.0))

# Micro Bear Surface: active inside Macro Bear
micro_bear_energy = 0.8 * (1.0 - 2.0 * xp1) + 0.8 * (1.0 - 2.0 * xp3) + 1.2 * (1.0 - 2.0 * xacc)
y_micro_bear = 1.0 / (1.0 + np.exp(-micro_bear_energy * 2.0))

print(f"Calibration finished on {N_tr} training bars.")
print(f"Macro Bull bars: {(y_macro >= 0.60).sum()} ({(y_macro >= 0.60).mean()*100:.1f}%)")
print(f"Macro Bear bars: {(y_macro <= 0.40).sum()} ({(y_macro <= 0.40).mean()*100:.1f}%)")
print(f"Macro Chop bars: {((y_macro > 0.40) & (y_macro < 0.60)).sum()} ({((y_macro > 0.40) & (y_macro < 0.60)).mean()*100:.1f}%)")

