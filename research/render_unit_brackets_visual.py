import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import ListedColormap, BoundaryNorm

# Setup Figure
fig = plt.figure(figsize=(18, 12), facecolor='#0d1117')
gs = GridSpec(2, 2, hspace=0.25, wspace=0.20, left=0.06, right=0.95, top=0.93, bottom=0.07)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['text.color'] = '#c9d1d9'
plt.rcParams['axes.labelcolor'] = '#8b949e'
plt.rcParams['xtick.color'] = '#8b949e'
plt.rcParams['ytick.color'] = '#8b949e'

# Panel 1: Target Price S-Curve Mapping into [0, 1]
ax0 = fig.add_subplot(gs[0, 0])
ax0.set_facecolor('#161b22')
ax0.grid(True, color='#21262d', linestyle='--', alpha=0.7)

delta_atr = np.linspace(-4.5, 4.5, 300)
k_scale = 1.2
y_unit = 1.0 / (1.0 + np.exp(-delta_atr / k_scale))

ax0.plot(delta_atr, y_unit, color='#38bdf8', lw=2.4, label='Sigmoidal Mapping: y = σ(ΔP / 1.2 ATR)')

# Mark Brackets
bracket_edges = np.linspace(0.0, 1.0, 11)
colors_b = ['#7f1d1d', '#991b1b', '#dc2626', '#f87171', '#64748b', '#475569', '#4ade80', '#22c55e', '#16a34a', '#14532d']

for i in range(10):
    b_low, b_high = bracket_edges[i], bracket_edges[i+1]
    ax0.axhspan(b_low, b_high, color=colors_b[i], alpha=0.18)
    ax0.axhline(b_high, color='#30363d', lw=0.6, ls=':')

ax0.axvline(0, color='#f0f6fc', lw=1.0, ls='--', label='Zero Displacement (y = 0.50)')
ax0.axhline(0.5, color='#f0f6fc', lw=1.0, ls='--')

ax0.set_xlabel('Real Market Move ΔP (ATR Multiples)', fontsize=9.5, fontweight='bold')
ax0.set_ylabel('Normalized Target Value y in [0, 1]', fontsize=9.5, fontweight='bold')
ax0.set_title('TARGET PRICE COMPRESSION: CONTINUOUS DISPLACEMENT TO [0, 1]', fontsize=10.5, fontweight='bold', color='#f0f6fc')
ax0.legend(loc='upper left', facecolor='#161b22', edgecolor='#30363d', fontsize=8.5)

# Panel 2: Synthetic Unit-Square [0, 1]^2 Precondition Manifold
ax1 = fig.add_subplot(gs[0, 1])
ax1.set_facecolor('#161b22')

x_p = np.linspace(0, 1, 150)
x_v = np.linspace(0, 1, 150)
X_P, X_V = np.meshgrid(x_p, x_v)

# Synthetic energy function mapping [0, 1]^2 to y in [0, 1]
# Centered around 0.5:
# y = 0.5 + 0.45 * (2*xp - 1) * exp(0.8 * (xv - 0.5))
Y_synthetic = 0.5 + 0.45 * (2 * X_P - 1) * np.exp(0.8 * (X_V - 0.5))
Y_synthetic = np.clip(Y_synthetic, 0.01, 0.99)

cmap_b = ListedColormap(colors_b)
norm_b = BoundaryNorm(bracket_edges, cmap_b.N)

cf = ax1.contourf(X_P, X_V, Y_synthetic, levels=bracket_edges, cmap=cmap_b, norm=norm_b, alpha=0.85)
cs = ax1.contour(X_P, X_V, Y_synthetic, levels=[0.1, 0.3, 0.5, 0.7, 0.9], colors='#ffffff', linewidths=0.7, alpha=0.6)
ax1.clabel(cs, fmt='y=%.1f', fontsize=8, colors='#ffffff')

ax1.axvline(0.5, color='#94a3b8', lw=0.8, ls=':')
ax1.axhline(0.5, color='#94a3b8', lw=0.8, ls=':')

ax1.set_xlabel('Normalized Price Impulse x_p in [0, 1]', fontsize=9.5, fontweight='bold')
ax1.set_ylabel('Normalized Volume Ratio x_v in [0, 1]', fontsize=9.5, fontweight='bold')
ax1.set_title('SYNTHETIC UNIT HYPERCUBE [0, 1]^2 -> TARGET BRACKETS', fontsize=10.5, fontweight='bold', color='#f0f6fc')

cbar = plt.colorbar(cf, ax=ax1, orientation='vertical', pad=0.03, ticks=bracket_edges[::2])
cbar.ax.set_yticklabels([f'B{i}' for i in range(0, 11, 2)], fontsize=8)
cbar.set_label('Target Landing Bracket (B0 to B9)', fontsize=8.5, fontweight='bold')

# Panel 3: Bracket Decile Distribution on Real 2021-2022 Test Data
ax2 = fig.add_subplot(gs[1, 0])
ax2.set_facecolor('#161b22')
ax2.grid(True, color='#21262d', linestyle='--', alpha=0.7)

