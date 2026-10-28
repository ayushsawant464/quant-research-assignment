import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import harness_public as harness
import task1_backup as t1_asym
import strategy_experiments.task1_multi_ema_conservative as t1_multi_ema
import task2_backup as t2_multi_tf

os.makedirs('charts', exist_ok=True)

# 1. Backtest Task 1 Multi-EMA on Full 10-Year Data
bars_fl = harness.load_bars('data/nifty50_15min_full_2017-04-03_2026-10-26.csv')
exp_fl = harness.load_expiries('data/nifty_monthly_expiries_2017-01_2026-10.csv')

pos_t1_ema = t1_multi_ema.positions(bars_fl, t1_multi_ema.PARAMS)
res_t1_ema = harness.task1_backtest(bars_fl, pos_t1_ema, exp_fl)
s_t1_ema, eq_t1_ema = harness.task1_stats(res_t1_ema)
dd_t1_ema = eq_t1_ema / eq_t1_ema.cummax() - 1.0

pos_t1_asym = t1_asym.positions(bars_fl, t1_asym.PARAMS)
res_t1_asym = harness.task1_backtest(bars_fl, pos_t1_asym, exp_fl)
s_t1_asym, eq_t1_asym = harness.task1_stats(res_t1_asym)
dd_t1_asym = eq_t1_asym / eq_t1_asym.cummax() - 1.0

# 2. Backtest Task 2 Multi-Timeframe EMA Ribbon on Full Data
D_full = harness.load_stocks(
    ['data/stocks_daily_full_2021-04-26_2026-10-26.csv'],
    ['data/nifty50_daily_full_2021-04-26_2026-10-26.csv']
)
res_t2 = harness.task2_backtest(t2_multi_tf, D_full, t2_multi_tf.PARAMS, harness.T2_START, None)
s_t2_fl, eq_t2 = harness.task2_stats(res_t2)
dd_t2 = eq_t2 / eq_t2.cummax() - 1.0

# Setup 4-Panel High-Resolution Figure
plt.style.use('dark_background')
fig = plt.figure(figsize=(18, 12), dpi=200)
gs = gridspec.GridSpec(2, 2, height_ratios=[1.2, 1], hspace=0.30, wspace=0.22,
                       left=0.06, right=0.96, top=0.92, bottom=0.07)

t1_cutoff = pd.Timestamp('2022-01-31')
t2_cutoff = pd.Timestamp('2024-06-30')

