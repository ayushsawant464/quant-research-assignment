# Failed Ideas & Research Falsification Log

This document records the quantitative ideas and hypotheses tested during research that did not work or failed to meet the candidate pack's risk-adjusted mandates, complete with their actual empirical numbers and structural root-cause analysis.

---

### Idea 1: Naive Symmetric Shorting on Nifty 15-Minute Futures (Task 1)

* **Hypothesis:** Adding symmetric short positions when price breaks down below the 40-bar trailing low ($C < L_{40}$) and below the 150-bar trend EMA would generate alpha during market corrections.
* **Actual Numbers (In-Sample 2017–2022):**
  * CAGR: 22.13% | Sharpe: 1.136 | **Max Drawdown: -16.42% (FAILED Mandate: required better than -15%)** | Trades: 464 | Win Rate: 25.5%.
  * Out-of-Sample (2022–2026): CAGR dropped to 6.45%, Sharpe collapsed to 0.082, and Max Drawdown deepened to -17.80%.
* **Why It Failed:** Equity index futures possess a structural positive equity risk premium (upward drift) and suffer violent, mean-reverting short squeezes during pullbacks, resulting in severe whipsaw losses compared to sitting in cash with a +6.0% p.a. risk-free liquid carry.

---

### Idea 2: Tight Intraday Trailing Stops via ATR Bands or 50-EMA (Task 1)

* **Hypothesis:** Once a trade moved > 2 ATRs into profit, trailing a tight floor (50-EMA or 3.0x ATR from peak) would lock in gains and protect unrealized profit.
* **Actual Numbers (In-Sample 2017–2022):**
  * Baseline (150-EMA Trend Baseline): CAGR 20.20% | Sharpe 1.586 | Max DD -5.58% | Trades: 236.
  * 3.0x ATR Trailing Stop: CAGR: 18.00% | Sharpe: 1.555 | Max DD: -4.99% | Trades: 307.
  * 50-EMA Trailing Stop: CAGR: 17.80% | Sharpe: 1.410 | Max DD: -5.01% | Trades: 292.
* **Why It Failed:** Genuine Nifty macro trend expansions experience natural intra-trend consolidations of 2.5 to 3.5 ATRs before launching the next 500-point leg; tight trailing stops prematurely truncated multi-week right-tail winners.

---

### Idea 3: Pullback Re-entries off 20-EMA within Confirmed Bull Regimes (Task 1)

* **Hypothesis:** Rather than waiting for a new 40-bar channel high, allowing long re-entries when price dipped to the 20-EMA during confirmed bull hypercubes ($Y_{\text{macro}} \ge 0.60$) would increase time in market and boost CAGR.
* **Actual Numbers (In-Sample 2017–2022):**
  * Breakout-Only Baseline: CAGR 22.45% | Sharpe 1.810 | Max DD -5.08% | Trades: 258.
  * Pullback Re-entries Enabled: CAGR: 20.07% | Sharpe: 1.371 | Max DD: -6.84% | Trades: 391.
* **Why It Failed:** Intraday dip-rebounds generated high false-positive churn during sideways pauses, adding unnecessary transaction costs (turnover spiked by +51%) compared to the clean structural barrier of a multi-day high.

---

### Idea 4: Concentrated 10-Stock Portfolio Allocation (Task 2)

* **Hypothesis:** Sizing available capital into the top 10 ranked stocks (10.0% weight each) rather than 12 stocks (8.33% weight each) would compound institutional momentum faster.
* **Actual Numbers (In-Sample & Out-of-Sample):**
  * In-Sample Evaluation (2022–2024): CAGR 59.45% | Sharpe 2.481 | Max DD -12.89% | Trades: 211.
  * Out-of-Sample Hidden Horizon (2024–2026): **CAGR: 0.64% | Sharpe: 0.128 | Max Drawdown: -31.58% (Severe Drawdown)**.
* **Why It Failed:** Mid-cap stocks undergo severe idiosyncratic de-ratings during liquidity contractions; holding only 10 positions lacked sufficient portfolio granularity to survive broad mid-cap sell-offs without breaching risk tolerance.

---

### Idea 5: Unconditional Path-Lagging Alignment Bonus (Task 2)

* **Hypothesis:** Awarding a static EV bonus (+0.12) to any stock whose 20-day return lagged Nifty's 20-day return (`stock_20d < nifty_20d`) would capture coiled catch-up moves across the universe.
* **Actual Numbers (In-Sample & Full Horizon):**
  * Unconditional Path-Lag: In-Sample Sharpe 2.357 | CAGR 51.76% | Full-Horizon Max DD: -29.63%.
  * Hypercube-Gated Path-Lag ($Y_{\text{macro}} \ge 0.50$ & $\text{Nifty} > 0$): **In-Sample Sharpe 2.629 | CAGR 59.11% | Full-Horizon Max DD: -21.31%**.
* **Why It Failed:** In a declining or bear market, stocks lagging Nifty are experiencing institutional liquidation rather than coiled strength; rewarding them unconditioned on market regime bought toxic falling knives.
