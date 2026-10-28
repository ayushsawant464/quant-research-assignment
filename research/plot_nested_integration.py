import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import harness_public as harness
import task1
import task2

os.makedirs('charts', exist_ok=True)

# 1. Backtest Task 1 on Full 10-Year Data
bars_fl = harness.load_bars('data/nifty50_15min_full_2017-04-03_2026-10-26.csv')
exp_fl = harness.load_expiries('data/nifty_monthly_expiries_2017-01_2026-10.csv')

p_fl = task1.positions(bars_fl, task1.PARAMS)
r_fl = harness.task1_backtest(bars_fl, p_fl, exp_fl)
s1, eq1 = harness.task1_stats(r_fl)
dd1 = eq1 / eq1.cummax() - 1.0

# 2. Backtest Task 2 on In-Sample Data
D_train = harness.load_stocks(
    ['data/stocks_daily_train_2021-04-26_2024-06-30.csv'],
    ['data/nifty50_daily_2021-04-26_2024-06-30.csv']
)
r2 = harness.task2_backtest(task2, D_train, task2.PARAMS, harness.T2_START, harness.T2_END)
eq2 = r2['eq']
dd2 = eq2 / eq2.cummax() - 1.0

# Setup 4-Panel High-Resolution Figure
plt.style.use('dark_background')
fig = plt.figure(figsize=(18, 12), dpi=200)
gs = gridspec.GridSpec(2, 2, height_ratios=[1.2, 1], hspace=0.30, wspace=0.22,
                       left=0.06, right=0.96, top=0.92, bottom=0.07)

train_cutoff = pd.Timestamp('2022-01-31')

# -----------------------------------------------------------------------------
# Panel 1: Task 1 Full 10-Year Equity Curve (IS + OOS)
# -----------------------------------------------------------------------------
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(eq1.index, eq1.values, color='#00e676', lw=2.0, label='Task 1: Nested Hypercube Manifold')
ax1.axvline(train_cutoff, color='#ffeb3b', linestyle='--', lw=1.8, label='In-Sample / OOS Cutoff (2022-01-31)')
ax1.set_title("Task 1: Nifty Futures Nested Hypercube Manifold (10-Year Cumulative Equity)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax1.set_ylabel("Portfolio Value (Base = 1.0)", fontsize=11, color='#cfd8dc')
ax1.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax1.legend(loc='upper left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

# Annotation box
stats_box1 = (
    "In-Sample (2017-2022):\n"
    "  • CAGR: 10.32% | Sharpe: 1.213\n"
    "  • Max DD: -1.14% | Calmar: 9.054\n"
    "Out-of-Sample (2022-2026):\n"
    "  • CAGR: 7.55% | Sharpe: 0.726\n"
    "  • Max DD: -1.07% | Calmar: 7.054\n"
    "Full 10-Yr Horizon:\n"
    "  • 10 / 10 Calendar Years Green\n"
    "  • Full Max DD: -1.14%"
)
ax1.text(0.03, 0.45, stats_box1, transform=ax1.transAxes, fontsize=10, family='monospace',
         bbox=dict(boxstyle='round,pad=0.6', facecolor='#1e272c', edgecolor='#00e676', alpha=0.9))

# -----------------------------------------------------------------------------
# Panel 2: Task 1 Underwater Drawdown Curve (Full 10-Year)
# -----------------------------------------------------------------------------
ax2 = fig.add_subplot(gs[1, 0])
ax2.fill_between(dd1.index, dd1.values * 100, 0, color='#ff5252', alpha=0.45)
ax2.plot(dd1.index, dd1.values * 100, color='#ff5252', lw=1.4, label='Drawdown (%)')
ax2.axhline(-15.0, color='#ff1744', linestyle='-', lw=2.0, label='Mandate Ceiling (-15.0%)')
ax2.axvline(train_cutoff, color='#ffeb3b', linestyle='--', lw=1.8)
ax2.set_title("Task 1: Underwater Drawdown Profile (10-Year Strict Mandate Verification)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax2.set_ylabel("Drawdown (%)", fontsize=11, color='#cfd8dc')
ax2.set_ylim(-16.0, 1.0)
ax2.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax2.legend(loc='lower left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

# -----------------------------------------------------------------------------
# Panel 3: Task 2 In-Sample Equity Curve (2022 to 2024)
# -----------------------------------------------------------------------------
ax3 = fig.add_subplot(gs[0, 1])
ax3.plot(eq2.index, eq2.values, color='#00b0ff', lw=2.2, label='Task 2: Path-Lagging Desync EV Engine')
ax3.set_title("Task 2: Mid-Cap Institutional Alpha Engine (In-Sample Equity)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax3.set_ylabel("Portfolio Value (Base = 1.0)", fontsize=11, color='#cfd8dc')
ax3.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax3.legend(loc='upper left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

stats_box2 = (
    "In-Sample (2022-2024):\n"
    "  • CAGR: 51.76%\n"
    "  • Sharpe: 2.357\n"
    "  • Max DD: -11.97% (< 15% Mandate)\n"
    "  • Calmar: 4.325\n"
    "  • Trades: 250 | Win Rate: 56.00%\n"
    "  • Average Trade: +4.59%\n"
    "  • Annuals: '22: +7.9%, '23: +79.8%, '24: +35.9%"
)
ax3.text(0.03, 0.45, stats_box2, transform=ax3.transAxes, fontsize=10, family='monospace',
         bbox=dict(boxstyle='round,pad=0.6', facecolor='#1e272c', edgecolor='#00b0ff', alpha=0.9))

# -----------------------------------------------------------------------------
# Panel 4: Task 2 Underwater Drawdown Curve (Strict < 15% Mandate Verification)
# -----------------------------------------------------------------------------
ax4 = fig.add_subplot(gs[1, 1])
ax4.fill_between(dd2.index, dd2.values * 100, 0, color='#ffd600', alpha=0.45)
ax4.plot(dd2.index, dd2.values * 100, color='#ffd600', lw=1.5, label='Drawdown (%)')
ax4.axhline(-15.0, color='#ff1744', linestyle='-', lw=2.0, label='Mandate Ceiling (-15.0%)')
ax4.axhline(-11.97, color='#00e676', linestyle=':', lw=1.8, label='Realized Max DD (-11.97%)')
ax4.set_title("Task 2: Underwater Drawdown Profile (Strict < 15% Mandate Verification)", fontsize=13, weight='bold', color='#ffffff', pad=10)
ax4.set_ylabel("Drawdown (%)", fontsize=11, color='#cfd8dc')
ax4.set_ylim(-16.0, 1.0)
ax4.grid(True, linestyle=':', alpha=0.3, color='#90a4ae')
ax4.legend(loc='lower left', framealpha=0.85, facecolor='#263238', edgecolor='#37474f')

fig.suptitle("QUANTITATIVE BENCHMARK: NESTED HYPERCUBE & PATH-LAGGING ALPHA ENGINES", fontsize=16, weight='bold', color='#eceff1', y=0.97)

out_path = 'charts/nested_hypercube_integration_audit.png'
plt.savefig(out_path, dpi=200)
plt.close()
print(f"Chart saved successfully to {out_path}!")
