import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates

# Load prepared data
with open('charts/crash_forensics_data.json') as f:
    records = json.load(f)

df = pd.DataFrame(records)
df['dt'] = pd.to_datetime(df['time'])

fig = plt.figure(figsize=(20, 18), facecolor='#0d1117')
gs = GridSpec(5, 1, height_ratios=[3.0, 1.8, 1.8, 1.6, 1.8], hspace=0.15)

# Style helper
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['text.color'] = '#c9d1d9'
plt.rcParams['axes.labelcolor'] = '#8b949e'
plt.rcParams['xtick.color'] = '#8b949e'
plt.rcParams['ytick.color'] = '#8b949e'

# 1. Price Panel
ax0 = fig.add_subplot(gs[0])
ax0.set_facecolor('#161b22')
ax0.grid(True, color='#21262d', linestyle='--', alpha=0.7)

# Shade Position Regimes
for i in range(len(df) - 1):
    pos = df.loc[i, 'pos']
    if pos == 1:
        ax0.axvspan(df.loc[i, 'dt'], df.loc[i+1, 'dt'], color='#238636', alpha=0.25)
    elif pos == -1:
        ax0.axvspan(df.loc[i, 'dt'], df.loc[i+1, 'dt'], color='#da3633', alpha=0.25)

ax0.plot(df['dt'], df['close'], color='#58a6ff', lw=2.2, label='Nifty 50 Futures (15m Close)')
ax0.plot(df['dt'], df['h50'], color='#7ee787', lw=1.2, ls='--', alpha=0.8, label='H50 Channel (Long Breakout)')
ax0.plot(df['dt'], df['l25'], color='#f85149', lw=1.2, ls='--', alpha=0.8, label='L25 Channel (Short Breakdown)')
ax0.plot(df['dt'], df['etrend'], color='#d29922', lw=1.5, ls='-', alpha=0.8, label='EMA 150 Macro Baseline')

# Key Annotations
p_a = df[df['time'] == '2020-02-19 10:15'].iloc[0]
p_b = df[df['time'] == '2020-02-24 09:15'].iloc[0]
p_c = df[df['time'] == '2020-03-09 09:15'].iloc[0]
p_d = df[df['time'] == '2020-03-24 09:15'].iloc[0]

ax0.annotate('Point A: Deceleration Stall\nVel=0.13, Acc=-0.57\nModel pulls to Cash (0.0)', 
             xy=(p_a['dt'], p_a['close']), xytext=(p_a['dt'] - pd.Timedelta(days=4), p_a['close'] + 400),
             arrowprops=dict(facecolor='#d29922', shrink=0.08, width=1.5, headwidth=7),
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#161b22', edgecolor='#d29922', alpha=0.9),
             fontsize=9, color='#e6edf3', fontweight='bold')

ax0.annotate('Point B: Gap Down & Rupture!\nVel=-4.65, Acc=-4.58 (Max Decel)\nALL Neurons Fire 1.0 -> SHORT (-1)', 
             xy=(p_b['dt'], p_b['close']), xytext=(p_b['dt'] + pd.Timedelta(days=1), p_b['close'] + 350),
             arrowprops=dict(facecolor='#f85149', shrink=0.08, width=1.5, headwidth=7),
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#161b22', edgecolor='#f85149', alpha=0.9),
             fontsize=9, color='#ff7b72', fontweight='bold')

ax0.annotate('Point C: Crude War Gap Down\nClose: 10,400 -> Short Harvested', 
             xy=(p_c['dt'], p_c['close']), xytext=(p_c['dt'] + pd.Timedelta(days=1), p_c['close'] + 500),
             arrowprops=dict(facecolor='#a371f7', shrink=0.08, width=1.5, headwidth=7),
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#161b22', edgecolor='#a371f7', alpha=0.9),
             fontsize=9, color='#d2a8ff', fontweight='bold')

ax0.annotate('Point D: Climax Bottom 7,573\nMod 2 halts premature dip-buying', 
             xy=(p_d['dt'], p_d['close']), xytext=(p_d['dt'] - pd.Timedelta(days=5), p_d['close'] - 500),
             arrowprops=dict(facecolor='#3fb950', shrink=0.08, width=1.5, headwidth=7),
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#161b22', edgecolor='#3fb950', alpha=0.9),
             fontsize=9, color='#7ee787', fontweight='bold')

ax0.set_ylabel('Nifty 50 Futures', fontsize=11, fontweight='bold')
ax0.set_title('PHASE 46 QUANT PIPELINE FORENSICS: THE GREAT COVID CRASH DETECTABILITY & KINEMATICS', 
              fontsize=14, fontweight='bold', color='#f0f6fc', pad=12)
ax0.legend(loc='lower left', facecolor='#161b22', edgecolor='#30363d', fontsize=9)
ax0.tick_params(labelbottom=False)

