"""Stock analyser public API (domain engine; cognition stays in PIE kernel)."""
from .constants import SIM_NAME, TOPIC, TIMEFRAMES, FINDING_STATUS
from .data.models import Instrument, EquityBar, OptionBar
from .data.store import ensure_schema, get_db_path
from .data.universe import resolve_universe, list_universes
from .features.algebra import evaluate, ALLOWED_OPS
from .strategies.model import Strategy, strategy_from_dict
from .strategies.genome import mutate
from .backtest.engine import run_backtest
from .backtest.validation import validate_strategy
from .connector import StockConnector
from .paper import propose_paper, execute_live

__all__ = ["SIM_NAME", "TOPIC", "TIMEFRAMES", "FINDING_STATUS", "Instrument",
           "EquityBar", "OptionBar", "ensure_schema", "get_db_path",
           "resolve_universe", "list_universes", "evaluate", "ALLOWED_OPS",
           "Strategy", "strategy_from_dict", "mutate", "run_backtest",
           "validate_strategy", "StockConnector", "propose_paper", "execute_live"]
