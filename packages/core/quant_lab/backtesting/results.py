"""
Backtest results container and aggregation.

Provides a clean interface for accessing backtest results,
including performance metrics, trade history, and equity curve.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
import pandas as pd

from quant_lab.portfolio.portfolio import Portfolio
from quant_lab.portfolio.trade import Trade
from quant_lab.backtesting.metrics import PerformanceMetrics


class BacktestResults:
    """
    Container for backtest results.
    
    Provides:
    - Performance metrics (Sharpe, Sortino, etc.)
    - Daily equity curve
    - Trade history
    - Final portfolio state
    """
    
    def __init__(
        self,
        strategy_name: str,
        start_date: date,
        end_date: date,
        initial_capital: float,
        final_value: float,
        daily_snapshots: list[dict],
        executed_trades: list[Trade],
        portfolio: Portfolio,
    ):
        """
        Initialize backtest results.
        
        Args:
            strategy_name: Name of the strategy
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            final_value: Ending portfolio value
            daily_snapshots: List of daily portfolio snapshots
            executed_trades: List of executed trades
            portfolio: Final portfolio state
        """
        self.strategy_name = strategy_name
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.final_value = final_value
        self.daily_snapshots = daily_snapshots
        self.executed_trades = executed_trades
        self.portfolio = portfolio
        
        # Calculate metrics
        self._metrics: Optional[dict] = None
    
    @property
    def metrics(self) -> dict:
        """Get performance metrics (calculated lazily)."""
        if self._metrics is None:
            self._metrics = self._calculate_metrics()
        return self._metrics
    
    @property
    def equity_curve(self) -> pd.DataFrame:
        """Get equity curve as DataFrame."""
        return pd.DataFrame(self.daily_snapshots)
    
    @property
    def trade_history(self) -> pd.DataFrame:
        """Get trade history as DataFrame."""
        if not self.executed_trades:
            return pd.DataFrame()
        
        trades_data = []
        for trade in self.executed_trades:
            trades_data.append({
                "timestamp": trade.timestamp,
                "ticker": trade.ticker,
                "action": trade.action,
                "quantity": float(trade.quantity),
                "price": float(trade.price),
                "fees": float(trade.fees),
                "slippage": float(trade.slippage),
                "total_cost": float(trade.total_cost),
            })
        
        return pd.DataFrame(trades_data)
    
    @property
    def num_trades(self) -> int:
        """Get total number of trades executed."""
        return len(self.executed_trades)
    
    @property
    def duration_days(self) -> int:
        """Get backtest duration in days."""
        return (self.end_date - self.start_date).days
    
    def _calculate_metrics(self) -> dict:
        """Calculate performance metrics."""
        # Extract daily values
        daily_values = [snap["total_value"] for snap in self.daily_snapshots]
        
        # Calculate trade P&Ls for trade-level metrics
        trades_pnl = self._calculate_trades_pnl()
        
        # Use PerformanceMetrics calculator
        calculator = PerformanceMetrics(
            daily_values=daily_values,
            initial_capital=self.initial_capital,
        )
        
        metrics = calculator.calculate_all(trades_pnl=trades_pnl)
        
        # Add backtest metadata
        metrics.update({
            "strategy_name": self.strategy_name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "duration_days": self.duration_days,
            "initial_capital": self.initial_capital,
            "final_value": self.final_value,
        })
        
        return metrics
    
    def _calculate_trades_pnl(self) -> list[float]:
        """
        Calculate P&L for each closed trade.
        
        Note: This is a simplified calculation for metrics.
        Real P&L is tracked in portfolio.realized_pnl.
        """
        # For now, use realized P&L from portfolio
        # In a more sophisticated version, we'd track per-trade P&L
        if not self.executed_trades:
            return []
        
        # Estimate: divide total realized P&L by number of closing trades
        closing_trades = [
            t for t in self.executed_trades 
            if t.is_closing
        ]
        
        if not closing_trades:
            return []
        
        # Simple approximation
        avg_pnl_per_trade = float(self.portfolio.realized_pnl) / len(closing_trades)
        
        return [avg_pnl_per_trade] * len(closing_trades)
    
    def summary(self) -> str:
        """Get formatted summary of backtest results."""
        metrics = self.metrics
        
        summary = f"""
╔════════════════════════════════════════════════════════════╗
║  BACKTEST RESULTS: {self.strategy_name:<42} ║
╠════════════════════════════════════════════════════════════╣
║  Period: {self.start_date} to {self.end_date}              ║
║  Duration: {self.duration_days} days                                      ║
╠════════════════════════════════════════════════════════════╣
║  RETURNS                                                   ║
║    Initial Capital:        ${self.initial_capital:>15,.2f}       ║
║    Final Value:            ${self.final_value:>15,.2f}       ║
║    Total Return:           {metrics['total_return']:>14.2%}        ║
║    Annualized Return:      {metrics['annualized_return']:>14.2%}        ║
╠════════════════════════════════════════════════════════════╣
║  RISK METRICS                                              ║
║    Volatility (Annual):    {metrics['volatility']:>14.2%}        ║
║    Sharpe Ratio:           {metrics['sharpe_ratio']:>15.2f}        ║
║    Sortino Ratio:          {metrics['sortino_ratio']:>15.2f}        ║
║    Max Drawdown:           {metrics['max_drawdown']:>14.2%}        ║
║    Calmar Ratio:           {metrics['calmar_ratio']:>15.2f}        ║
╠════════════════════════════════════════════════════════════╣
║  TRADING ACTIVITY                                          ║
║    Number of Trades:       {metrics.get('num_trades', 0):>15}        ║
║    Win Rate:               {metrics.get('win_rate', 0):>14.2%}        ║
║    Profit Factor:          {metrics.get('profit_factor', 0):>15.2f}        ║
║    Avg Win/Loss Ratio:     {metrics.get('avg_win_loss_ratio', 0):>15.2f}        ║
╚════════════════════════════════════════════════════════════╝
        """.strip()
        
        return summary
    
    def to_dict(self) -> dict:
        """Convert results to dictionary format (for JSON serialization)."""
        return {
            "strategy_name": self.strategy_name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_capital": self.initial_capital,
            "final_value": self.final_value,
            "metrics": self.metrics,
            "num_trades": self.num_trades,
            "duration_days": self.duration_days,
        }
