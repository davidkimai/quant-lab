"""
Strategy protocols for trading signal generation.

All strategies implement a common interface for signal generation,
enabling hot-swapping of different approaches in the backtesting engine.
"""

from datetime import date
from typing import Protocol, runtime_checkable

from quant_lab.models.market_data import MarketData
from quant_lab.models.signal import Signal
from quant_lab.portfolio.portfolio import Portfolio


@runtime_checkable
class Strategy(Protocol):
    """
    Protocol for trading strategies.
    
    All strategies must implement generate_signals() to be compatible
    with the backtesting engine.
    """
    
    name: str
    description: str
    
    def generate_signals(
        self,
        market_data: MarketData,
        portfolio: Portfolio,
        current_date: date,
    ) -> list[Signal]:
        """
        Generate trading signals based on market data and portfolio state.
        
        Args:
            market_data: Historical market data up to current_date
            portfolio: Current portfolio state
            current_date: The date for which to generate signals
        
        Returns:
            List of Signal objects (buy/sell/hold/short/cover)
            
        Note:
            Strategies should only use data available up to current_date
            to avoid look-ahead bias in backtesting.
        """
        ...


class StrategyConfig:
    """
    Base configuration for strategies.
    
    Subclass this to add strategy-specific parameters.
    """
    
    def __init__(
        self,
        max_position_size: float = 0.20,  # Max 20% per position
        min_confidence: float = 0.5,       # Minimum signal confidence
        commission_bps: float = 5.0,       # 5 basis points
        slippage_bps: float = 2.0,         # 2 basis points
    ):
        self.max_position_size = max_position_size
        self.min_confidence = min_confidence
        self.commission_bps = commission_bps
        self.slippage_bps = slippage_bps
