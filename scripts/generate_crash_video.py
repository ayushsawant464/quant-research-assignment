import json
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.animation as anim
from matplotlib.gridspec import GridSpec

print("Loading dataset for video rendering...")
with open('charts/crash_forensics_data.json') as f:
    records = json.load(f)

N = len(records)
df = pd.DataFrame(records)

# Setup 16:9 Full HD canvas
fig = plt.figure(figsize=(19.2, 10.8), facecolor='#0b0f19', dpi=100)
gs = GridSpec(4, 2, width_ratios=[0.67, 0.33], hspace=0.22, wspace=0.14,
              left=0.06, right=0.96, top=0.93, bottom=0.06)

# Left Column: Charts
ax_price = fig.add_subplot(gs[0, 0])
ax_price.set_facecolor('#111625')
ax_price.grid(True, color='#1f2638', linestyle='--', alpha=0.6)

ax_kin = fig.add_subplot(gs[1, 0], sharex=ax_price)
ax_kin.set_facecolor('#111625')
ax_kin.grid(True, color='#1f2638', linestyle='--', alpha=0.6)

ax_model = fig.add_subplot(gs[2, 0], sharex=ax_price)
ax_model.set_facecolor('#111625')
ax_model.grid(True, color='#1f2638', linestyle='--', alpha=0.6)

ax_pnl = fig.add_subplot(gs[3, 0], sharex=ax_price)
ax_pnl.set_facecolor('#111625')
ax_pnl.grid(True, color='#1f2638', linestyle='--', alpha=0.6)

# Right Column: Neural Cockpit HUD
ax_hud = fig.add_subplot(gs[:, 1])
ax_hud.set_facecolor('#0d121f')
ax_hud.axis('off')
ax_hud.set_xlim(0, 1)
ax_hud.set_ylim(0, 1)

# Pre-plot Full Lines on Left Subplots
x_axis = np.arange(N)

# 1. Price
ax_price.plot(x_axis, df['close'], color='#58a6ff', lw=1.8, label='Nifty 50 Close')
ax_price.plot(x_axis, df['h50'], color='#3fb950', lw=1.0, ls='--', alpha=0.7, label='H50 Breakout')
ax_price.plot(x_axis, df['l25'], color='#f85149', lw=1.0, ls='--', alpha=0.7, label='L25 Breakdown')
ax_price.plot(x_axis, df['etrend'], color='#d29922', lw=1.2, ls='-', alpha=0.7, label='EMA 150 Macro')
ax_price.set_ylabel('Price', fontsize=9, fontweight='bold', color='#8b949e')
ax_price.set_title('PRICE & STRATEGY EXECUTION REGIME', fontsize=10, fontweight='bold', color='#c9d1d9', loc='left')
ax_price.legend(loc='lower left', facecolor='#161b22', edgecolor='#30363d', fontsize=7.5, ncol=4)
ax_price.tick_params(labelbottom=False, colors='#8b949e', labelsize=8)

# 2. Kinematics
ax_kin.plot(x_axis, df['vel'], color='#38bdf8', lw=1.2, label='Velocity v (ΔP/ATR)')
ax_kin.plot(x_axis, df['acc'], color='#f43f5e', lw=1.0, ls='--', alpha=0.85, label='Acceleration a (Δv)')
ax_kin.axhline(0, color='#6e7681', lw=0.6, ls=':')
ax_kin.axhline(-2.0, color='#ff7b72', lw=0.8, ls='--', alpha=0.7, label='Alert a < -2.0')
ax_kin.set_ylabel('Kinematics', fontsize=9, fontweight='bold', color='#8b949e')
ax_kin.legend(loc='lower left', facecolor='#161b22', edgecolor='#30363d', fontsize=7.5, ncol=3)
ax_kin.tick_params(labelbottom=False, colors='#8b949e', labelsize=8)

# 3. Model Predictor
ax_model.plot(x_axis, df['base'], color='#818cf8', lw=1.0, label='Base PLS (X·β)')
ax_model.plot(x_axis, df['final'], color='#fbbf24', lw=1.5, label='Final Pred ŷ')
ax_model.axhline(0.05, color='#34d399', lw=0.8, ls=':', label='Threshold ±0.05')
ax_model.axhline(-0.05, color='#f87171', lw=0.8, ls=':')
ax_model.axhline(0.0, color='#6e7681', lw=0.6)
ax_model.set_ylabel('Prediction', fontsize=9, fontweight='bold', color='#8b949e')
ax_model.legend(loc='lower left', facecolor='#161b22', edgecolor='#30363d', fontsize=7.5, ncol=3)
ax_model.tick_params(labelbottom=False, colors='#8b949e', labelsize=8)

