"""
Backtesting engine with event-driven simulation.

The engine runs a strategy against historical data, day by day,
applying trades and tracking portfolio performance.

Key principles:
- Point-in-time data (no look-ahead bias)
- Realistic trade execution (with fees and slippage)
- Immutable state (functional approach)
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
import pandas as pd

from quant_lab.models.market_data import MarketData
from quant_lab.models.signal import Signal
from quant_lab.portfolio.portfolio import Portfolio
from quant_lab.portfolio.trade import Trade, TradeAction, TradeBuilder
from quant_lab.strategies.protocols import Strategy


class BacktestConfig:
    """Configuration for backtesting."""
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_bps: float = 5.0,     # 5 basis points
        slippage_bps: float = 2.0,       # 2 basis points
        rebalance_frequency: int = 1,    # Daily rebalancing
    ):
        self.initial_capital = initial_capital
        self.commission_bps = commission_bps
        self.slippage_bps = slippage_bps
        self.rebalance_frequency = rebalance_frequency


class BacktestEngine:
    """
    Event-driven backtesting engine.
    
    Simulates strategy performance on historical data with:
    - Daily event loop
    - Point-in-time market data
    - Realistic trade execution
    - Portfolio state tracking
    
    Usage:
        engine = BacktestEngine(strategy, market_data, config)
        results = await engine.run()
    """
    
    def __init__(
        self,
        strategy: Strategy,
        market_data: MarketData,
        config: Optional[BacktestConfig] = None,
    ):
        self.strategy = strategy
        self.market_data = market_data
        self.config = config or BacktestConfig()
        
        # Initialize portfolio
        self.portfolio = Portfolio.create(
            initial_capital=Decimal(str(self.config.initial_capital))
        )
        
        # Track history
        self.daily_snapshots: list[dict] = []
        self.executed_trades: list[Trade] = []
    
    async def run(self) -> "BacktestResults":
        """
        Run the backtest.
        
        Returns:
            BacktestResults object with performance metrics and trade history
        """
        # Get trading days from market data
        trading_days = self._get_trading_days()
        
        if not trading_days:
            raise ValueError("No trading days available in market data")
        
        # Event loop: iterate through each trading day
        for i, current_date in enumerate(trading_days):
            # Get point-in-time market data
            point_in_time_data = self.market_data.as_of(current_date)
            
            # Update portfolio prices with current market prices
            current_prices = self._get_current_prices(point_in_time_data, current_date)
            self.portfolio = self.portfolio.update_prices(current_prices)
            
            # Generate signals from strategy (only on rebalance days)
            if i % self.config.rebalance_frequency == 0:
                signals = self.strategy.generate_signals(
                    market_data=point_in_time_data,
                    portfolio=self.portfolio,
                    current_date=current_date,
                )
                
                # Execute trades
                for signal in signals:
                    if signal.is_actionable():
                        trade = self._signal_to_trade(signal, current_prices)
                        
                        if trade:
                            # Check if trade is executable
                            can_execute, reason = self.portfolio.can_execute_trade(trade)
                            
                            if can_execute:
                                self.portfolio = self.portfolio.apply_trade(trade)
                                self.executed_trades.append(trade)
            
            # Save daily snapshot
            self.daily_snapshots.append({
                "date": current_date,
                "total_value": float(self.portfolio.total_value),
                "cash": float(self.portfolio.cash),
                "positions_value": float(self.portfolio.long_exposure + self.portfolio.short_exposure),
                "num_positions": len(self.portfolio.positions),
                "realized_pnl": float(self.portfolio.realized_pnl),
                "unrealized_pnl": float(self.portfolio.unrealized_pnl),
            })
        
        # Build results
        from quant_lab.backtesting.results import BacktestResults
        
        return BacktestResults(
            strategy_name=self.strategy.name,
            start_date=trading_days[0],
            end_date=trading_days[-1],
            initial_capital=self.config.initial_capital,
            final_value=float(self.portfolio.total_value),
            daily_snapshots=self.daily_snapshots,
            executed_trades=self.executed_trades,
            portfolio=self.portfolio,
        )
    
    def _get_trading_days(self) -> list[date]:
        """Extract sorted list of trading days from market data."""
        all_dates = set()
        
        for ticker in self.market_data.tickers:
            ticker_prices = self.market_data.get_prices(ticker)
            all_dates.update(ticker_prices["date"].tolist())
        
        return sorted(list(all_dates))
    
    def _get_current_prices(
        self,
        market_data: MarketData,
        current_date: date,
    ) -> dict[str, Decimal]:
        """Get current prices for all tickers."""
        prices = {}
        
        for ticker in market_data.tickers:
            ticker_prices = market_data.get_prices(ticker)
            ticker_prices = ticker_prices[ticker_prices["date"] == current_date]
            
            if not ticker_prices.empty:
                prices[ticker] = ticker_prices.iloc[0]["close"]
        
        return prices
    
    def _signal_to_trade(
        self,
        signal: Signal,
        current_prices: dict[str, Decimal],
    ) -> Optional[Trade]:
        """Convert a signal to an executable trade."""
        if signal.ticker not in current_prices:
            return None
        
        price = current_prices[signal.ticker]
        
        # Map signal action to trade action
        action_map = {
            "buy": TradeAction.BUY,
            "sell": TradeAction.SELL,
            "short": TradeAction.SHORT,
            "cover": TradeAction.COVER,
        }
        
        trade_action = action_map.get(signal.action)
        if not trade_action:
            return None
        
        # Build trade with fees and slippage
        trade = (
            TradeBuilder(signal.ticker, trade_action, signal.quantity, price)
            .with_commission_bps(self.config.commission_bps)
            .with_slippage_bps(self.config.slippage_bps)
            .with_metadata("signal_confidence", float(signal.confidence))
            .with_metadata("signal_reasoning", signal.reasoning or "")
            .build()
        )
        
        return trade