# Load real Nifty 15-min data
df = pd.read_csv('data/nifty50_15min_full_2017-04-03_2026-10-26.csv')
c = df['close']
h = df['high']
l = df['low']
tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
atr = tr.ewm(span=20, adjust=False).mean() + 1e-4

delta_real = ((c.shift(-5) - c) / atr).values
y_real = 1.0 / (1.0 + np.exp(-delta_real / 1.2))
mask_21_22 = (pd.to_datetime(df['datetime']) >= '2021-01-01') & (pd.to_datetime(df['datetime']) <= '2022-12-31')
y_test = y_real[mask_21_22 & ~np.isnan(y_real)]

b_indices = np.digitize(y_test, bracket_edges) - 1
b_indices = np.clip(b_indices, 0, 9)
counts = pd.Series(b_indices).value_counts().sort_index()

ax2.bar(range(10), counts.values, color=colors_b, edgecolor='#30363d', width=0.65)
ax2.set_xticks(range(10))
ax2.set_xticklabels([f'B{i}\n[{bracket_edges[i]:.1f}-{bracket_edges[i+1]:.1f}]' for i in range(10)], fontsize=8)
ax2.set_xlabel('Target Landing Brackets on [0, 1] Scale', fontsize=9.5, fontweight='bold')
ax2.set_ylabel('Number of 15-min Bars (2021-2022 Test Set)', fontsize=9.5, fontweight='bold')
ax2.set_title('REAL MARKET TARGET FREQUENCY DISTRIBUTION (2021-2022)', fontsize=10.5, fontweight='bold', color='#f0f6fc')

# Panel 4: Inverse Precondition Requirement Lookup Table (HUD)
ax3 = fig.add_subplot(gs[1, 1])
ax3.set_facecolor('#111625')
ax3.axis('off')

ax3.text(0.5, 0.94, "EXHAUSTIVE PRECONDITION LOOKUP TABLE", 
         fontsize=10.5, fontweight='bold', color='#f0f6fc', ha='center')
ax3.text(0.5, 0.88, "All Inputs in [0, 1] | Target in [0, 1] Brackets", 
         fontsize=8.5, color='#94a3b8', ha='center')

table_lines = [
    ("B9 [0.9 - 1.0]: Extreme Bull Surge (> +2.6 ATR)", "x_p in [0.75, 1.00]", "x_v in [0.65, 1.00]", "Breakout with high volume"),
    ("B8 [0.8 - 0.9]: Strong Bull Run (+1.7 to +2.6 ATR)", "x_p in [0.65, 0.85]", "x_v in [0.55, 0.90]", "Solid positive impulse"),
    ("B7 [0.7 - 0.8]: Moderate Bull (+1.0 to +1.7 ATR)", "x_p in [0.58, 0.75]", "x_v in [0.45, 0.75]", "Normal bullish continuation"),
    ("B6 [0.6 - 0.7]: Mild Bull Drift (+0.5 to +1.0 ATR)", "x_p in [0.52, 0.65]", "x_v in [0.35, 0.65]", "Routine upward drift"),
    ("B5 [0.5 - 0.6]: Upward Chop (0.0 to +0.5 ATR)", "x_p in [0.48, 0.55]", "x_v in [0.20, 0.50]", "Resting balance / noise"),
    ("B4 [0.4 - 0.5]: Downward Chop (-0.5 to 0.0 ATR)", "x_p in [0.45, 0.52]", "x_v in [0.20, 0.50]", "Resting balance / noise"),
    ("B3 [0.3 - 0.4]: Mild Bear Drift (-1.0 to -0.5 ATR)", "x_p in [0.35, 0.48]", "x_v in [0.35, 0.65]", "Routine downward drift"),
    ("B2 [0.2 - 0.3]: Moderate Bear (-1.7 to -1.0 ATR)", "x_p in [0.25, 0.42]", "x_v in [0.45, 0.75]", "Normal bearish supply"),
    ("B1 [0.1 - 0.2]: Strong Breakdown (-2.6 to -1.7 ATR)", "x_p in [0.15, 0.35]", "x_v in [0.55, 0.90]", "Heavy institutional selling"),
    ("B0 [0.0 - 0.1]: Severe Crash (< -2.6 ATR)", "x_p in [0.00, 0.25]", "x_v in [0.65, 1.00]", "Panic liquidation / breakdown")
]

y_p = 0.80
for b_name, p_range, v_range, note in table_lines:
    is_extreme = ('B9' in b_name or 'B0' in b_name)
    c_txt = '#4ade80' if 'Bull' in b_name else ('#f87171' if ('Bear' in b_name or 'Crash' in b_name or 'Breakdown' in b_name) else '#94a3b8')
    fw = 'bold' if is_extreme else 'normal'
    ax3.text(0.04, y_p, b_name, color=c_txt, fontsize=8.0, fontweight=fw)
    ax3.text(0.04, y_p - 0.035, f"Required: {p_range}  |  {v_range}  ({note})", color='#64748b', fontsize=7.2)
    y_p -= 0.075

plt.savefig('charts/unit_scaled_target_brackets.png', dpi=150)
plt.close()
print("Saved charts/unit_scaled_target_brackets.png")
