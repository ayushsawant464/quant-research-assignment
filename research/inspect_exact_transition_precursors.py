import numpy as np
import pandas as pd

df = pd.read_csv('data/nifty50_15min_full_2017-04-03_2026-10-26.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

# Let's inspect the exact 10 days leading up to the Oct 2021 Peak (Oct 08, 2021 to Oct 22, 2021)
# Nifty made its historic all-time high on Oct 19, 2021 at 18,604.
sub_oct21 = df[(df['datetime'] >= '2021-10-14') & (df['datetime'] <= '2021-10-25')].copy()

# Compute Daily metrics during this week
sub_oct21['date'] = sub_oct21['datetime'].dt.date
daily_oct21 = sub_oct21.groupby('date').agg(
    open=('open', 'first'),
    high=('high', 'max'),
    low=('low', 'min'),
    close=('close', 'last'),
    volume=('n_1min', 'sum')
)
daily_oct21['range'] = daily_oct21['high'] - daily_oct21['low']
daily_oct21['body'] = daily_oct21['close'] - daily_oct21['open']
daily_oct21['upper_wick'] = daily_oct21['high'] - np.maximum(daily_oct21['open'], daily_oct21['close'])
daily_oct21['lower_wick'] = np.minimum(daily_oct21['open'], daily_oct21['close']) - daily_oct21['low']

print("--- DAILY PRICE ACTION AROUND OCT 2021 PEAK (18,604) ---")
print(daily_oct21.to_string())

# Same for Feb 2020 Peak (Feb 12 to Feb 25, 2020)
sub_feb20 = df[(df['datetime'] >= '2020-02-12') & (df['datetime'] <= '2020-02-25')].copy()
sub_feb20['date'] = sub_feb20['datetime'].dt.date
daily_feb20 = sub_feb20.groupby('date').agg(
    open=('open', 'first'),
    high=('high', 'max'),
    low=('low', 'min'),
    close=('close', 'last'),
    volume=('n_1min', 'sum')
)
daily_feb20['range'] = daily_feb20['high'] - daily_feb20['low']
daily_feb20['body'] = daily_feb20['close'] - daily_feb20['open']
daily_feb20['upper_wick'] = daily_feb20['high'] - np.maximum(daily_feb20['open'], daily_feb20['close'])
daily_feb20['lower_wick'] = np.minimum(daily_feb20['open'], daily_feb20['close']) - daily_feb20['low']

print("\n--- DAILY PRICE ACTION AROUND FEB 2020 PEAK (12,150) ---")
print(daily_feb20.to_string())

# Same for Jan 2018 Peak (Jan 22 to Feb 02, 2018)
sub_jan18 = df[(df['datetime'] >= '2018-01-22') & (df['datetime'] <= '2018-02-05')].copy()
sub_jan18['date'] = sub_jan18['datetime'].dt.date
daily_jan18 = sub_jan18.groupby('date').agg(
    open=('open', 'first'),
    high=('high', 'max'),
    low=('low', 'min'),
    close=('close', 'last'),
    volume=('n_1min', 'sum')
)
daily_jan18['range'] = daily_jan18['high'] - daily_jan18['low']
daily_jan18['body'] = daily_jan18['close'] - daily_jan18['open']
daily_jan18['upper_wick'] = daily_jan18['high'] - np.maximum(daily_jan18['open'], daily_jan18['close'])
daily_jan18['lower_wick'] = np.minimum(daily_jan18['open'], daily_jan18['close']) - daily_jan18['low']

print("\n--- DAILY PRICE ACTION AROUND JAN 2018 PEAK (11,170) ---")
print(daily_jan18.to_string())

