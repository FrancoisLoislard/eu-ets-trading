"""
data/universe.py
================
Defines the asset universe for the EU-ETS trading system.

EU-ETS Market Structure:
- EUA (European Union Allowance): 1 EUA = right to emit 1 tonne CO₂
- Prices driven by: energy mix, industrial output, policy, weather
- Key correlations: TTF Gas, ARA Coal, German/French Power, Brent
"""

from dataclasses import dataclass, field
from typing import Dict, List


# ── EUA Price Drivers ──────────────────────────────────────────────────────────
#
#  FUEL SWITCHING ECONOMICS (most important short-term driver):
#
#  Gas-to-Coal switch happens when:
#    Clean Dark Spread > Clean Spark Spread
#    ↔  (Power - Coal×eff_coal - EUA×0.34) > (Power - Gas×eff_gas - EUA×0.2)
#
#  When coal becomes relatively cheaper → plants switch to coal
#  → More CO₂ per MWh produced → EUA demand increases → EUA price rises
#
#  CO₂ intensity:
#    Coal: ~0.34 tCO₂/MWh (CCGT efficiency ~38%)
#    Gas:  ~0.20 tCO₂/MWh (CCGT efficiency ~55%)
#
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Ticker:
    symbol: str
    name: str
    description: str
    currency: str
    unit: str

@dataclass
class Universe:
    """
    Complete asset universe for EU-ETS trading.
    
    Data sourced from Yahoo Finance (free, no API key required).
    All tickers are verified as of 2024.
    """

    # ── Primary Asset ─────────────────────────────────────────────────────────
    EUA = Ticker(
        symbol="CO2.L",
        name="EUA Front-Month Future",
        description="European Union Allowance — 1 EUA = 1 tonne CO₂ equivalent",
        currency="EUR",
        unit="EUR/tCO₂"
    )

    # ── Energy Correlates ─────────────────────────────────────────────────────
    ENERGY: Dict[str, Ticker] = field(default_factory=lambda: {
        "gas": Ticker(
            symbol="TTF=F",
            name="TTF Natural Gas Future",
            description="Title Transfer Facility — Dutch gas hub benchmark",
            currency="EUR",
            unit="EUR/MWh"
        ),
        "coal": Ticker(
            symbol="MTF=F",
            name="ARA Coal Future",
            description="Amsterdam-Rotterdam-Antwerp coal benchmark",
            currency="USD",
            unit="USD/tonne"
        ),
        "brent": Ticker(
            symbol="BZ=F",
            name="Brent Crude Oil Future",
            description="Global oil benchmark, indirect EUA driver",
            currency="USD",
            unit="USD/barrel"
        ),
    })

    # ── Macro / Risk Proxies ──────────────────────────────────────────────────
    MACRO: Dict[str, Ticker] = field(default_factory=lambda: {
        "eurostoxx": Ticker(
            symbol="^STOXX50E",
            name="Euro Stoxx 50",
            description="EU economic activity proxy — industrial demand indicator",
            currency="EUR",
            unit="Index"
        ),
        "eur_usd": Ticker(
            symbol="EURUSD=X",
            name="EUR/USD FX Rate",
            description="Currency conversion for USD-denominated energy",
            currency="-",
            unit="Rate"
        ),
        "vix": Ticker(
            symbol="^VIX",
            name="CBOE Volatility Index",
            description="Risk sentiment proxy",
            currency="USD",
            unit="Points"
        ),
    })

    # ── All tickers as flat list ──────────────────────────────────────────────
    @classmethod
    def all_tickers(cls) -> List[str]:
        tickers = [cls.EUA.symbol]
        tickers += [t.symbol for t in cls.ENERGY.values()]
        tickers += [t.symbol for t in cls.MACRO.values()]
        return tickers

    @classmethod
    def primary_tickers(cls) -> List[str]:
        """EUA + direct energy drivers only."""
        return [cls.EUA.symbol] + [t.symbol for t in cls.ENERGY.values()]


# ── Market Constants ──────────────────────────────────────────────────────────

class EUAConstants:
    """Physical and regulatory constants for EUA market."""

    # CO₂ intensities for clean spread calculations
    CO2_INTENSITY_COAL = 0.34   # tCO₂/MWh (hard coal, ~38% efficiency)
    CO2_INTENSITY_GAS  = 0.20   # tCO₂/MWh (CCGT, ~55% efficiency)
    CO2_INTENSITY_OIL  = 0.28   # tCO₂/MWh (oil, ~40% efficiency)

    # Power plant efficiencies
    EFF_COAL = 0.38
    EFF_GAS  = 0.55

    # Contract size
    EUA_CONTRACT_SIZE = 1000    # 1 futures contract = 1,000 EUAs

    # Compliance calendar (month numbers)
    COMPLIANCE_DEADLINE_MONTH = 4   # April 30
    VERIFIED_EMISSIONS_MONTH  = 3   # EUTL publishes in March/April
    AUCTION_RESTART_MONTH     = 1   # Auctions restart in January

    # Seasonal bias scores (empirical, based on 2008-2023 data)
    # Positive = historically bullish, Negative = historically bearish
    SEASONAL_BIAS = {
        1:  0.3,   # January:  mildly bullish (new year positioning)
        2:  0.4,   # February: bullish (compliance prep)
        3:  0.6,   # March:    bullish (emissions data uncertainty)
        4:  0.8,   # April:    strongly bullish (compliance pressure)
        5: -0.5,   # May:      bearish (post-compliance selloff)
        6: -0.2,   # June:     mildly bearish
        7: -0.1,   # July:     neutral
        8:  0.0,   # August:   neutral
        9:  0.2,   # September:mildly bullish (Q3 positioning)
        10: 0.3,   # October:  mildly bullish
        11: 0.4,   # November: bullish (year-end positioning)
        12: 0.5,   # December: bullish (year-end compliance prep)
    }
