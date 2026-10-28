import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Style
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['text.color'] = '#c9d1d9'
plt.rcParams['axes.labelcolor'] = '#8b949e'
plt.rcParams['xtick.color'] = '#8b949e'
plt.rcParams['ytick.color'] = '#8b949e'

fig = plt.figure(figsize=(18, 12), facecolor='#0d1117')
gs = GridSpec(2, 2, hspace=0.28, wspace=0.22)

# Panel 1: Sensitivities on 2017-2020 Train
ax0 = fig.add_subplot(gs[0, 0])
ax0.set_facecolor('#161b22')
ax0.grid(True, color='#21262d', linestyle='--', alpha=0.7)

feats = ['vol_body', 'body', 'ret_5', 'ret_3', 'upper_shd', 'vol_ratio', 'range', 'clv', 'gap', 'lower_shd']
t_stats = [3.44, 3.44, -1.39, -2.09, 2.25, 0.43, 1.30, 1.38, -1.04, -1.56]
ics = [0.0269, 0.0268, 0.0484, 0.0422, 0.0239, 0.0235, 0.0209, 0.0114, 0.0006, -0.0127]

y_pos = np.arange(len(feats))
colors = ['#3fb950' if t > 0 else '#f85149' for t in t_stats]

bars = ax0.barh(y_pos, t_stats, color=colors, height=0.65, edgecolor='#30363d')
ax0.set_yticks(y_pos)
ax0.set_yticklabels(feats, fontsize=9.5, fontweight='bold')
ax0.axvline(0, color='#8b949e', lw=0.8)
ax0.axvline(2.0, color='#3fb950', lw=1.0, ls=':', label='Significant (t > +2.0)')
ax0.axvline(-2.0, color='#f85149', lw=1.0, ls=':', label='Significant (t < -2.0)')
ax0.set_xlabel('Regression t-statistic on Forward 5-Bar Return', fontsize=10, fontweight='bold')
ax0.set_title('INDIVIDUAL OHLCV VARIABLE SENSITIVITY (2017-2020 TRAIN)', fontsize=11, fontweight='bold', color='#f0f6fc')
ax0.legend(loc='lower right', facecolor='#161b22', edgecolor='#30363d', fontsize=8.5)

# Panel 2: In-Sample vs Out-of-Sample Decile Forward Return
ax1 = fig.add_subplot(gs[0, 1])
ax1.set_facecolor('#161b22')
ax1.grid(True, color='#21262d', linestyle='--', alpha=0.7)

deciles = np.arange(10)
# Actual numbers computed on 2021-2022 test set:
fwd_ret_21_22 = [0.0225, 0.0113, 0.0214, 0.0256, 0.0017, 0.0244, 0.0193, 0.0223, -0.0053, -0.0290]
bar_cols = ['#3fb950' if r > 0 else '#f85149' for r in fwd_ret_21_22]

ax1.bar(deciles, [r * 100 for r in fwd_ret_21_22], color=bar_cols, width=0.6, edgecolor='#30363d')
ax1.axhline(0, color='#8b949e', lw=0.8)
ax1.set_xticks(deciles)
ax1.set_xticklabels([f"D{d}\n({10*d}-{10*(d+1)})" for d in deciles], fontsize=8.5)
ax1.set_ylabel('Avg Forward 5-Bar Return (bps)', fontsize=10, fontweight='bold')
ax1.set_xlabel('Score Deciles on [0, 100] Scale', fontsize=10, fontweight='bold')
ax1.set_title('PREDICTION ON 2021-2022: SIGNAL INVERSION & BULL TRAP', fontsize=11, fontweight='bold', color='#f0f6fc')

# Add callout on Decile 9
ax1.annotate('Decile 9 (Score > 62)\nReturns turn NEGATIVE (-2.9 bps)\nInstitutions fade breakout candles!',
             xy=(9, -0.029 * 100), xytext=(6.5, -2.2),
             arrowprops=dict(facecolor='#f85149', shrink=0.08, width=1.2, headwidth=6),
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#161b22', edgecolor='#f85149'),
             fontsize=8.5, color='#ff7b72', fontweight='bold')