# 2. Kinematics Panel: Velocity & Acceleration
ax1 = fig.add_subplot(gs[1], sharex=ax0)
ax1.set_facecolor('#161b22')
ax1.grid(True, color='#21262d', linestyle='--', alpha=0.7)

ax1.plot(df['dt'], df['vel'], color='#38bdf8', lw=1.5, label='Velocity v = ΔP / ATR')
ax1.plot(df['dt'], df['acc'], color='#f43f5e', lw=1.2, ls='--', alpha=0.85, label='Acceleration a = Δv (Leading Inflection)')
ax1.axhline(0, color='#8b949e', lw=0.8, ls=':')
ax1.axhline(-2.0, color='#ff7b72', lw=1.2, ls='--', alpha=0.7, label='Severe Deceleration Alert (a < -2.0σ)')
ax1.fill_between(df['dt'], df['acc'], -2.0, where=(df['acc'] < -2.0), color='#f43f5e', alpha=0.35)

ax1.set_ylabel('Kinematics (ATR / Bar)', fontsize=10, fontweight='bold')
ax1.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', fontsize=8.5)
ax1.tick_params(labelbottom=False)

# 3. Predictors & Modulators
ax2 = fig.add_subplot(gs[2], sharex=ax0)
ax2.set_facecolor('#161b22')
ax2.grid(True, color='#21262d', linestyle='--', alpha=0.7)

ax2.plot(df['dt'], df['base'], color='#818cf8', lw=1.3, label='Base PLS Linear (X · β)')
ax2.plot(df['dt'], df['final'], color='#fbbf24', lw=1.8, label='Final Modulated Prediction ŷ')
ax2.axhline(0.05, color='#34d399', lw=1.0, ls=':', label='Activation Thresholds (±0.05)')
ax2.axhline(-0.05, color='#f87171', lw=1.0, ls=':')
ax2.axhline(0.0, color='#8b949e', lw=0.7, ls='-')
ax2.axhline(1.449, color='#94a3b8', lw=0.8, ls='--', label='Kurtosis MAD Bounds [-1.41, +1.45]')
ax2.axhline(-1.414, color='#94a3b8', lw=0.8, ls='--')

ax2.set_ylabel('Model Predictors', fontsize=10, fontweight='bold')
ax2.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', fontsize=8.5)
ax2.tick_params(labelbottom=False)

# 4. Neuron Excitation Heatmap / Activity Tracks
ax3 = fig.add_subplot(gs[3], sharex=ax0)
ax3.set_facecolor('#161b22')
ax3.grid(True, color='#21262d', linestyle='--', alpha=0.7)

# Plot top key neuron activations: E_acc, E_jerk, E_vol, E_crash
ax3.plot(df['dt'], df['e_acc'], color='#f87171', lw=1.3, label='⚡ Downside Acc Neuron [0-1]')
ax3.plot(df['dt'], df['e_jerk'], color='#c084fc', lw=1.1, label='💥 Jerk Shock Neuron [0-1]')
ax3.plot(df['dt'], df['e_vol'], color='#38bdf8', lw=1.1, label='🌊 Range Expansion Neuron [0-1]')
ax3.plot(df['dt'], df['e_crash'], color='#fb923c', lw=2.2, label='🚨 COMPOSITE CRASH NEURON [0-1]')

ax3.axhline(0.70, color='#f85149', lw=1.2, ls='--', alpha=0.8, label='Neuron Firing Threshold (0.70)')
ax3.fill_between(df['dt'], df['e_crash'], 0.70, where=(df['e_crash'] >= 0.70), color='#f85149', alpha=0.3)

ax3.set_ylabel('Neuron Excitation [0-1]', fontsize=10, fontweight='bold')
ax3.set_ylim(-0.05, 1.05)
ax3.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', fontsize=8.5)
ax3.tick_params(labelbottom=False)

# 5. Cumulative Strategy Return vs Benchmark Buy & Hold
ax4 = fig.add_subplot(gs[4], sharex=ax0)
ax4.set_facecolor('#161b22')
ax4.grid(True, color='#21262d', linestyle='--', alpha=0.7)

ax4.plot(df['dt'], df['strat_cum'], color='#3fb950', lw=2.4, label='Adapted Task 1 Strategy (+18.30% Return)')
ax4.plot(df['dt'], df['bnh_cum'], color='#f85149', lw=2.0, ls='--', label='Nifty 50 Buy & Hold (-28.24% Drawdown)')
ax4.axhline(0.0, color='#8b949e', lw=0.8)

ax4.set_ylabel('Cumulative Return (%)', fontsize=10, fontweight='bold')
ax4.set_xlabel('Timestamp (15-Minute Bars)', fontsize=11, fontweight='bold')
ax4.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax4.legend(loc='upper left', facecolor='#161b22', edgecolor='#30363d', fontsize=9.5)

plt.tight_layout()
plt.savefig('charts/crash_forensics_detailed_annotated.png', dpi=200, bbox_inches='tight')
plt.close()
print("Saved charts/crash_forensics_detailed_annotated.png")
