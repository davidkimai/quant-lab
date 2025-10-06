"""
SQLAlchemy ORM models for backtest persistence.

Models:
- BacktestRun: Stores backtest metadata and results
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func

from quant_lab_api.database.base import Base


class BacktestRun(Base):
    """
    Store backtest execution results.
    
    Contains:
    - Strategy and configuration metadata
    - Performance metrics
    - Equity curve data
    - Trade history
    """
    
    __tablename__ = "backtest_runs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Metadata
    strategy_name = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Date range
    start_date = Column(String(10), nullable=False)  # ISO format YYYY-MM-DD
    end_date = Column(String(10), nullable=False)
    duration_days = Column(Integer, nullable=False)
    
    # Configuration
    initial_capital = Column(Float, nullable=False)
    tickers = Column(JSON, nullable=False)  # List of tickers
    config = Column(JSON, nullable=True)     # Strategy config
    
    # Results
    final_value = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    annualized_return = Column(Float, nullable=False)
    
    # Risk metrics
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    
    # Trading metrics
    num_trades = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    
    # Detailed data (JSON)
    metrics = Column(JSON, nullable=True)           # Full metrics dict
    equity_curve = Column(JSON, nullable=True)      # Daily snapshots
    trade_history = Column(JSON, nullable=True)     # Trade details
    
    # Status
    status = Column(
        String(20),
        nullable=False,
        default="completed",
        index=True,
    )  # completed, failed, running
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<BacktestRun(id={self.id}, strategy={self.strategy_name}, return={self.total_return:.2%})>"