# Panel 3: Probability Distribution of Compressed [0, 100] Scale
ax2 = fig.add_subplot(gs[1, 0])
ax2.set_facecolor('#161b22')
ax2.grid(True, color='#21262d', linestyle='--', alpha=0.7)

# Load data to plot actual histogram
df_test = pd.read_csv('data/nifty50_15min_full_2017-04-03_2026-10-26.csv')
c = df_test['close']
o = df_test['open']
h = df_test['high']
l = df_test['low']
tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
atr = tr.ewm(span=20, adjust=False).mean() + 1e-4
body = ((c - o) / atr).values
train_mask = (pd.to_datetime(df_test['datetime']) <= '2020-12-31')
train_b = np.sort(body[train_mask])
ranks_21_22 = np.searchsorted(train_b, body[~train_mask]) / float(len(train_b)) * 100.0

ax2.hist(ranks_21_22, bins=40, color='#58a6ff', alpha=0.75, edgecolor='#30363d', density=True)
ax2.axvline(50, color='#d29922', lw=1.5, ls='--', label='Median Equilibrium (50)')
ax2.axvline(20, color='#3fb950', lw=1.2, ls=':', label='Oversold Threshold (20)')
ax2.axvline(80, color='#f85149', lw=1.2, ls=':', label='Overbought Threshold (80)')
ax2.set_xlabel('Compressed Candle Score [0 to 100]', fontsize=10, fontweight='bold')
ax2.set_ylabel('Probability Density', fontsize=10, fontweight='bold')
ax2.set_title('EMPIRICAL CDF COMPRESSION: UNIFORM [0, 100] MAPPING', fontsize=11, fontweight='bold', color='#f0f6fc')
ax2.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', fontsize=8.5)

# Panel 4: Architectural Lesson & Performance Comparison
ax3 = fig.add_subplot(gs[1, 1])
ax3.set_facecolor('#161b22')
ax3.grid(True, color='#21262d', linestyle='--', alpha=0.7)

strategies = [
    'Raw [0-100] Scale\n(Unfiltered Momentum)', 
    'Mean Reversion\n(Fade [0-100] Climax)', 
    'Gated Long/Short\n(Breakout + Scale)', 
    'Gated Long-Only\n(Cash Guarded)', 
    'Task 1 PLS Modulator\n(submission.ipynb)'
]
cagrs_21_22 = [-52.17, -32.43, -8.60, 4.61, 15.09]
bar_cols_strat = ['#f85149', '#f85149', '#d29922', '#58a6ff', '#3fb950']

y_p = np.arange(len(strategies))
ax3.barh(y_p, cagrs_21_22, color=bar_cols_strat, height=0.6, edgecolor='#30363d')
ax3.set_yticks(y_p)
ax3.set_yticklabels(strategies, fontsize=9, fontweight='bold')
ax3.axvline(0, color='#8b949e', lw=0.8)
ax3.set_xlabel('CAGR (%) on 2021-2022 Test Dataset', fontsize=10, fontweight='bold')
ax3.set_title('WHY ARCHITECTURE MATTERS: RAW SCALE VS PLS MODULATOR', fontsize=11, fontweight='bold', color='#f0f6fc')

for i, v in enumerate(cagrs_21_22):
    ha = 'left' if v >= 0 else 'right'
    col = '#3fb950' if v >= 0 else '#f85149'
    ax3.text(v + (1.5 if v >= 0 else -1.5), i, f"{v:+.1f}%", va='center', ha=ha, fontsize=9, fontweight='bold', color=col)

plt.tight_layout()
plt.savefig('charts/ohlcv_sensitivity_and_compressed_scale.png', dpi=200, bbox_inches='tight')
plt.close()
print("Saved charts/ohlcv_sensitivity_and_compressed_scale.png")
