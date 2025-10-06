"""
Performance metrics calculator for backtesting results.

Calculates key risk-adjusted return metrics:
- Sharpe Ratio: Risk-adjusted returns
- Sortino Ratio: Downside risk-adjusted returns
- Max Drawdown: Largest peak-to-trough decline
- Calmar Ratio: Return / Max Drawdown
- Win Rate: Percentage of profitable trades
"""

from decimal import Decimal
from typing import Optional
import numpy as np
import pandas as pd


class PerformanceMetrics:
    """
    Calculate performance metrics from backtest results.
    
    Metrics:
    - Total Return %
    - Annualized Return %
    - Sharpe Ratio
    - Sortino Ratio
    - Max Drawdown %
    - Calmar Ratio
    - Volatility (annualized)
    - Win Rate
    - Average Win / Average Loss
    """
    
    def __init__(
        self,
        daily_values: list[float],
        initial_capital: float,
        risk_free_rate: float = 0.02,  # 2% annual risk-free rate
    ):
        """
        Initialize metrics calculator.
        
        Args:
            daily_values: List of daily portfolio values
            initial_capital: Starting capital
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        self.daily_values = np.array(daily_values)
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        
        # Calculate daily returns
        self.daily_returns = np.diff(self.daily_values) / self.daily_values[:-1]
        
        # Trading days per year (approx)
        self.trading_days_per_year = 252
    
    def total_return(self) -> float:
        """Calculate total return percentage."""
        if len(self.daily_values) == 0:
            return 0.0
        
        final_value = self.daily_values[-1]
        return (final_value - self.initial_capital) / self.initial_capital
    
    def annualized_return(self) -> float:
        """Calculate annualized return (CAGR)."""
        if len(self.daily_values) < 2:
            return 0.0
        
        total_return = self.total_return()
        num_days = len(self.daily_values) - 1
        years = num_days / self.trading_days_per_year
        
        if years <= 0:
            return 0.0
        
        # CAGR formula: (ending_value / beginning_value)^(1/years) - 1
        cagr = (1 + total_return) ** (1 / years) - 1
        return cagr
    
    def volatility(self, annualized: bool = True) -> float:
        """
        Calculate volatility (standard deviation of returns).
        
        Args:
            annualized: If True, return annualized volatility
        """
        if len(self.daily_returns) == 0:
            return 0.0
        
        vol = np.std(self.daily_returns, ddof=1)
        
        if annualized:
            vol *= np.sqrt(self.trading_days_per_year)
        
        return vol
    
    def sharpe_ratio(self) -> float:
        """
        Calculate Sharpe Ratio (risk-adjusted return).
        
        Formula: (Return - Risk-Free Rate) / Volatility
        """
        if len(self.daily_returns) == 0:
            return 0.0
        
        ann_return = self.annualized_return()
        ann_vol = self.volatility(annualized=True)
        
        if ann_vol == 0:
            return 0.0
        
        sharpe = (ann_return - self.risk_free_rate) / ann_vol
        return sharpe
    
    def sortino_ratio(self) -> float:
        """
        Calculate Sortino Ratio (downside risk-adjusted return).
        
        Similar to Sharpe but only considers downside volatility.
        """
        if len(self.daily_returns) == 0:
            return 0.0
        
        ann_return = self.annualized_return()
        
        # Calculate downside deviation (only negative returns)
        negative_returns = self.daily_returns[self.daily_returns < 0]
        
        if len(negative_returns) == 0:
            return float('inf')  # No downside risk
        
        downside_vol = np.std(negative_returns, ddof=1)
        downside_vol_ann = downside_vol * np.sqrt(self.trading_days_per_year)
        
        if downside_vol_ann == 0:
            return 0.0
        
        sortino = (ann_return - self.risk_free_rate) / downside_vol_ann
        return sortino
    
    def max_drawdown(self) -> float:
        """
        Calculate maximum drawdown (largest peak-to-trough decline).
        
        Returns:
            Max drawdown as a negative percentage (e.g., -0.25 for 25% drawdown)
        """
        if len(self.daily_values) < 2:
            return 0.0
        
        # Calculate running maximum
        cumulative_max = np.maximum.accumulate(self.daily_values)
        
        # Calculate drawdown at each point
        drawdowns = (self.daily_values - cumulative_max) / cumulative_max
        
        # Return the maximum drawdown (most negative value)
        max_dd = np.min(drawdowns)
        
        return max_dd
    
    def calmar_ratio(self) -> float:
        """
        Calculate Calmar Ratio (return / max drawdown).
        
        Higher is better. Measures return per unit of drawdown risk.
        """
        max_dd = abs(self.max_drawdown())
        
        if max_dd == 0:
            return float('inf')
        
        ann_return = self.annualized_return()
        calmar = ann_return / max_dd
        
        return calmar
    
    def win_rate(self, trades_pnl: list[float]) -> float:
        """
        Calculate win rate from list of trade P&Ls.
        
        Args:
            trades_pnl: List of realized P&L from each trade
        
        Returns:
            Win rate as percentage (0.0 to 1.0)
        """
        if not trades_pnl:
            return 0.0
        
        winning_trades = sum(1 for pnl in trades_pnl if pnl > 0)
        return winning_trades / len(trades_pnl)
    
    def profit_factor(self, trades_pnl: list[float]) -> float:
        """
        Calculate profit factor (gross profit / gross loss).
        
        Args:
            trades_pnl: List of realized P&L from each trade
        
        Returns:
            Profit factor (>1.0 means profitable overall)
        """
        if not trades_pnl:
            return 0.0
        
        gross_profit = sum(pnl for pnl in trades_pnl if pnl > 0)
        gross_loss = abs(sum(pnl for pnl in trades_pnl if pnl < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def average_win_loss_ratio(self, trades_pnl: list[float]) -> float:
        """
        Calculate average win / average loss ratio.
        
        Args:
            trades_pnl: List of realized P&L from each trade
        
        Returns:
            Ratio of average winning trade to average losing trade
        """
        if not trades_pnl:
            return 0.0
        
        wins = [pnl for pnl in trades_pnl if pnl > 0]
        losses = [abs(pnl) for pnl in trades_pnl if pnl < 0]
        
        if not wins or not losses:
            return 0.0
        
        avg_win = sum(wins) / len(wins)
        avg_loss = sum(losses) / len(losses)
        
        if avg_loss == 0:
            return float('inf')
        
        return avg_win / avg_loss
    
    def calculate_all(self, trades_pnl: Optional[list[float]] = None) -> dict:
        """
        Calculate all metrics and return as dictionary.
        
        Args:
            trades_pnl: Optional list of trade P&Ls for trade-level metrics
        
        Returns:
            Dictionary of all calculated metrics
        """
        metrics = {
            "total_return": self.total_return(),
            "annualized_return": self.annualized_return(),
            "volatility": self.volatility(annualized=True),
            "sharpe_ratio": self.sharpe_ratio(),
            "sortino_ratio": self.sortino_ratio(),
            "max_drawdown": self.max_drawdown(),
            "calmar_ratio": self.calmar_ratio(),
        }
        
        # Add trade-level metrics if trades provided
        if trades_pnl is not None:
            metrics.update({
                "win_rate": self.win_rate(trades_pnl),
                "profit_factor": self.profit_factor(trades_pnl),
                "avg_win_loss_ratio": self.average_win_loss_ratio(trades_pnl),
                "num_trades": len(trades_pnl),
            })
        
        return metrics