# 4. PnL
ax_pnl.plot(x_axis, df['strat_cum'], color='#3fb950', lw=1.8, label='Task 1 Strategy (+18.3%)')
ax_pnl.plot(x_axis, df['bnh_cum'], color='#f85149', lw=1.5, ls='--', label='Nifty Buy & Hold (-28.2%)')
ax_pnl.axhline(0.0, color='#6e7681', lw=0.6)
ax_pnl.set_ylabel('Cum Ret %', fontsize=9, fontweight='bold', color='#8b949e')
ax_pnl.set_xlabel('15-Minute Bar Index (Feb 17 - Mar 27, 2020)', fontsize=9, fontweight='bold', color='#8b949e')
ax_pnl.legend(loc='upper left', facecolor='#161b22', edgecolor='#30363d', fontsize=7.5, ncol=2)
ax_pnl.tick_params(colors='#8b949e', labelsize=8)

# Vertical Sync Cursors
cur_p = ax_price.axvline(0, color='#ffffff', lw=1.4, ls='-')
cur_k = ax_kin.axvline(0, color='#ffffff', lw=1.4, ls='-')
cur_m = ax_model.axvline(0, color='#ffffff', lw=1.4, ls='-')
cur_e = ax_pnl.axvline(0, color='#ffffff', lw=1.4, ls='-')

dot_p, = ax_price.plot([0], [df.loc[0, 'close']], marker='o', markersize=6, color='#ffffff')
dot_k, = ax_kin.plot([0], [df.loc[0, 'vel']], marker='o', markersize=5, color='#38bdf8')
dot_m, = ax_model.plot([0], [df.loc[0, 'final']], marker='o', markersize=5, color='#fbbf24')
dot_e, = ax_pnl.plot([0], [df.loc[0, 'strat_cum']], marker='o', markersize=5, color='#3fb950')

# Setup Static HUD Geometry & Dynamic Text Objects
# HUD Title
ax_hud.text(0.5, 0.97, "QUANT COCKPIT: EVENT TELEMETRY", color='#f0f6fc',
            fontsize=12, fontweight='bold', ha='center', va='top')
ax_hud.text(0.5, 0.94, "Pause video at any frame to inspect exact variables",
            color='#8b949e', fontsize=8, ha='center', va='top')

# Section 1: Telemetry Panel
rect_tel = Rectangle((0.04, 0.70), 0.92, 0.22, facecolor='#161b26', edgecolor='#30363d', lw=1.2)
ax_hud.add_patch(rect_tel)

txt_time = ax_hud.text(0.08, 0.885, "", color='#58a6ff', fontsize=10, fontweight='bold', va='center')
txt_px = ax_hud.text(0.08, 0.845, "", color='#ffffff', fontsize=9.5, va='center')
txt_kin = ax_hud.text(0.08, 0.805, "", color='#e6edf3', fontsize=9, va='center')
txt_model = ax_hud.text(0.08, 0.765, "", color='#e6edf3', fontsize=9, va='center')
txt_state = ax_hud.text(0.08, 0.725, "", color='#ffffff', fontsize=9.5, fontweight='bold', va='center')

# Section 2: Neural Excitation Meters Header
ax_hud.text(0.5, 0.665, "NEURON EXCITATION GAUGES [0.0 - 1.0]", color='#f0f6fc',
            fontsize=10.5, fontweight='bold', ha='center', va='center')

# 8 Horizontal Bar Gauges
neuron_labels = [
    "1. Velocity Surge",
    "2. Downside Accel",
    "3. Jerk Shock",
    "4. Range Expansion",
    "5. Macro Divergence",
    "6. Mod 2 Exhaustion",
    "7. Stall / Desync",
    "8. CRASH COMPOSITE"
]

bar_y_positions = np.linspace(0.60, 0.12, 8)
bg_rects = []
fill_rects = []
val_texts = []
lbl_texts = []

