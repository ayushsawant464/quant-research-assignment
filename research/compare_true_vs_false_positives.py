import numpy as np
import pandas as pd

df = pd.read_csv('data/nifty50_15min_full_2017-04-03_2026-10-26.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

df['date'] = df['datetime'].dt.date
daily = df.groupby('date').agg(
    open=('open', 'first'),
    high=('high', 'max'),
    low=('low', 'min'),
    close=('close', 'last'),
    volume=('n_1min', 'sum')
).reset_index()

c = daily['close']
h = daily['high']
l = daily['low']
o = daily['open']
v = daily['volume']

tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
atr = tr.ewm(span=20, adjust=False).mean()

h50 = h.rolling(50).max().shift(1)
range_d = h - l
body_d = c - o
upper_wick = h - np.maximum(o, c)

e50 = c.ewm(span=50, adjust=False).mean()
e200 = c.ewm(span=200, adjust=False).mean()

# Distance from 50-day EMA in ATR units
trend_ext = (c - e50) / atr
macro_ext = (c - e200) / atr

# Efficiency ratio
net_5 = (c - c.shift(5)).abs()
gross_5 = range_d.rolling(5).sum() + 1e-6
er_5 = net_5 / gross_5

# Volume ratio
v_mean = v.rolling(20).mean().shift(1) + 1e-4
vol_surge = v / v_mean

# Let's check True Regime Reversals vs False Positives
true_dates = ['2018-01-18', '2019-04-18', '2020-01-20', '2021-01-21', '2021-10-19', '2022-01-18', '2022-09-15', '2024-09-19']
false_dates = ['2020-06-24', '2020-10-15', '2020-11-19', '2020-11-25', '2020-12-21', '2021-08-18', '2021-09-17', '2023-06-08', '2023-12-12']

def get_stats(date_list, label):
    rows = daily[daily['date'].astype(str).isin(date_list)]
    print(f"\n--- {label} ---")
    for _, r in rows.iterrows():
        idx = r.name
        print(f"Date: {r['date']} | Close: {r['close']:>7.1f} | MacroExt (C-EMA200)/ATR: {macro_ext[idx]:>5.2f} | ER_5: {er_5[idx]:.3f} | VolSurge: {vol_surge[idx]:.2f}")
    
    sub_macro = macro_ext[rows.index]
    sub_er = er_5[rows.index]
    sub_vol = vol_surge[rows.index]
    print(f"AVG MacroExt: {sub_macro.mean():.2f} | AVG ER_5: {sub_er.mean():.3f} | AVG VolSurge: {sub_vol.mean():.2f}")

get_stats(true_dates, "TRUE REGIME REVERSALS (Market shift followed)")
get_stats(false_dates, "FALSE POSITIVES (Market continued bull)")
