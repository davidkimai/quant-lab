"""
Repository for backtest data access.

Provides CRUD operations for BacktestRun model.
"""

from typing import Optional
from sqlalchemy.orm import Session

from quant_lab_api.database.models import BacktestRun


class BacktestRepository:
    """Repository for managing backtest persistence."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def create(
        self,
        strategy_name: str,
        start_date: str,
        end_date: str,
        duration_days: int,
        initial_capital: float,
        tickers: list[str],
        final_value: float,
        total_return: float,
        annualized_return: float,
        metrics: dict,
        equity_curve: list[dict],
        trade_history: list[dict],
        config: Optional[dict] = None,
        status: str = "completed",
        error_message: Optional[str] = None,
    ) -> BacktestRun:
        """
        Create a new backtest record.

        Args:
            strategy_name: Name of the strategy used
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            duration_days: Number of days in backtest
            initial_capital: Starting capital
            tickers: List of tickers traded
            final_value: Final portfolio value
            total_return: Total return percentage
            annualized_return: Annualized return percentage
            metrics: Dictionary of performance metrics
            equity_curve: List of daily portfolio snapshots
            trade_history: List of trades executed
            config: Optional strategy configuration
            status: Backtest status (completed, failed, running)
            error_message: Optional error message if failed

        Returns:
            Created BacktestRun instance
        """
        # Extract individual metrics for indexed columns
        sharpe_ratio = metrics.get("sharpe_ratio")
        sortino_ratio = metrics.get("sortino_ratio")
        max_drawdown = metrics.get("max_drawdown")
        volatility = metrics.get("volatility")
        num_trades = metrics.get("num_trades", 0)
        win_rate = metrics.get("win_rate")
        profit_factor = metrics.get("profit_factor")

        backtest = BacktestRun(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            initial_capital=initial_capital,
            tickers=tickers,
            config=config,
            final_value=final_value,
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            volatility=volatility,
            num_trades=num_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            metrics=metrics,
            equity_curve=equity_curve,
            trade_history=trade_history,
            status=status,
            error_message=error_message,
        )

        self.db.add(backtest)
        self.db.commit()
        self.db.refresh(backtest)

        return backtest

    def get_by_id(self, backtest_id: int) -> Optional[BacktestRun]:
        """
        Get a backtest by ID.

        Args:
            backtest_id: Backtest ID

        Returns:
            BacktestRun instance or None if not found
        """
        return self.db.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        strategy_name: Optional[str] = None,
    ) -> list[BacktestRun]:
        """
        Get all backtests with pagination and optional filtering.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            strategy_name: Optional strategy name filter

        Returns:
            List of BacktestRun instances
        """
        query = self.db.query(BacktestRun)

        if strategy_name:
            query = query.filter(BacktestRun.strategy_name == strategy_name)

        return query.order_by(BacktestRun.created_at.desc()).offset(skip).limit(limit).all()

    def delete(self, backtest_id: int) -> bool:
        """
        Delete a backtest by ID.

        Args:
            backtest_id: Backtest ID

        Returns:
            True if deleted, False if not found
        """
        backtest = self.get_by_id(backtest_id)

        if not backtest:
            return False

        self.db.delete(backtest)
        self.db.commit()

        return True

    def update_status(
        self,
        backtest_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[BacktestRun]:
        """
        Update backtest status.

        Args:
            backtest_id: Backtest ID
            status: New status (completed, failed, running)
            error_message: Optional error message

        Returns:
            Updated BacktestRun instance or None if not found
        """
        backtest = self.get_by_id(backtest_id)

        if not backtest:
            return None

        backtest.status = status
        if error_message:
            backtest.error_message = error_message

        self.db.commit()
        self.db.refresh(backtest)

        return backtest
