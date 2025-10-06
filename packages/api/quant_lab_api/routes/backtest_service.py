"""
Backtest service for orchestrating backtesting operations.

Handles:
- Loading market data
- Running backtests with progress callbacks
- Persisting results to database
"""

from typing import Callable, Optional, Awaitable
from datetime import date
from decimal import Decimal
import asyncio

from quant_lab.data import CSVDataProvider
from quant_lab.models.market_data import MarketData
from quant_lab.backtesting import BacktestEngine, BacktestConfig
from quant_lab.strategies import (
    Strategy,
    ValueMoatStrategy,
    TrendFollowingStrategy,
    MultiFactorStrategy,
)

from quant_lab_api.config import settings


# Strategy registry
AVAILABLE_STRATEGIES: dict[str, type[Strategy]] = {
    "value_moat": ValueMoatStrategy,
    "trend_following": TrendFollowingStrategy,
    "multi_factor": MultiFactorStrategy,
}


class BacktestService:
    """
    Service for running backtests with progress tracking.
    
    Provides:
    - Strategy instantiation
    - Market data loading
    - Backtest execution with callbacks
    - Results formatting
    """
    
    def __init__(self):
        self.data_provider = CSVDataProvider(
            data_dir=settings.csv_data_dir,
            fundamentals_file=settings.fundamentals_file,
        )
    
    async def run_backtest(
        self,
        strategy_name: str,
        tickers: list[str],
        start_date: date,
        end_date: date,
        initial_capital: float = 100000.0,
        commission_bps: float = 5.0,
        slippage_bps: float = 2.0,
        rebalance_frequency: int = 5,
        progress_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """
        Run a backtest with optional progress callbacks.
        
        Args:
            strategy_name: Name of strategy to use
            tickers: List of stock symbols
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            commission_bps: Commission in basis points
            slippage_bps: Slippage in basis points
            rebalance_frequency: Days between rebalances
            progress_callback: Optional async callback for progress updates
        
        Returns:
            Dictionary with backtest results
        
        Raises:
            ValueError: If strategy name is invalid or data cannot be loaded
        """
        # Validate strategy
        if strategy_name not in AVAILABLE_STRATEGIES:
            raise ValueError(
                f"Unknown strategy: {strategy_name}. "
                f"Available: {list(AVAILABLE_STRATEGIES.keys())}"
            )
        
        # Send progress: loading data
        if progress_callback:
            await progress_callback({
                "stage": "loading_data",
                "message": f"Loading market data for {len(tickers)} tickers...",
                "progress": 0.1,
            })
        
        # Load market data
        try:
            prices_df = await self.data_provider.fetch_prices(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
            )
            
            fundamentals = await self.data_provider.fetch_fundamentals(tickers)
            
            market_data = MarketData(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                prices=prices_df,
                fundamentals=fundamentals,
            )
        except Exception as e:
            raise ValueError(f"Failed to load market data: {str(e)}")
        
        # Send progress: initializing
        if progress_callback:
            await progress_callback({
                "stage": "initializing",
                "message": f"Initializing {strategy_name} strategy...",
                "progress": 0.2,
            })
        
        # Create strategy instance
        strategy = AVAILABLE_STRATEGIES[strategy_name]()
        
        # Create backtest config
        config = BacktestConfig(
            initial_capital=initial_capital,
            commission_bps=commission_bps,
            slippage_bps=slippage_bps,
            rebalance_frequency=rebalance_frequency,
        )
        
        # Send progress: running backtest
        if progress_callback:
            await progress_callback({
                "stage": "running",
                "message": "Running backtest simulation...",
                "progress": 0.3,
            })
        
        # Create and run backtest engine
        engine = BacktestEngine(
            strategy=strategy,
            market_data=market_data,
            config=config,
        )
        
        # Run backtest (this is the heavy computation)
        results = await engine.run()
        
        # Send progress: computing metrics
        if progress_callback:
            await progress_callback({
                "stage": "computing_metrics",
                "message": "Computing performance metrics...",
                "progress": 0.8,
            })
        
        # Format results
        results_dict = {
            "strategy_name": results.strategy_name,
            "start_date": results.start_date.isoformat(),
            "end_date": results.end_date.isoformat(),
            "duration_days": results.duration_days,
            "initial_capital": results.initial_capital,
            "final_value": results.final_value,
            "metrics": results.metrics,
            "equity_curve": results.daily_snapshots,
            "trade_history": [
                {
                    "timestamp": trade.timestamp.isoformat(),
                    "ticker": trade.ticker,
                    "action": trade.action,
                    "quantity": float(trade.quantity),
                    "price": float(trade.price),
                    "fees": float(trade.fees),
                    "slippage": float(trade.slippage),
                }
                for trade in results.executed_trades
            ],
            "tickers": tickers,
        }
        
        # Send progress: complete
        if progress_callback:
            await progress_callback({
                "stage": "complete",
                "message": "Backtest complete!",
                "progress": 1.0,
                "results": results_dict,
            })
        
        return results_dict
    
    @staticmethod
    def get_available_strategies() -> list[dict[str, str]]:
        """
        Get list of available strategies with metadata.
        
        Returns:
            List of strategy metadata dictionaries
        """
        strategies = []
        
        for key, strategy_class in AVAILABLE_STRATEGIES.items():
            # Instantiate to get metadata
            instance = strategy_class()
            
            strategies.append({
                "id": key,
                "name": instance.name,
                "description": instance.description,
            })
        
        return strategies
