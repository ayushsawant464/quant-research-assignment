import json

with open('charts/crash_forensics_data.json') as f:
    data_json = f.read()

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Quant Cockpit: Crash Forensics & Neural Telemetry</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
  body {{ background: #0b0f19; color: #c9d1d9; display: flex; height: 100vh; overflow: hidden; }}
  #main {{ flex: 1; display: flex; flex-direction: column; padding: 12px 18px; }}
  #sidebar {{ width: 440px; background: #0d121f; border-left: 1px solid #21262d; padding: 16px; display: flex; flex-direction: column; overflow-y: auto; }}
  
  header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
  h1 {{ font-size: 17px; font-weight: 700; color: #f0f6fc; letter-spacing: 0.5px; }}
  .badge {{ background: #21262d; border: 1px solid #30363d; padding: 4px 8px; border-radius: 4px; font-size: 11px; color: #58a6ff; }}

  /* Controls */
  #controls {{ display: flex; align-items: center; gap: 12px; background: #161b26; border: 1px solid #30363d; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px; }}
  button {{ background: #238636; color: white; border: none; padding: 6px 14px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 12px; transition: 0.15s; }}
  button:hover {{ background: #2ea043; }}
  button.secondary {{ background: #21262d; border: 1px solid #30363d; color: #c9d1d9; }}
  button.secondary:hover {{ background: #30363d; }}
  #slider {{ flex: 1; accent-color: #58a6ff; cursor: pointer; }}
  #frameLabel {{ font-size: 12px; font-weight: 600; color: #58a6ff; min-width: 140px; text-align: right; }}

  /* Charts Canvas Container */
  #chartsContainer {{ flex: 1; display: flex; flex-direction: column; gap: 8px; position: relative; }}
  .chart-box {{ flex: 1; background: #111625; border: 1px solid #1f2638; border-radius: 6px; position: relative; overflow: hidden; }}
  .chart-title {{ position: absolute; top: 6px; left: 10px; font-size: 10px; font-weight: 700; color: #8b949e; letter-spacing: 0.5px; z-index: 5; pointer-events: none; }}
  canvas {{ width: 100%; height: 100%; display: block; }}

  /* Sidebar HUD */
  .hud-card {{ background: #161b26; border: 1px solid #30363d; border-radius: 6px; padding: 12px; margin-bottom: 14px; }}
  .hud-title {{ font-size: 11px; font-weight: 700; color: #8b949e; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px; display: flex; justify-content: space-between; }}
  .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
  .stat-item {{ background: #0d121f; padding: 8px; border-radius: 4px; border: 1px solid #21262d; }}
  .stat-lbl {{ font-size: 10px; color: #8b949e; margin-bottom: 2px; }}
  .stat-val {{ font-size: 13px; font-weight: 700; color: #f0f6fc; }}
  
  /* State Pill */
  .state-pill {{ padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: 700; display: inline-block; }}
  .state-long {{ background: rgba(35, 134, 54, 0.2); color: #3fb950; border: 1px solid #238636; }}
  .state-short {{ background: rgba(218, 54, 51, 0.2); color: #f85149; border: 1px solid #da3633; }}
  .state-flat {{ background: rgba(139, 148, 158, 0.2); color: #8b949e; border: 1px solid #30363d; }}

  /* Neuron Meters */
  .neuron-row {{ margin-bottom: 9px; }}
  .neuron-hdr {{ display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 3px; }}
  .neuron-lbl {{ color: #c9d1d9; font-weight: 500; }}
  .neuron-val {{ font-weight: 700; }}
  .meter-track {{ width: 100%; height: 8px; background: #21262d; border-radius: 4px; overflow: hidden; position: relative; }}
  .meter-fill {{ height: 100%; width: 0%; border-radius: 4px; transition: width 0.05s, background-color 0.15s; }}

  .crash-card {{ border: 1px solid #f85149; background: rgba(218, 54, 51, 0.08); }}
</style>
</head>
<body>

<div id="main">
  <header>
    <h1>QUANT COCKPIT: EVENT FORENSICS & INDICATOR TELEMETRY</h1>
    <div class="badge">NIFTY 50 15-MIN BARS (COVID CRASH WINDOW)</div>
  </header>

  <div id="controls">
    <button id="btnPlay">▶ Play</button>
    <button class="secondary" id="btnPrev">◀ -1 Bar</button>
    <button class="secondary" id="btnNext">+1 Bar ▶</button>
    <button class="secondary" id="btnSpeed">1x</button>
    <input type="range" id="slider" min="0" max="699" value="0">
    <div id="frameLabel">Bar #0 (2020-02-17 09:15)</div>
  </div>

  <div id="chartsContainer">
    <div class="chart-box" style="flex: 2.2;">
      <div class="chart-title">PRICE & EXECUTION REGIMES (CLOSE, H50, L25, EMA 150)</div>
      <canvas id="cvsPrice"></canvas>
    </div>
    <div class="chart-box" style="flex: 1.4;">
      <div class="chart-title">KINEMATICS: VELOCITY v (CYAN) & ACCELERATION a (ROSE DASHED)</div>
      <canvas id="cvsKin"></canvas>
    </div>
    <div class="chart-box" style="flex: 1.4;">
      <div class="chart-title">MODEL SIGNALS: BASE PLS (INDIGO) & FINAL PREDICTION ŷ (GOLD)</div>
      <canvas id="cvsModel"></canvas>
    </div>
    <div class="chart-box" style="flex: 1.4;">
      <div class="chart-title">STRATEGY CUMULATIVE RETURN (GREEN) VS BUY & HOLD (RED)</div>
      <canvas id="cvsPnl"></canvas>
    </div>
  </div>
</div>

<div id="sidebar">
  <div class="hud-card">
    <div class="hud-title"><span>CURRENT TELEMETRY</span> <span id="hudTime">2020-02-17 09:15</span></div>
    <div class="stat-grid">
      <div class="stat-item"><div class="stat-lbl">Price Close</div><div class="stat-val" id="valPrice">12,110.0</div></div>
      <div class="stat-item"><div class="stat-lbl">ATR (Volatility)</div><div class="stat-val" id="valAtr">34.2</div></div>
      <div class="stat-item"><div class="stat-lbl">H50 / L25 Channel</div><div class="stat-val" id="valChannel" style="font-size: 11px;">12,160 / 12,050</div></div>
      <div class="stat-item"><div class="stat-lbl">EMA 150 Macro</div><div class="stat-val" id="valEtrend">12,080.0</div></div>
    </div>
  </div>

  <div class="hud-card">
    <div class="hud-title"><span>STRATEGY STATE & STALL</span> <span id="valState" class="state-pill state-flat">FLAT (0.0)</span></div>
    <div class="stat-grid">
      <div class="stat-item"><div class="stat-lbl">Stall Counter</div><div class="stat-val" id="valStall">0 / 6 Bars</div></div>
      <div class="stat-item"><div class="stat-lbl">Strategy PnL</div><div class="stat-val" id="valPnl" style="color: #3fb950;">+0.00%</div></div>
      <div class="stat-item"><div class="stat-lbl">Base PLS (X·β)</div><div class="stat-val" id="valBase">0.000</div></div>
      <div class="stat-item"><div class="stat-lbl">Final Pred ŷ</div><div class="stat-val" id="valFinal">0.000</div></div>
    </div>
  </div>

  <div class="hud-card crash-card">
    <div class="hud-title" style="color: #f85149;"><span>🚨 COMPOSITE CRASH NEURON</span> <span id="valCrashTxt">0.00 (RESTING)</span></div>
    <div class="meter-track" style="height: 12px; margin-top: 4px;">
      <div class="meter-fill" id="meterCrash" style="width: 0%; background: #3fb950;"></div>
    </div>
  </div>

  <div class="hud-card" style="flex: 1;">
    <div class="hud-title"><span>NEURON EXCITATION GAUGES [0.0 - 1.0]</span></div>
    
    <div class="neuron-row">
      <div class="neuron-hdr"><span class="neuron-lbl">1. Velocity Surge</span><span class="neuron-val" id="valN1">0.00</span></div>
      <div class="meter-track"><div class="meter-fill" id="mN1"></div></div>
    </div>
    <div class="neuron-row">
      <div class="neuron-hdr"><span class="neuron-lbl">2. Downside Acceleration</span><span class="neuron-val" id="valN2">0.00</span></div>
      <div class="meter-track"><div class="meter-fill" id="mN2"></div></div>
    </div>
    <div class="neuron-row">
      <div class="neuron-hdr"><span class="neuron-lbl">3. Jerk / Liquidity Shock</span><span class="neuron-val" id="valN3">0.00</span></div>
      <div class="meter-track"><div class="meter-fill" id="mN3"></div></div>
    </div>
    <div class="neuron-row">
      <div class="neuron-hdr"><span class="neuron-lbl">4. Range Expansion (High-Low)</span><span class="neuron-val" id="valN4">0.00</span></div>
      <div class="meter-track"><div class="meter-fill" id="mN4"></div></div>
    </div>
    <div class="neuron-row">
      <div class="neuron-hdr"><span class="neuron-lbl">5. Macro Divergence (EMA150)</span><span class="neuron-val" id="valN5">0.00</span></div>
      <div class="meter-track"><div class="meter-fill" id="mN5"></div></div>
    </div>
    <div class="neuron-row">
      <div class="neuron-hdr"><span class="neuron-lbl">6. Mod 2 Exhaustion (ReLU)</span><span class="neuron-val" id="valN6">0.00</span></div>
      <div class="meter-track"><div class="meter-fill" id="mN6"></div></div>
    </div>
    <div class="neuron-row">
      <div class="neuron-hdr"><span class="neuron-lbl">7. Stall Threat (Desync Risk)</span><span class="neuron-val" id="valN7">0.00</span></div>
      <div class="meter-track"><div class="meter-fill" id="mN7"></div></div>
    </div>
  </div>
</div>

<script>
const DATA = {data_json};
const N = DATA.length;

let currentIdx = 0;
let isPlaying = false;
let playInterval = null;
let speed = 1;
const speeds = [0.5, 1, 2, 4];
let speedIdx = 1;

// Canvas Setup
const cvsPrice = document.getElementById('cvsPrice');
const cvsKin = document.getElementById('cvsKin');
const cvsModel = document.getElementById('cvsModel');
const cvsPnl = document.getElementById('cvsPnl');

function resizeCanvas(cvs) {{
  const rect = cvs.getBoundingClientRect();
  cvs.width = rect.width * window.devicePixelRatio;
  cvs.height = rect.height * window.devicePixelRatio;
}}

function initCanvases() {{
  [cvsPrice, cvsKin, cvsModel, cvsPnl].forEach(resizeCanvas);
  drawAll();
}}

window.addEventListener('resize', initCanvases);

function getX(i, width) {{
  return (i / (N - 1)) * (width - 20) + 10;
}}

function drawLine(ctx, dataKey, minY, maxY, width, height, color, lw = 1.5, isDashed = false) {{
  ctx.strokeStyle = color;
  ctx.lineWidth = lw * window.devicePixelRatio;
  if (isDashed) ctx.setLineDash([4 * window.devicePixelRatio, 4 * window.devicePixelRatio]);
  else ctx.setLineDash([]);
  
  ctx.beginPath();
  for (let i = 0; i < N; i++) {{
    const x = getX(i, width);
    const val = DATA[i][dataKey];
    const y = height - ((val - minY) / (maxY - minY)) * (height - 20) - 10;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }}
  ctx.stroke();
  ctx.setLineDash([]);
}}

function drawCursor(ctx, idx, width, height) {{
  const x = getX(idx, width);
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 1.2 * window.devicePixelRatio;
  ctx.setLineDash([]);
  ctx.beginPath();
  ctx.moveTo(x, 0);
  ctx.lineTo(x, height);
  ctx.stroke();
}}

function drawAll() {{
  drawPriceChart();
  drawKinChart();
  drawModelChart();
  drawPnlChart();
  updateHUD();
}}

function drawPriceChart() {{
  const ctx = cvsPrice.getContext('2d');
  const w = cvsPrice.width;
  const h = cvsPrice.height;
  ctx.clearRect(0, 0, w, h);
  
  // Shade Positions
  for (let i = 0; i < N - 1; i++) {{
    const pos = DATA[i].pos;
    if (pos !== 0) {{
      const x1 = getX(i, w);
      const x2 = getX(i + 1, w);
      ctx.fillStyle = pos === 1 ? 'rgba(35, 134, 54, 0.25)' : 'rgba(218, 54, 51, 0.25)';
      ctx.fillRect(x1, 0, x2 - x1, h);
    }}
  }}
  
  const minP = 7300, maxP = 12400;
  drawLine(ctx, 'h50', minP, maxP, w, h, '#3fb950', 1, true);
  drawLine(ctx, 'l25', minP, maxP, w, h, '#f85149', 1, true);
  drawLine(ctx, 'etrend', minP, maxP, w, h, '#d29922', 1.2);
  drawLine(ctx, 'close', minP, maxP, w, h, '#58a6ff', 2);
  
  // Current Dot
  const curX = getX(currentIdx, w);
  const curY = h - ((DATA[currentIdx].close - minP) / (maxP - minP)) * (h - 20) - 10;
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.arc(curX, curY, 4 * window.devicePixelRatio, 0, Math.PI * 2);
  ctx.fill();
  
  drawCursor(ctx, currentIdx, w, h);
}}

function drawKinChart() {{
  const ctx = cvsKin.getContext('2d');
  const w = cvsKin.width;
  const h = cvsKin.height;
  ctx.clearRect(0, 0, w, h);
  
  const minK = -7, maxK = 6;
  // Zero line
  const zeroY = h - ((0 - minK) / (maxK - minK)) * (h - 20) - 10;
  ctx.strokeStyle = '#30363d';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, zeroY); ctx.lineTo(w, zeroY); ctx.stroke();
  
  drawLine(ctx, 'vel', minK, maxK, w, h, '#38bdf8', 1.4);
  drawLine(ctx, 'acc', minK, maxK, w, h, '#f43f5e', 1.2, true);
  
  drawCursor(ctx, currentIdx, w, h);
}}

function drawModelChart() {{
  const ctx = cvsModel.getContext('2d');
  const w = cvsModel.width;
  const h = cvsModel.height;
  ctx.clearRect(0, 0, w, h);
  
  const minM = -0.5, maxM = 0.5;
  const zeroY = h - ((0 - minM) / (maxM - minM)) * (h - 20) - 10;
  ctx.strokeStyle = '#30363d';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, zeroY); ctx.lineTo(w, zeroY); ctx.stroke();
  
  drawLine(ctx, 'base', minM, maxM, w, h, '#818cf8', 1.2);
  drawLine(ctx, 'final', minM, maxM, w, h, '#fbbf24', 1.8);
  
  drawCursor(ctx, currentIdx, w, h);
}}

function drawPnlChart() {{
  const ctx = cvsPnl.getContext('2d');
  const w = cvsPnl.width;
  const h = cvsPnl.height;
  ctx.clearRect(0, 0, w, h);
  
  const minRet = -35, maxRet = 25;
  const zeroY = h - ((0 - minRet) / (maxRet - minRet)) * (h - 20) - 10;
  ctx.strokeStyle = '#30363d';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, zeroY); ctx.lineTo(w, zeroY); ctx.stroke();
  
  drawLine(ctx, 'bnh_cum', minRet, maxRet, w, h, '#f85149', 1.5, true);
  drawLine(ctx, 'strat_cum', minRet, maxRet, w, h, '#3fb950', 2);
  
  drawCursor(ctx, currentIdx, w, h);
}}

function updateNeuronMeter(idVal, idMeter, val) {{
  const pct = Math.max(0, Math.min(100, val * 100));
  const elVal = document.getElementById(idVal);
  const elMeter = document.getElementById(idMeter);
  
  let col = '#3fb950';
  let status = '';
  if (val >= 0.70) {{
    col = '#f85149';
    status = ' [FIRE!]';
  }} else if (val >= 0.40) {{
    col = '#d29922';
    status = ' [ALERT]';
  }}
  
  elVal.textContent = val.toFixed(2) + status;
  elVal.style.color = col;
  elMeter.style.width = pct + '%';
  elMeter.style.backgroundColor = col;
}}

function updateHUD() {{
  const row = DATA[currentIdx];
  document.getElementById('frameLabel').textContent = `Bar #${{currentIdx}} (${{row.time}})`;
  document.getElementById('hudTime').textContent = row.time;
  document.getElementById('valPrice').textContent = row.close.toLocaleString('en-US', {{ minimumFractionDigits: 1 }});
  document.getElementById('valAtr').textContent = row.atr.toFixed(1);
  document.getElementById('valChannel').textContent = `${{row.h50.toFixed(0)}} / ${{row.l25.toFixed(0)}}`;
  document.getElementById('valEtrend').textContent = row.etrend.toFixed(1);
  
  const elState = document.getElementById('valState');
  if (row.pos === 1) {{
    elState.textContent = 'LONG (+1.0)';
    elState.className = 'state-pill state-long';
  }} else if (row.pos === -1) {{
    elState.textContent = 'SHORT (-1.0)';
    elState.className = 'state-pill state-short';
  }} else {{
    elState.textContent = 'FLAT (0.0)';
    elState.className = 'state-pill state-flat';
  }}
  
  document.getElementById('valStall').textContent = row.pos !== 0 ? `${{row.stall}} / 6 Bars` : '0 / 6 (Flat)';
  const pnlCol = row.strat_cum >= 0 ? '#3fb950' : '#f85149';
  document.getElementById('valPnl').textContent = `${{row.strat_cum >= 0 ? '+' : ''}}${{row.strat_cum.toFixed(2)}}%`;
  document.getElementById('valPnl').style.color = pnlCol;
  
  document.getElementById('valBase').textContent = row.base.toFixed(3);
  document.getElementById('valFinal').textContent = row.final.toFixed(3);
  
  // Composite Crash Meter
  updateNeuronMeter('valCrashTxt', 'meterCrash', row.e_crash);
  
  // 7 Sub-neurons
  updateNeuronMeter('valN1', 'mN1', row.e_vel);
  updateNeuronMeter('valN2', 'mN2', row.e_acc);
  updateNeuronMeter('valN3', 'mN3', row.e_jerk);
  updateNeuronMeter('valN4', 'mN4', row.e_vol);
  updateNeuronMeter('valN5', 'mN5', row.e_macro);
  updateNeuronMeter('valN6', 'mN6', row.e_mod2);
  updateNeuronMeter('valN7', 'mN7', row.e_stall);
}}

// Controls
const slider = document.getElementById('slider');
slider.addEventListener('input', (e) => {{
  currentIdx = parseInt(e.target.value);
  drawAll();
}});

document.getElementById('btnPrev').addEventListener('click', () => {{
  if (currentIdx > 0) {{
    currentIdx--;
    slider.value = currentIdx;
    drawAll();
  }}
}});

document.getElementById('btnNext').addEventListener('click', () => {{
  if (currentIdx < N - 1) {{
    currentIdx++;
    slider.value = currentIdx;
    drawAll();
  }}
}});

const btnPlay = document.getElementById('btnPlay');
btnPlay.addEventListener('click', () => {{
  isPlaying = !isPlaying;
  if (isPlaying) {{
    btnPlay.textContent = '❚❚ Pause';
    btnPlay.style.background = '#da3633';
    playInterval = setInterval(() => {{
      if (currentIdx < N - 1) {{
        currentIdx++;
        slider.value = currentIdx;
        drawAll();
      }} else {{
        isPlaying = false;
        btnPlay.textContent = '▶ Play';
        btnPlay.style.background = '#238636';
        clearInterval(playInterval);
      }}
    }}, 66 / speed);
  }} else {{
    btnPlay.textContent = '▶ Play';
    btnPlay.style.background = '#238636';
    clearInterval(playInterval);
  }}
}});

const btnSpeed = document.getElementById('btnSpeed');
btnSpeed.addEventListener('click', () => {{
  speedIdx = (speedIdx + 1) % speeds.length;
  speed = speeds[speedIdx];
  btnSpeed.textContent = speed + 'x';
  if (isPlaying) {{
    clearInterval(playInterval);
    playInterval = setInterval(() => {{
      if (currentIdx < N - 1) {{
        currentIdx++;
        slider.value = currentIdx;
        drawAll();
      }} else {{
        isPlaying = false;
        btnPlay.textContent = '▶ Play';
        btnPlay.style.background = '#238636';
        clearInterval(playInterval);
      }}
    }}, 66 / speed);
  }}
}});

// Keyboard Shortcuts: Space to Play/Pause, Left/Right Arrows to step
window.addEventListener('keydown', (e) => {{
  if (e.key === ' ' || e.code === 'Space') {{
    e.preventDefault();
    btnPlay.click();
  }} else if (e.key === 'ArrowLeft') {{
    e.preventDefault();
    document.getElementById('btnPrev').click();
  }} else if (e.key === 'ArrowRight') {{
    e.preventDefault();
    document.getElementById('btnNext').click();
  }}
}});

// First Render
setTimeout(initCanvases, 50);
</script>
</body>
</html>
"""

with open('charts/interactive_crash_inspector.html', 'w') as f:
    f.write(html_content)

print("Saved charts/interactive_crash_inspector.html")