for idx, y_pos in enumerate(bar_y_positions):
    # Label
    is_crash = (idx == 7)
    c_lbl = '#fb923c' if is_crash else '#8b949e'
    fw = 'bold' if is_crash else 'normal'
    lbl = ax_hud.text(0.05, y_pos, neuron_labels[idx], color=c_lbl, fontsize=8.5,
                      fontweight=fw, va='center')
    lbl_texts.append(lbl)
    
    # Background bar
    bg = Rectangle((0.44, y_pos - 0.016), 0.40, 0.032, facecolor='#21262d', edgecolor='#30363d', lw=0.8)
    ax_hud.add_patch(bg)
    bg_rects.append(bg)
    
    # Active fill bar
    fill = Rectangle((0.44, y_pos - 0.016), 0.01, 0.032, facecolor='#3fb950')
    ax_hud.add_patch(fill)
    fill_rects.append(fill)
    
    # Value text
    val_txt = ax_hud.text(0.86, y_pos, "0.00", color='#c9d1d9', fontsize=8.5,
                          fontweight='bold', va='center')
    val_texts.append(val_txt)

# Footer Info
ax_hud.text(0.5, 0.05, "Green: <0.40 (Resting) | Yellow: 0.40-0.70 (Alert) | Red: >0.70 (FIRING)",
            color='#6e7681', fontsize=7.5, ha='center', va='center')

# Update Animation Function
def update_frame(frame_idx):
    row = df.iloc[frame_idx]
    
    # Update Cursors
    cur_p.set_xdata([frame_idx])
    cur_k.set_xdata([frame_idx])
    cur_m.set_xdata([frame_idx])
    cur_e.set_xdata([frame_idx])
    
    dot_p.set_data([frame_idx], [row['close']])
    dot_k.set_data([frame_idx], [row['vel']])
    dot_m.set_data([frame_idx], [row['final']])
    dot_e.set_data([frame_idx], [row['strat_cum']])
    
    # Update Telemetry Text
    pos_str = "LONG (+1.0)" if row['pos'] == 1 else ("SHORT (-1.0)" if row['pos'] == -1 else "FLAT / CASH (0.0)")
    c_pos = '#3fb950' if row['pos'] == 1 else ('#f85149' if row['pos'] == -1 else '#8b949e')
    stall_display = f"{int(row['stall'])}/6" if row['pos'] != 0 else "0/6 (Flat)"
    
    txt_time.set_text(f"TIME: {row['time']} | Bar #{frame_idx}")
    txt_px.set_text(f"Price: {row['close']:,.1f} | ATR: {row['atr']:.1f} | H50: {row['h50']:.1f} | L25: {row['l25']:.1f}")
    txt_kin.set_text(f"Kinematics:  Vel: {row['vel']:+.2f}  |  Acc: {row['acc']:+.2f}  |  Jerk: {row['jerk']:+.2f}")
    txt_model.set_text(f"Model:  Base: {row['base']:+.3f}  |  Mod2: {row['m2']:.2f}  |  Final: {row['final']:+.3f}")
    txt_state.set_text(f"State: {pos_str}  |  Stall: {stall_display}")
    txt_state.set_color(c_pos)
    
    # Update 8 Neuron Excitation Gauges
    e_vals = [
        row['e_vel'], row['e_acc'], row['e_jerk'], row['e_vol'],
        row['e_macro'], row['e_mod2'], row['e_stall'], row['e_crash']
    ]
    
    for idx, e in enumerate(e_vals):
        w = max(0.005, min(0.40, e * 0.40))
        fill_rects[idx].set_width(w)
        
        # Color coding
        if e < 0.40:
            fc = '#3fb950' # Green
            status = ""
        elif e < 0.70:
            fc = '#d29922' # Yellow/Amber
            status = " [ALERT]"
        else:
            fc = '#f85149' # Red
            status = " [FIRE!]"
            
        fill_rects[idx].set_facecolor(fc)
        val_texts[idx].set_text(f"{e:.2f}{status}")
        val_texts[idx].set_color(fc if e >= 0.40 else '#c9d1d9')

print("Starting video encoding to charts/crash_forensics_cockpit.mp4 (700 frames @ 15 FPS)...")
t0 = time.time()
ani = anim.FuncAnimation(fig, update_frame, frames=N, interval=66)
ani.save('charts/crash_forensics_cockpit.mp4', writer='ffmpeg', fps=15, bitrate=2500)
t1 = time.time()
print(f"Video generation successful in {t1 - t0:.1f} seconds!")
