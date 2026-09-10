SIM_NAME = "stock_analyser"
TOPIC = "sim_stock"
TIMEFRAMES = ("1D", "15m", "5m", "1m")  # V1 uses 1D + 15m
DEFAULT_TF = "1D"
FEE_BPS = 5.0
SLIPPAGE_BPS = 5.0
ATR_N = 14
SEED_SYMBOLS = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "ITC", "BHARTIARTL", "LT", "HINDUNILVR",
    "KOTAKBANK", "AXISBANK", "BAJFINANCE", "ASIANPAINT", "MARUTI",
]
UNIVERSES = ("NIFTY_200", "OPTIONS_ELIGIBLE", "ALL_EQUITIES", "MY_RESEARCH_UNIVERSE")
# Index spot is not tradable (no single instrument): never buy/sell in
# backtests or paper. Canonical set — benchmarks (sectors.py) and recorder
# reference these names; membership here is what excludes them from trading.
INDEX_SYMBOLS = ("NIFTY", "BANKNIFTY", "NIFTY_AUTO", "NIFTY_IT",
                 "NIFTY_PHARMA", "NIFTY_FMCG", "NIFTY_METAL", "NIFTY_ENERGY")


def is_tradable(symbol: str) -> bool:
    return str(symbol or "").upper() not in INDEX_SYMBOLS
FINDING_STATUS = (
    "HYPOTHESIS", "SUPPORTED", "ROBUST", "REFUTED",
    "REGIME_DEPENDENT", "INSUFFICIENT_DATA", "SUPERSEDED",
)
