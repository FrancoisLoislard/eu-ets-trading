# 🌍 EU-ETS Algorithmic Trading System

> **A professional-grade algorithmic trading framework for European Carbon Allowances (EUA)**  
> Built with Python · Backtesting · Live/Paper Trading · Risk Management

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)

---

## 📖 Table of Contents

- [What is EU-ETS?](#-what-is-eu-ets)
- [Why Algorithmic Trading on Carbon?](#-why-algorithmic-trading-on-carbon)
- [Project Architecture](#-project-architecture)
- [Strategies Implemented](#-strategies-implemented)
- [Quickstart](#-quickstart)
- [Configuration](#-configuration)
- [Backtesting](#-backtesting)
- [Paper Trading](#-paper-trading)
- [Risk Management](#-risk-management)
- [Roadmap](#-roadmap)

---

## 🌱 What is EU-ETS?

The **European Union Emissions Trading System (EU-ETS)** is the world's largest carbon market, operating since 2005.

### How it works

```
Industrial Emitters (Steel, Cement, Airlines, Power...)
        │
        │  Must surrender 1 EUA per tonne of CO₂ emitted
        ▼
European Union Allowances (EUA)
        │
        ├── Allocated for free (shrinking every year)
        └── Bought at auction or on secondary markets
```

### Key Market Facts

| Metric | Value (2024) |
|--------|-------------|
| **Market Cap** | ~€800 billion/year |
| **EUA Price Range** | €50–€105/tonne CO₂ |
| **Compliance Deadline** | April 30 each year |
| **Main Exchange** | ICE Endex, EEX |
| **Participants** | ~11,000 installations + speculators |
| **Ticker (Yahoo Finance)** | `CO2.L` (EUA front-month future) |

---

## ⚡ Why Algorithmic Trading on Carbon?

The EU-ETS exhibits **structural inefficiencies** that lend themselves to systematic exploitation:

### 1. 📅 Calendar Effects
```
January │ Low volumes, year reset, auction restarts
February │ Compliance prep begins (Q1 industrial reports)
March    │ Verified emissions data published → volatility spike
April    │ ⚠️  COMPLIANCE DEADLINE — peak buying pressure
May      │ Post-compliance selloff, price often drops
...
December │ Year-end positioning, low liquidity
```

### 2. 🔗 Cross-Market Correlations

EUA prices are driven by **fuel switching economics**:

```
Gas Price ↑  →  Power producers switch to Coal  →  CO₂ emissions ↑  →  EUA demand ↑
Coal Price ↑ →  Power producers switch to Gas   →  CO₂ emissions ↓  →  EUA demand ↓

Clean Spark Spread = Power Price - Gas Price - (Efficiency × EUA Price)
Clean Dark Spread  = Power Price - Coal Price - (Efficiency × EUA Price)
```

### 3. 🏛️ Policy-Driven Volatility
- MSR (Market Stability Reserve) announcements
- EU Fit-for-55 legislation updates
- CBAM (Carbon Border Adjustment Mechanism) developments
- REPowerEU policy shifts

### 4. 📊 Unique Seasonality
Unlike equities, EUA has **predictable seasonal patterns** tied to compliance cycles — this is a persistent, structural alpha source.

---

## 🗂️ Project Architecture

```
eu-ets-trading/
│
├── 📁 data/                    # Data layer
│   ├── raw/                    # Raw downloaded data (never modified)
│   ├── processed/              # Cleaned, feature-engineered datasets
│   ├── cache/                  # API response caches
│   ├── collector.py            # Yahoo Finance data collector
│   ├── features.py             # Feature engineering pipeline
│   └── universe.py             # Asset universe definition
│
├── 📁 strategies/              # Trading strategies
│   ├── base.py                 # Abstract base strategy class
│   ├── momentum.py             # Trend-following strategies
│   ├── mean_reversion.py       # Mean-reversion strategies
│   ├── seasonal.py             # Seasonality-based strategies
│   ├── spread.py               # EUA/Gas/Coal spread strategies
│   └── ensemble.py             # Strategy combination layer
│
├── 📁 backtest/                # Backtesting engine
│   ├── engine.py               # Core backtesting loop
│   ├── metrics.py              # Performance metrics (Sharpe, Sortino, etc.)
│   ├── optimizer.py            # Parameter optimization
│   └── report.py               # HTML backtest reports
│
├── 📁 risk/                    # Risk management
│   ├── position_sizer.py       # Kelly criterion, fixed-fraction, volatility-target
│   ├── portfolio_risk.py       # VaR, CVaR, drawdown limits
│   └── monitor.py              # Real-time risk monitoring
│
├── 📁 execution/               # Execution layer
│   ├── paper_trader.py         # Paper trading engine (simulated fills)
│   ├── broker_base.py          # Abstract broker interface
│   └── yahoo_feed.py           # Yahoo Finance live feed
│
├── 📁 dashboard/               # Monitoring
│   └── app.py                  # Streamlit dashboard
│
├── 📁 notebooks/               # Research & analysis
│   ├── 01_market_structure.ipynb
│   ├── 02_feature_analysis.ipynb
│   ├── 03_strategy_research.ipynb
│   └── 04_backtest_analysis.ipynb
│
├── 📁 configs/                 # Configuration files
│   ├── default.yaml            # Default parameters
│   └── strategies/             # Per-strategy configs
│
├── 📁 tests/                   # Unit & integration tests
│
├── main.py                     # Entry point (CLI)
├── requirements.txt            # Dependencies
├── pyproject.toml              # Project metadata
├── .env.example                # Environment variables template
└── .gitignore                  # Git ignore rules
```

---

## 📈 Strategies Implemented

### 1. EUA Momentum (`strategies/momentum.py`)
> *"The trend is your friend — especially before compliance deadline"*

Captures the structural uptrend toward the April compliance deadline using dual moving averages and RSI filters.

```
Signal = LONG if (EMA_fast > EMA_slow) AND (RSI > 50) AND (Volume > avg_volume)
```

### 2. Post-Compliance Mean Reversion (`strategies/mean_reversion.py`)
> *"What goes up before April, comes down in May"*

Exploits the systematic post-compliance selloff using Bollinger Bands and Z-score signals.

```
Signal = SHORT if (Z-score > 2.0) AND (month == May) AND (in compliance window)
```

### 3. Energy Spread Strategy (`strategies/spread.py`)
> *"Trade the fuel-switching economics"*

Monitors the relationship between EUA prices and energy markets (TTF Gas, Coal futures).

```
Signal = LONG EUA if (Clean Dark Spread > threshold) AND (Gas-to-Coal switch is economic)
```

### 4. Seasonal Calendar (`strategies/seasonal.py`)
> *"April compliance, May selloff, December positioning — every year"*

Pure calendar-based strategy capturing known seasonal patterns with volatility adjustment.

---

## 🚀 Quickstart

### Prerequisites
```bash
Python 3.10+
```

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/eu-ets-trading.git
cd eu-ets-trading

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Run your first backtest
```bash
python main.py backtest --strategy momentum --start 2018-01-01 --end 2024-01-01
```

### Start paper trading
```bash
python main.py paper-trade --strategy momentum --capital 100000
```

### Launch dashboard
```bash
streamlit run dashboard/app.py
```

---

## ⚙️ Configuration

All parameters live in `configs/default.yaml`:

```yaml
# Market
universe:
  eua_ticker: "CO2.L"          # EUA front-month future
  gas_ticker: "TTF=F"           # TTF Gas future
  coal_ticker: "MTF=F"          # Coal future
  power_ticker: "^STOXX"        # EU Power proxy

# Execution
execution:
  initial_capital: 100_000      # EUR
  commission: 0.001             # 0.1% per trade
  slippage: 0.0005              # 0.05% slippage assumption

# Risk
risk:
  max_position_pct: 0.20        # Max 20% of capital per trade
  max_drawdown_pct: 0.15        # Halt trading at 15% drawdown
  var_confidence: 0.95          # 95% VaR
  volatility_target: 0.15       # 15% annualized vol target
```

---

## 📊 Backtesting

The backtesting engine is designed to be **realistic and avoid common pitfalls**:

| Feature | Implementation |
|---------|---------------|
| **Look-ahead bias** | Signals generated on close, executed next open |
| **Transaction costs** | Commission + slippage model |
| **Realistic fills** | Volume-weighted, no partial fill assumption |
| **Walk-forward** | Out-of-sample validation windows |
| **Metrics** | Sharpe, Sortino, Calmar, Max Drawdown, Win Rate |

```bash
# Full backtest with HTML report
python main.py backtest \
  --strategy momentum \
  --start 2018-01-01 \
  --end 2024-01-01 \
  --optimize \
  --report backtest_report.html
```

---

## 🔄 Paper Trading

Paper trading simulates live execution without real money:

```bash
python main.py paper-trade \
  --strategy momentum \
  --capital 100000 \
  --duration 30d  # Run for 30 days
```

Fills are simulated using **next-bar execution** with configurable slippage. All trades are logged to `data/paper_trades.csv`.

---

## 🛡️ Risk Management

Every strategy goes through the risk layer before execution:

```
Strategy Signal
      │
      ▼
┌─────────────────┐
│  Position Sizer  │  ← Volatility-target sizing
│  (Kelly / Fixed) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Portfolio Risk  │  ← VaR check, drawdown limit
│  Monitor         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Order Manager   │  ← Size limits, concentration
└────────┬────────┘
         │
         ▼
    Execution
```

---

## 🗺️ Roadmap

- [x] **Step 1** — Project structure & documentation
- [ ] **Step 2** — Data pipeline (Yahoo Finance collector + feature engineering)
- [ ] **Step 3** — Strategy implementation (Momentum, Mean-Reversion, Spread)
- [ ] **Step 4** — Backtesting engine + metrics + HTML reports
- [ ] **Step 5** — Risk management layer
- [ ] **Step 6** — Paper trading engine + live feed
- [ ] **Step 7** — Streamlit dashboard
- [ ] **Step 8** — Walk-forward optimization + ensemble

---

## ⚠️ Disclaimer

> This project is for **educational and research purposes only**.  
> Trading carbon allowances involves significant financial risk.  
> Past performance does not guarantee future results.  
> Always consult a qualified financial advisor before trading.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
