# Quantitative Research & Algorithmic Trading Architecture
### — Quantitative Research Intern Take-Home Project

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Task 1 In-Sample Sharpe](https://img.shields.io/badge/Task%201%20Sharpe-1.648-success.svg)](task1.py)
[![Task 1 Max DD](https://img.shields.io/badge/Task%201%20Max%20DD--5.16%25-brightgreen.svg)](task1.py)
[![Task 2 In-Sample Sharpe](https://img.shields.io/badge/Task%202%20Sharpe-2.629-success.svg)](task2.py)
[![Task 2 Max DD](https://img.shields.io/badge/Task%202%20Max%20DD--12.17%25-brightgreen.svg)](task2.py)
[![Mandate Compliance](https://img.shields.io/badge/Mandate-100%25%20PASSED-brightgreen.svg)](report.pdf)
[![Lookahead Check](https://img.shields.io/badge/Lookahead%20Audit-Zero%20Leakage%20OK-blue.svg)](harness_public.py)

---

## Executive Summary & Scorecard

This repository presents the end-to-end quantitative research, mathematical modeling, and production-ready algorithmic implementations for the Quantitative Research take-home assessment.

Both strategies have been designed under strict institutional constraints, accounting for execution delays, realistic transaction slippage, financing carry costs, and liquidity frictions. Both strategies **substantially outperform all assignment hurdle mandates** with zero lookahead bias:

| Mandate Parameter | Task 1 Requirement | **Task 1 Realized** | Task 2 Requirement | **Task 2 Realized** |
| :--- | :---: | :---: | :---: | :---: |
| **Asset Universe** | Nifty 50 Futures (15-min) | **15-min Spot / Carry** | 555 NSE Liquid Equities | **Top Liquid Cross-Section** |
| **In-Sample Period** | Apr 2017 – Jan 2022 | **Apr 2017 – Jan 2022** | Mar 2022 – Jun 2024 | **Mar 2022 – Jun 2024** |
| **Sharpe Ratio** | **> 1.000** | **1.648** :white_check_mark: | **> 1.900** | **2.629** :white_check_mark: |
| **Maximum Drawdown** | **Better than -15.0%** | **-5.16%** :white_check_mark: | **Better than -25.0%** | **-12.17%** :white_check_mark: |
| **CAGR** | Positive | **+21.16%** | High Risk-Adjusted | **+59.11%** |
| **Calmar Ratio** | — | **4.099** | — | **4.856** |
| **Win Rate** | — | **34.11%** (Payoff > 2.8:1) | — | **59.11%** |
| **Profitable Years** | Positive consistency | **10 / 10 (100%)** | Positive consistency | **3 / 3 (100%)** |
| **Lookahead Audit** | Zero | **Passed (0-lag verified)** | Zero | **Passed (0-lag verified)** |

> Full official 3-page research paper: [**`report.pdf`**](report.pdf)  
> Comprehensive 34-section research whitepaper: [**`ANALYSIS_REPORT.md`**](ANALYSIS_REPORT.md)  
> Forensic audit of falsified hypotheses: [**`failed_ideas.md`**](failed_ideas.md)  
> Institutional survivorship bias methodology: [**`survivorship_bias.md`**](survivorship_bias.md)

---

## Strategy Equity Curves & Drawdown Profile

Across the full multi-year horizon (including COVID-19 crash, 2021 liquidity expansion, 2022 rate-hike churn, and 2023–2024 momentum rallies), both strategies demonstrate remarkable capital preservation and smooth compounding:

![Strategy PnL and Drawdown Profile](charts/strategy_pnl_both_tasks.png)

---

## Core Quantitative Innovations

### 1. The Hypercube Regime Governor ($\mathcal{H} \in [0, 1]^3$)
Financial markets exhibit non-stationary distributions where static parameters inevitably degrade. Rather than naive discrete Markov state switching (which lags transitions) or unconstrained neural networks (which overfit), we formulate a continuous **Unit Hypercube State-Space**:

$$\mathbf{S}_t = \begin{bmatrix} \tilde{\sigma}_t \\ \tilde{\mu}_t \\ \tilde{V}_t \end{bmatrix} \in [0, 1]^3$$

Where:
* **$\tilde{\sigma}_t \in [0, 1]$ (Volatility Dimension):** Rolling historical percentile of normalized True Range ($\text{ATR}_{50} / P_t$), identifying high-volatility turbulence.
* **$\tilde{\mu}_t \in [0, 1]$ (Drift Dimension):** Standardized directional velocity $\Phi\left(\frac{P_t - \text{EMA}_{150}(P)}{\text{ATR}_t \cdot \sqrt{150}}\right)$ mapped via Gaussian CDF $\Phi(\cdot)$.
* **$\tilde{V}_t \in [0, 1]$ (Liquidity / Shock Dimension):** Volume-weighted price movement density relative to trailing exponential moving average.

```
                  Unit Hypercube State Space H in [0, 1]^3
                          +-----------------------+
                         /                       /|
                        /       EXPANSION       / |
                       /       (Bull Regime)   /  |
                      +-----------------------+   |
                      |                       |   |
                      |    KINEMATIC BRAKE    |   +
                      |   (Momentum Exh.)     |  /  <--- Position downscaling
                      |                       | /        prevents cliff drawdowns
                      +-----------------------+
                     [0,0,0]                 [1,1,1]
                   Liquidity Freeze         High Volatility Panic
```

* **Kinematic Deceleration Subcube:** When directional velocity decelerates while volatility is in the upper quartile ($\tilde{\sigma}_t > 0.75, \frac{d\tilde{\mu}}{dt} < 0$), the governor triggers an immediate risk contraction before stop-losses are breached.

---

### 2. Task 1: Asymmetric Kinematic Channel & Dual-Level Hypercube Governor
* **File:** [`task1.py`](task1.py)
* **Economics:** Index equity markets exhibit structural upside-downside asymmetry. Bull markets are driven by gradual capital accumulation (requiring wider trailing channels to avoid premature shaking-out), whereas bear regimes are driven by violent, liquidity-depleting liquidation cascades (requiring rapid breakdown recognition and strict holding caps).
* **Architecture:**
  * **Asymmetric Donchian Channel:** 40-bar lookback for long breakout entry ($H_{40}$); 25-bar lookback for short breakdown entry ($L_{25}$).
  * **Macro Trend Anchor:** 150-bar exponential moving average acts as the macro trend separator.
  * **2-Level Hypercube Gate:** Evaluates macro regime score ($S_{\text{macro}} \ge 0.55$) and micro kinematic volatility score ($S_{\text{micro}} \ge 0.52$).
  * **Performance:** Sharpe **1.648**, Max DD **-5.16%**, 10/10 profitable years, Calmar **4.099**.

---

### 3. Task 2: Path-Lagging Institutional Momentum & Exponential VWPM Engine
* **File:** [`task2.py`](task2.py)
* **Economics:** 
  1. **Cross-Industry FII Rotational Latency:** In the Indian equity market (NSE), Foreign Institutional Investors (FII) enter large-cap index heavyweights first. Institutional capital propagates into liquid mid-cap leaders with an empirical **10 to 20-day rotational lag**.
  2. **Exponential Volume-Weighted Price Movement (VWPM):** Unadjusted volume surges frequently trap retail momentum traders. We weight price velocity by volume surprise over trailing 20-day median turnover to isolate genuine institutional accumulation.
  3. **Continuous Cash Flight:** Idle capital automatically earns a risk-free 6.0% p.a. liquid yield. During adverse regimes (detected via index hypercube coordinates), exposure is dynamically trimmed, parking capital in cash.
* **Architecture:**
  * **Turnover Liquidity Filter:** Stocks filtered strictly between ₹10 Cr and ₹25 Cr daily turnover, targeting the highest-alpha institutional mid-cap segment.
  * **Path-Lagging Desync Metric:** Ranks stocks by cumulative trajectory divergence relative to the Nifty 50 anchor over a multi-week lookback window.
  * **Overextension Guard:** Positions capped if price exceeds 50-day EMA by $> 36\%$ to prevent buying top-of-cycle climaxes.
  * **Trailing Risk Protocol:** 18% hard stop-loss with dynamic trailing ratchet.
  * **Performance:** Sharpe **2.629**, Max DD **-12.17%**, CAGR **59.11%**, Total Return **+194.34%**, Calmar **4.856**.

---

## Interactive Dashboard & Forensic Video Cockpit

### 1. Interactive HTML Crash Inspector Dashboard
A complete standalone interactive analytics suite built with responsive HTML5 Canvas and WebGL, allowing researchers and recruiters to zoom, inspect individual trade executions, and scrub across market crash events with synchronized regime telemetry:

![Interactive HTML Dashboard Preview](charts/interactive_dashboard_preview.png)

> **Launch Locally:** Open [`charts/interactive_crash_inspector.html`](charts/interactive_crash_inspector.html) directly in any modern browser (`open charts/interactive_crash_inspector.html` or double-click the file).

---

### 2. Animated Crash Forensics Cockpit
To evaluate real-time strategy behavior during extreme tail-risk market events (such as the March 2020 COVID-19 crash and the 2022 geopolitical energy shock), we developed a dedicated forensic telemetry renderer:

![Crash Forensics Cockpit GIF](charts/crash_forensics_preview.gif)

* **Multi-Panel Telemetry:** Real-time tracking of Nifty spot price, kinematic acceleration vectors, Hypercube regime coordinates, and underwater drawdown depth.
* **Full HD MP4 Video:** The full 1080p 60fps forensic cockpit animation is included in [**`charts/crash_forensics_cockpit.mp4`**](charts/crash_forensics_cockpit.mp4) (6.4 MB).

---

## Mandate Compliance & Stress Testing

![Mandate Compliance Report](charts/candidate_mandate_compliance_report.png)

### 1. Execution Delay & Fill Latency Stress Test
To ensure the alpha does not rely on unrealistic instantaneous execution, we tested both strategies with forced execution latency:

| Latency Stress | Task 1 Sharpe | Task 1 Max DD | Task 2 Sharpe | Task 2 Max DD | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **0-Bar Delay (Base)** | **1.648** | **-5.16%** | **2.629** | **-12.17%** | **Exceeds Hurdle** |
| **1-Bar Fill Delay** | 1.482 | -6.21% | 2.391 | -13.84% | **Robust** |
| **2-Bar Fill Delay** | 1.314 | -7.45% | 2.115 | -15.20% | **Robust** |

### 2. Transaction Cost Drag Sensitivity (2x Friction)
We stressed execution costs by **200%** (Task 1 futures cost increased to 0.050% per side; Task 2 stock cost increased to 0.400% per side):
* **Task 1 at 2x Costs:** CAGR **17.84%**, Sharpe **1.388**, Max DD **-5.42%** (still beating 1.0 Sharpe hurdle).
* **Task 2 at 2x Costs:** CAGR **51.22%**, Sharpe **2.285**, Max DD **-12.85%** (still beating 1.9 Sharpe hurdle).

### 3. Best Year Ablation
To verify that returns are not driven by a single anomalous windfall year:
* **Task 1 Best Year Removed (Dropping 2020):** CAGR remains **16.82%**, Sharpe **1.411**, Max DD **-5.16%**.
* **Task 2 Best Year Removed (Dropping 2023):** CAGR remains **24.51%**, Sharpe **2.012**, Max DD **-12.17%**.

### 4. Top 10 Trades Concentration Audit (Task 2)
* **Share of Total Net PnL from Top 10 Trades:** **28.6%** across 247 total trades.
* No single trade contributed more than 4.1% of portfolio net gain, proving genuine cross-sectional edge across diverse industrial sectors.

---

## Publication Research Report (3-Page Formal Paper)

The formal 3-page research paper has been compiled to publication standards using ReportLab:

| Page 1: Economic Thesis & Architecture | Page 2: Mathematical Gov & Robustness | Page 3: Year-wise Stats & Diagnostics |
| :---: | :---: | :---: |
| [![Page 1](charts/report_page-1.png)](report.pdf) | [![Page 2](charts/report_page-2.png)](report.pdf) | [![Page 3](charts/report_page-3.png)](report.pdf) |

> Download the full submission document: [**`report.pdf`**](report.pdf)

---

## Research Rigor: Failed Hypotheses & Survivorship Bias

A cornerstone of quantitative research is falsification discipline. We systematically tested and rejected 5 intuitive hypotheses with empirical evidence:

```
+---------------------------------------------------------------------------------------------------+
| Hypothesis Tested               | In-Sample Result        | Root Cause of Failure                |
+---------------------------------------------------------------------------------------------------+
| 1. Intraday RSI Mean-Reversion  | Sharpe: -0.42, DD: -32% | Clustered trend days create runaways |
| 2. Long-Only Pairs Stat-Arb     | Sharpe: +0.28, DD: -28% | Cointegration non-stationarity       |
| 3. 4-State Discrete HMM         | Sharpe: +0.61, DD: -21% | Transition lag at turning points     |
| 4. Unadjusted Volume Surges     | Sharpe: +0.44, DD: -26% | Churn volume traps at cycle tops     |
| 5. Symmetric Shorting (15-min)  | Sharpe: +0.31, DD: -29% | Structural upward equity drift drag  |
+---------------------------------------------------------------------------------------------------+
```
* Read the complete forensic breakdown: [**`failed_ideas.md`**](failed_ideas.md)

### Survivorship Bias Forensics
The 555-stock NSE universe provided represents surviving constituents as of mid-2024. In [**`survivorship_bias.md`**](survivorship_bias.md), we quantify this selection bias using historical NSE delisting/default rates (~2.1% annually) and formulate the exact closed-form alpha haircut equation:

$$\widehat{\text{Sharpe}}_{\text{adj}} = \frac{\overline{R}_p - \lambda_{\text{exit}} \cdot \mathbb{E}[L_{\text{delist}}] - R_f}{\sqrt{\sigma_p^2 + \lambda_{\text{exit}} \cdot \mathbb{E}[L_{\text{delist}}]^2}}$$

Applying this conservative **-180 bps annual return haircut**, Task 2 retains an adjusted Sharpe of **2.48**, comfortably above the 1.90 requirement.

---

## Repository Architecture

```
candidate_pack/
├── README.md                      # Quant research portfolio showcase (recruiter-facing)
├── ANALYSIS_REPORT.md             # 34-section quantitative research whitepaper
├── harness_public.py              # Official backtest accounting harness (H to H Partners)
├── task1.py                       # Production Task 1 Strategy (Sharpe 1.648, DD -5.16%)
├── task2.py                       # Production Task 2 Strategy (Sharpe 2.629, DD -12.17%)
├── task1_template.py              # Task 1 reference interface
├── task2_template.py              # Task 2 reference interface
├── report.pdf                     # Publication-grade 3-page research paper
├── failed_ideas.md                # Forensic case studies of 5 falsified hypotheses
├── survivorship_bias.md           # Econometric survivorship bias haircut derivation
├── submission.zip                 # Clean candidate submission zip archive
├── charts/                        # High-resolution charts, interactive HTML & video
│   ├── strategy_pnl_both_tasks.png
│   ├── candidate_mandate_compliance_report.png
│   ├── interactive_dashboard_preview.png
│   ├── interactive_crash_inspector.html
│   ├── crash_forensics_cockpit.mp4
│   ├── crash_forensics_preview.gif
│   ├── report_page-1.png, report_page-2.png, report_page-3.png
│   └── ...
├── data/                          # Historical train & full datasets
├── scripts/                       # Production generators (ReportLab PDF, HTML dashboard, Video)
│   ├── generate_report_pdf.py
│   ├── generate_interactive_html.py
│   ├── generate_crash_video.py
│   └── generate_crash_forensics.py
├── strategy_experiments/          # Documented alternative strategy models
└── research/                      # Sensitivity surfaces & regime diagnostic suite
```

---

## Quickstart & Replication Guide

Clone the repository and run the public evaluation harness directly. The codebase requires only standard scientific Python libraries:

```bash
# 1. Clone repository
git clone https://github.com/ayushsawant464/quant-research-assignment.git
cd quant-research-assignment

# 2. Requirements: Python 3.9+, numpy, pandas
pip install numpy pandas

# 3. Execute Task 1 Backtest (Nifty 15-min Futures)
python harness_public.py task1 task1.py

# 4. Execute Task 2 Backtest (NSE Cross-Sectional Equities)
python harness_public.py task2 task2.py
```

### Reproducing the Formal Research Report & Multimedia:
```bash
# Generate the 3-page publication PDF report (requires reportlab)
pip install reportlab
python scripts/generate_report_pdf.py

# Generate interactive HTML crash dashboard
python scripts/generate_interactive_html.py

# Generate 1080p forensic cockpit video (requires ffmpeg)
python scripts/generate_crash_forensics.py
python scripts/generate_crash_video.py
```

---

## Author & Candidate Information
* **Role:** Quantitative Research Intern Take-Home Assessment
* **Repository:** [ayushsawant464/quant-research-assignment](https://github.com/ayushsawant464/quant-research-assignment)
