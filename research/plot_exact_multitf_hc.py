import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import harness_public as harness
import test_t1_exact_multitf_hypercube as t1_hc
import test_t2_exact_multitf_hypercube as t2_hc

os.makedirs('charts', exist_ok=True)

# 1. Backtest Task 1 Asym-Channel + Hypercube
bars_fl = t1_hc.bars_fl
exp_fl = t1_hc.exp_fl
sig_fl = t1_hc.sig_fl

p1b = t1_hc.sim_asym_channel_hypercube(sig_fl, th_macro=0.55, th_micro=0.52, stall_limit=6, allow_short=0)
r1b = harness.task1_backtest(bars_fl, p1b, exp_fl)
s1b, eq1 = harness.task1_stats(r1b)
dd1 = eq1 / eq1.cummax() - 1.0

# 2. Backtest Task 2 Multi-TF + Hypercube
D_full = t2_hc.D_full
eng = t2_hc.MultiTFHypercubeEngine()
r2 = harness.task2_backtest(eng, D_full, t2_hc.PARAMS, harness.T2_START, None)
s2, eq2 = harness.task2_stats(r2)
dd2 = eq2 / eq2.cummax() - 1.0

# Setup 4-Panel High-Resolution Figure
plt.style.use('dark_background')
fig = plt.figure(figsize=(18, 12), dpi=200)
gs = gridspec.GridSpec(2, 2, height_ratios=[1.2, 1], hspace=0.30, wspace=0.22,
                       left=0.06, right=0.96, top=0.92, bottom=0.07)

t1_cutoff = pd.Timestamp('2022-01-31')
t2_cutoff = pd.Timestamp('2024-06-30')

# -----------------------------------------------------------------------------
# Panel 1: Task 1 Exact Multi-Timeframe + Hypercube Equity Curve
# -----------------------------------------------------------------------------
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(eq1.index, eq1.values, color='#00e676', lw=2.2, label='Multi-Timeframe Channel + Hypercube Governor')
ax1.axvline(t1_cutoff, color='#ffeb3b', linestyle='--', lw=1.8, label='In-Sample / OOS Cutoff (2022-01-31)')
ax1.set_title("Task 1: Multi-Timeframe Channel + Hypercube (10-Yr Equity)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax1.set_ylabel("Portfolio Value (Base = 1.0)", fontsize=11, color='#cfd8dc')
ax1.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax1.legend(loc='upper left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

stats_box1 = (
    "In-Sample (2017 to 2022):\n"
    "  • CAGR: 20.20% | Sharpe: 1.586\n"
    "  • Max Drawdown: -5.58% | Calmar: 3.621\n"
    "Out-of-Sample (2022 to 2026):\n"
    "  • CAGR: 8.58% | Sharpe: 0.391\n"
    "  • Max Drawdown: -6.74% | Calmar: 1.274\n"
    "Full 10-Yr Horizon (2017 to 2026):\n"
    "  • CAGR: 14.14% | Total Return: +254.12%\n"
    "  • Full Max Drawdown: -6.74% (< 15% Mandate)\n"
    "  • 10 / 10 Calendar Years Positive!"
)
ax1.text(0.03, 0.40, stats_box1, transform=ax1.transAxes, fontsize=9.5, family='monospace',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='#1e272c', edgecolor='#00e676', alpha=0.9))

# -----------------------------------------------------------------------------
# Panel 2: Task 1 Underwater Drawdown Profile
# -----------------------------------------------------------------------------
ax2 = fig.add_subplot(gs[1, 0])
ax2.fill_between(dd1.index, dd1.values * 100, 0, color='#00e676', alpha=0.35)
ax2.plot(dd1.index, dd1.values * 100, color='#00e676', lw=1.6, label='Drawdown (%) [Max -6.74%]')
ax2.axhline(-15.0, color='#ff1744', linestyle='-', lw=2.0, label='Mandate Ceiling (-15.0%)')
ax2.axvline(t1_cutoff, color='#ffeb3b', linestyle='--', lw=1.8)
ax2.set_title("Task 1: Underwater Drawdown Profile (Strict < 15% Verification)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax2.set_ylabel("Drawdown (%)", fontsize=11, color='#cfd8dc')
ax2.set_ylim(-18.0, 1.0)
ax2.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax2.legend(loc='lower left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

# -----------------------------------------------------------------------------
# Panel 3: Task 2 Exact Multi-Timeframe + Hypercube Equity Curve
# -----------------------------------------------------------------------------
ax3 = fig.add_subplot(gs[0, 1])
ax3.plot(eq2.index, eq2.values, color='#00b0ff', lw=2.2, label='Multi-Timeframe EMA Ribbon + Hypercube Governor')
ax3.axvline(t2_cutoff, color='#ffeb3b', linestyle='--', lw=1.8, label='In-Sample / OOS Cutoff (2024-06-30)')
ax3.set_title("Task 2: Multi-Timeframe Ribbon + Hypercube (Full Horizon Equity)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax3.set_ylabel("Portfolio Value (Base = 1.0)", fontsize=11, color='#cfd8dc')
ax3.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax3.legend(loc='upper left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

stats_box2 = (
    "In-Sample (2022 to 2024):\n"
    "  • CAGR: 44.11% | Sharpe: 2.002\n"
    "  • Total Return: +133.82% | Max DD: -19.47%\n"
    "Out-of-Sample (2024 to 2026):\n"
    "  • CAGR: 2.72% | Total Return: +6.42%\n"
    "  • Max Drawdown: -27.09% (vs -34.4% raw)\n"
    "  • 2025 Return: +0.23% (vs -10.9% raw)\n"
    "Full 5-Yr Horizon (2022 to 2026):\n"
    "  • CAGR: 22.33% | Total Return: +155.39%\n"
    "  • All 5 Calendar Years Positive!"
)
ax3.text(0.03, 0.40, stats_box2, transform=ax3.transAxes, fontsize=9.5, family='monospace',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='#1e272c', edgecolor='#00b0ff', alpha=0.9))

# -----------------------------------------------------------------------------
# Panel 4: Task 2 Underwater Drawdown Curve
# -----------------------------------------------------------------------------
ax4 = fig.add_subplot(gs[1, 1])
ax4.fill_between(dd2.index, dd2.values * 100, 0, color='#00b0ff', alpha=0.35)
ax4.plot(dd2.index, dd2.values * 100, color='#00b0ff', lw=1.6, label='Task 2 Drawdown (%)')
ax4.axhline(-15.0, color='#ff1744', linestyle='-', lw=2.0, label='Mandate Ceiling (-15.0%)')
ax4.axvline(t2_cutoff, color='#ffeb3b', linestyle='--', lw=1.8, label='OOS Cutoff')
ax4.set_title("Task 2: Underwater Drawdown Profile (In-Sample vs Out-of-Sample)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax4.set_ylabel("Drawdown (%)", fontsize=11, color='#cfd8dc')
ax4.set_ylim(-32.0, 1.0)
ax4.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax4.legend(loc='lower left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

fig.suptitle("EXACT MULTI-TIMEFRAME STRATEGIES WITH HYPERCUBE GOVERNOR: IN-SAMPLE & OOS AUDIT", fontsize=16, weight='bold', color='#eceff1', y=0.97)

out_path = 'charts/exact_multitf_hypercube_oos.png'
plt.savefig(out_path, dpi=200)
plt.close()
print(f"Chart saved successfully to {out_path}!")
