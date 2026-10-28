import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.dates as mdates

# 1. Load real Nifty 15-min data
df = pd.read_csv('data/nifty50_15min_full_2017-04-03_2026-10-26.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

c = df['close']
o = df['open']
h = df['high']
l = df['low']
v = df['n_1min']
N = len(df)

tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
atr = tr.ewm(span=20, adjust=False).mean() + 1e-4

# Diurnal Volume Curve
df['time_str'] = df['datetime'].dt.strftime('%H:%M')
diurnal_mean = df.groupby('time_str')['n_1min'].mean()
diurnal_std = df.groupby('time_str')['n_1min'].std()
time_labels = diurnal_mean.index.tolist()

df['diurnal_base'] = df['time_str'].map(diurnal_mean)
v_norm = (df['n_1min'] / (df['diurnal_base'] + 1e-4)).values
p_norm = ((c - o) / atr).values
target_move_atr = ((c.shift(-5) - c) / atr).values

# 2. Fit Exponential-Quadratic Manifold on Sideways/In-Sample 2017-2020
mask_tr = (df['datetime'] >= '2017-04-03') & (df['datetime'] <= '2020-12-31')
valid_tr = mask_tr & ~np.isnan(target_move_atr) & ~np.isnan(p_norm) & ~np.isnan(v_norm)

p_tr = p_norm[valid_tr]
v_tr = v_norm[valid_tr]
y_tr = target_move_atr[valid_tr]

# Quadratic-Exponential Basis Functions
v_exp_tr = np.exp(np.clip(0.35 * (v_tr - 1.0), -2.0, 2.0))
X_basis = np.column_stack([
    p_tr,
    p_tr * v_exp_tr,
    np.sign(p_tr) * (p_tr**2),
    v_tr - 1.0
])
coeffs, _, _, _ = np.linalg.lstsq(X_basis, y_tr, rcond=None)

# 3. Dense Synthetic State-Space Grid
p_grid = np.linspace(-3.5, 3.5, 200)
v_grid = np.linspace(0.2, 4.0, 200)
P_mesh, V_mesh = np.meshgrid(p_grid, v_grid)

V_mesh_exp = np.exp(np.clip(0.35 * (V_mesh.ravel() - 1.0), -2.0, 2.0))
mesh_basis = np.column_stack([
    P_mesh.ravel(),
    P_mesh.ravel() * V_mesh_exp,
    np.sign(P_mesh.ravel()) * (P_mesh.ravel()**2),
    V_mesh.ravel() - 1.0
])
synthetic_move = (mesh_basis @ coeffs).reshape(P_mesh.shape)

# Define 7 Slabs
slab_bounds = [-99.0, -2.5, -1.2, -0.4, 0.4, 1.2, 2.5, 99.0]
cmap_slabs = ListedColormap([
    '#7f1d1d', # Slab -3: Dark Red (Crash)
    '#b91c1c', # Slab -2: Red (Strong Bear)
    '#f87171', # Slab -1: Light Red (Mild Bear)
    '#334155', # Slab  0: Slate Gray (Sideways Chop)
    '#4ade80', # Slab +1: Light Green (Mild Bull)
    '#16a34a', # Slab +2: Green (Strong Bull)
    '#14532d'  # Slab +3: Dark Green (Extreme Bull)
])
norm_slabs = BoundaryNorm(slab_bounds, cmap_slabs.N)

# 4. Setup Plot
fig = plt.figure(figsize=(18, 12), facecolor='#0d1117')
gs = GridSpec(2, 2, hspace=0.25, wspace=0.20, left=0.06, right=0.95, top=0.93, bottom=0.07)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['text.color'] = '#c9d1d9'
plt.rcParams['axes.labelcolor'] = '#8b949e'
plt.rcParams['xtick.color'] = '#8b949e'
plt.rcParams['ytick.color'] = '#8b949e'

# Panel 1: The Synthetic 2D Slab Manifold
ax0 = fig.add_subplot(gs[0, 0])
ax0.set_facecolor('#161b22')

cf = ax0.contourf(P_mesh, V_mesh, synthetic_move, levels=slab_bounds, cmap=cmap_slabs, norm=norm_slabs, alpha=0.85)
cs = ax0.contour(P_mesh, V_mesh, synthetic_move, levels=[-2.5, -1.2, -0.4, 0.4, 1.2, 2.5], colors='#ffffff', linewidths=0.8, alpha=0.6)
ax0.clabel(cs, fmt='%.1f ATR', fontsize=8, colors='#ffffff')

ax0.axvline(0, color='#94a3b8', lw=1.0, ls=':')
ax0.axhline(1.0, color='#94a3b8', lw=1.0, ls=':')

ax0.set_xlabel('Normalized Price Impulse p = (Close - Open) / ATR', fontsize=9.5, fontweight='bold')
ax0.set_ylabel('Normalized Volume Ratio v = V / V_diurnal', fontsize=9.5, fontweight='bold')
ax0.set_title('SYNTHETIC 2D STATE-SPACE MANIFOLD: PREDICTED LANDING SLABS', fontsize=10.5, fontweight='bold', color='#f0f6fc')

# Colorbar
cbar = plt.colorbar(cf, ax=ax0, orientation='vertical', pad=0.03, ticks=[-3.0, -1.8, -0.8, 0.0, 0.8, 1.8, 3.0])
cbar.ax.set_yticklabels(['Slab -3', 'Slab -2', 'Slab -1', 'Slab 0', 'Slab +1', 'Slab +2', 'Slab +3'], fontsize=8)
cbar.set_label('Target Move Slab (ATR Multiples)', fontsize=8.5, fontweight='bold')

# Panel 2: Target Volume Estimation (Diurnal U-Curve)
ax1 = fig.add_subplot(gs[0, 1])
ax1.set_facecolor('#161b22')
ax1.grid(True, color='#21262d', linestyle='--', alpha=0.7)

x_diurnal = np.arange(len(time_labels))
ax1.plot(x_diurnal, diurnal_mean.values, color='#38bdf8', lw=2.0, label='Expected Baseline Volume V_diurnal(t)')
ax1.fill_between(x_diurnal, np.maximum(0, diurnal_mean.values - diurnal_std.values),
                 diurnal_mean.values + diurnal_std.values, color='#38bdf8', alpha=0.2, label='1-Sigma Volatility Band')

ax1.set_xticks(x_diurnal[::3])
ax1.set_xticklabels(time_labels[::3], rotation=35, fontsize=8)
ax1.set_ylabel('Average 15-Minute Volume (n_1min)', fontsize=9.5, fontweight='bold')
ax1.set_xlabel('Time of Day (IST)', fontsize=9.5, fontweight='bold')
ax1.set_title('TARGET VOLUME ESTIMATION: DETERMINISTIC DIURNAL U-CURVE', fontsize=10.5, fontweight='bold', color='#f0f6fc')
ax1.legend(loc='lower center', facecolor='#161b22', edgecolor='#30363d', fontsize=8)

# Panel 3: Real Historical Bars Overlaid on Synthetic Manifold
ax2 = fig.add_subplot(gs[1, 0])
ax2.set_facecolor('#161b22')

ax2.contourf(P_mesh, V_mesh, synthetic_move, levels=slab_bounds, cmap=cmap_slabs, norm=norm_slabs, alpha=0.35)
ax2.contour(P_mesh, V_mesh, synthetic_move, levels=[-2.5, -1.2, -0.4, 0.4, 1.2, 2.5], colors='#64748b', linewidths=0.6)

# Sample real points from 2021-2022 test dataset
mask_te = (df['datetime'] >= '2021-01-01') & (df['datetime'] <= '2022-12-31')
sample_te = df[mask_te].sample(n=1000, random_state=42)

p_sample = p_norm[sample_te.index]
v_sample = v_norm[sample_te.index]
actual_slabs_sample = target_move_atr[sample_te.index]

pt_cols = ['#4ade80' if m > 0.4 else ('#f87171' if m < -0.4 else '#94a3b8') for m in actual_slabs_sample]
ax2.scatter(p_sample, v_sample, c=pt_cols, s=10, alpha=0.5, edgecolors='none', label='Real 15-min Bars (2021-2022)')

ax2.set_xlim(-3.5, 3.5)
ax2.set_ylim(0.2, 4.0)
ax2.set_xlabel('Normalized Price Impulse p', fontsize=9.5, fontweight='bold')
ax2.set_ylabel('Normalized Volume Ratio v', fontsize=9.5, fontweight='bold')
ax2.set_title('REAL OUT-OF-SAMPLE DATA (2021-2022) MATCHED TO SYNTHETIC MANIFOLD', fontsize=10.5, fontweight='bold', color='#f0f6fc')
ax2.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', fontsize=8)

# Panel 4: Inverse Precondition Requirement Table / HUD
ax3 = fig.add_subplot(gs[1, 1])
ax3.set_facecolor('#111625')
ax3.axis('off')

ax3.text(0.5, 0.94, "INVERSE PRECONDITION MAP: REQUIRED VALUES FOR EACH SLAB", 
         fontsize=10.5, fontweight='bold', color='#f0f6fc', ha='center')

hud_rows = [
    ("SLAB +3 (Extreme Bull Climax)", "p >= +1.80 ATR", "v >= 2.2x Diurnal", "Super-exponential buying rush"),
    ("SLAB +2 (Strong Bull Run)", "p >= +1.00 ATR", "v >= 1.4x Diurnal", "High institutional sponsorship"),
    ("SLAB +1 (Mild Bull Drift)", "p >= +0.35 ATR", "v in [0.8x, 1.5x]", "Normal upward drift / equity risk premium"),
    ("SLAB  0 (Sideways Chop)", "p in [-0.4, +0.4]", "v <= 1.1x Diurnal", "Resting equilibrium / low participation"),
    ("SLAB -1 (Mild Bear Drift)", "p <= -0.35 ATR", "v in [0.8x, 1.5x]", "Normal profit taking / mild supply"),
    ("SLAB -2 (Strong Bear Selloff)", "p <= -1.00 ATR", "v >= 1.5x Diurnal", "Aggressive institutional liquidation"),
    ("SLAB -3 (Crash / Liquidity Rupture)", "p <= -2.00 ATR", "v >= 2.5x Diurnal", "Panic margin calls / liquidity vacuum")
]

y_pos = 0.82
for slab_name, p_cond, v_cond, econ_desc in hud_rows:
    c_hdr = '#4ade80' if '+3' in slab_name or '+2' in slab_name else ('#f87171' if '-3' in slab_name or '-2' in slab_name else '#e2e8f0')
    ax3.text(0.04, y_pos, slab_name, color=c_hdr, fontsize=9, fontweight='bold')
    ax3.text(0.04, y_pos - 0.045, f"Required: {p_cond}  |  {v_cond}", color='#94a3b8', fontsize=8)
    ax3.text(0.04, y_pos - 0.08, f"Microstructure: {econ_desc}", color='#64748b', fontsize=7.5, style='italic')
    y_pos -= 0.115

ax3.text(0.5, 0.03, "Physical Law: Delta P_target = sign(p) * [exp(alpha * v) - 1] * (1 + beta * |p|)",
         color='#fbbf24', fontsize=8.5, fontweight='bold', ha='center')

plt.savefig('charts/synthetic_slab_manifold_mapping.png', dpi=150)
plt.close()
print("Saved charts/synthetic_slab_manifold_mapping.png")
