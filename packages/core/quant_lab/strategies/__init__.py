"""Trading strategies for quantitative analysis."""

from quant_lab.strategies.protocols import Strategy, StrategyConfig
from quant_lab.strategies.value_moat import ValueMoatStrategy, ValueMoatConfig
from quant_lab.strategies.trend_following import TrendFollowingStrategy, TrendFollowingConfig
from quant_lab.strategies.multi_factor import MultiFactorStrategy, MultiFactorConfig

__all__ = [
    # Protocols
    "Strategy",
    "StrategyConfig",
    # Strategies
    "ValueMoatStrategy",
    "ValueMoatConfig",
    "TrendFollowingStrategy",
    "TrendFollowingConfig",
    "MultiFactorStrategy",
    "MultiFactorConfig",
]