# -----------------------------------------------------------------------------
# Panel 1: Task 1 Multi-Timeframe Equity Curves (Full 10 Years)
# -----------------------------------------------------------------------------
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(eq_t1_ema.index, eq_t1_ema.values, color='#00e676', lw=2.2, label='Multi-Timeframe EMA (20 / 50 / 750 bars)')
ax1.plot(eq_t1_asym.index, eq_t1_asym.values, color='#ff9100', lw=1.5, alpha=0.85, label='Asymmetric Channel (50 / 25 / 150 bars)')
ax1.axvline(t1_cutoff, color='#ffeb3b', linestyle='--', lw=1.8, label='In-Sample / OOS Cutoff (2022-01-31)')
ax1.set_title("Task 1: Multi-Timeframe Strategies (10-Year Cumulative Equity)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax1.set_ylabel("Portfolio Value (Base = 1.0)", fontsize=11, color='#cfd8dc')
ax1.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax1.legend(loc='upper left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

stats_box1 = (
    "Multi-EMA Strategy:\n"
    "  • In-Sample CAGR: 16.10% | Max DD: -4.77%\n"
    "  • Out-of-Sample CAGR: 9.65% | Max DD: -5.28%\n"
    "  • Full 10-Yr CAGR: 12.86% | Full Max DD: -5.28%\n"
    "Asymmetric Channel Breakout:\n"
    "  • In-Sample CAGR: 26.93% | Max DD: -7.81%\n"
    "  • Out-of-Sample CAGR: 6.19% | Max DD: -18.22%"
)
ax1.text(0.03, 0.40, stats_box1, transform=ax1.transAxes, fontsize=9.5, family='monospace',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='#1e272c', edgecolor='#00e676', alpha=0.9))

# -----------------------------------------------------------------------------
# Panel 2: Task 1 Underwater Drawdowns (Full 10 Years)
# -----------------------------------------------------------------------------
ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(dd_t1_ema.index, dd_t1_ema.values * 100, color='#00e676', lw=1.8, label='Multi-EMA Drawdown (Max -5.28%)')
ax2.plot(dd_t1_asym.index, dd_t1_asym.values * 100, color='#ff9100', lw=1.2, alpha=0.75, label='Asymmetric Channel (Max -18.22%)')
ax2.axhline(-15.0, color='#ff1744', linestyle='-', lw=2.0, label='Mandate Ceiling (-15.0%)')
ax2.axvline(t1_cutoff, color='#ffeb3b', linestyle='--', lw=1.8)
ax2.set_title("Task 1: Underwater Drawdown Profiles (Mandate Compliance Check)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax2.set_ylabel("Drawdown (%)", fontsize=11, color='#cfd8dc')
ax2.set_ylim(-22.0, 1.0)
ax2.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax2.legend(loc='lower left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

# -----------------------------------------------------------------------------
# Panel 3: Task 2 Multi-Timeframe EMA Ribbon Equity Curve
# -----------------------------------------------------------------------------
ax3 = fig.add_subplot(gs[0, 1])
ax3.plot(eq_t2.index, eq_t2.values, color='#00b0ff', lw=2.2, label='Task 2: Multi-Timeframe EMA Ribbon & Momentum')
ax3.axvline(t2_cutoff, color='#ffeb3b', linestyle='--', lw=1.8, label='In-Sample / OOS Cutoff (2024-06-30)')
ax3.set_title("Task 2: Multi-Timeframe EMA Ribbon (Full Horizon Equity)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax3.set_ylabel("Portfolio Value (Base = 1.0)", fontsize=11, color='#cfd8dc')
ax3.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax3.legend(loc='upper left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

stats_box2 = (
    "In-Sample (2022 to 2024):\n"
    "  • CAGR: 82.21% | Sharpe: 2.724\n"
    "  • Total Return: +303.37%\n"
    "  • Max Drawdown: -16.42%\n"
    "Out-of-Sample (2024 to 2026):\n"
    "  • CAGR: 10.88% | Sharpe: 0.602\n"
    "  • Total Return: +27.06%\n"
    "  • Max Drawdown: -34.38%\n"
    "Full Horizon (2022 to 2026):\n"
    "  • CAGR: 42.76% | Total: +423.73% (5.2x)"
)
ax3.text(0.03, 0.45, stats_box2, transform=ax3.transAxes, fontsize=9.5, family='monospace',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='#1e272c', edgecolor='#00b0ff', alpha=0.9))

# -----------------------------------------------------------------------------
# Panel 4: Task 2 Underwater Drawdown Curve
# -----------------------------------------------------------------------------
ax4 = fig.add_subplot(gs[1, 1])
ax4.fill_between(dd_t2.index, dd_t2.values * 100, 0, color='#00b0ff', alpha=0.35)
ax4.plot(dd_t2.index, dd_t2.values * 100, color='#00b0ff', lw=1.6, label='Task 2 Drawdown (%)')
ax4.axhline(-15.0, color='#ff1744', linestyle='-', lw=2.0, label='Mandate Ceiling (-15.0%)')
ax4.axvline(t2_cutoff, color='#ffeb3b', linestyle='--', lw=1.8, label='OOS Cutoff')
ax4.set_title("Task 2: Underwater Drawdown Profile (In-Sample vs Out-of-Sample)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax4.set_ylabel("Drawdown (%)", fontsize=11, color='#cfd8dc')
ax4.set_ylim(-38.0, 1.0)
ax4.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax4.legend(loc='lower left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

fig.suptitle("OUT-OF-SAMPLE FORENSIC AUDIT: MULTI-TIMEFRAME STRATEGIES (TASK 1 & TASK 2)", fontsize=16, weight='bold', color='#eceff1', y=0.97)

out_path = 'charts/multi_timeframe_oos_audit.png'
plt.savefig(out_path, dpi=200)
plt.close()
print(f"Chart saved successfully to {out_path}!")
