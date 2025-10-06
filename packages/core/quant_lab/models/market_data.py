"""
Market data models for price history and fundamental metrics.

MarketData provides a unified interface for strategies to access
historical prices and fundamental data without knowing the source.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
import pandas as pd
from pydantic import BaseModel, Field, field_validator


class OHLCV(BaseModel):
    """
    Open-High-Low-Close-Volume data for a single trading day.
    
    Attributes:
        date: Trading date
        open: Opening price
        high: High price
        low: Low price
        close: Closing price
        volume: Trading volume
        adjusted_close: Adjusted closing price (for splits/dividends)
    """
    
    date: date
    open: Decimal = Field(gt=0)
    high: Decimal = Field(gt=0)
    low: Decimal = Field(gt=0)
    close: Decimal = Field(gt=0)
    volume: int = Field(ge=0)
    adjusted_close: Optional[Decimal] = None
    
    @field_validator("open", "high", "low", "close", "adjusted_close", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | int | Decimal | None) -> Decimal | None:
        """Convert numeric values to Decimal for precision."""
        if v is None:
            return None
        return Decimal(str(v)) if not isinstance(v, Decimal) else v
    
    class Config:
        frozen = True


class Fundamentals(BaseModel):
    """
    Fundamental financial metrics for a company.
    
    Attributes:
        ticker: Stock symbol
        market_cap: Market capitalization
        pe_ratio: Price-to-earnings ratio
        revenue: Total revenue
        net_income: Net income
        total_assets: Total assets
        total_liabilities: Total liabilities
        free_cash_flow: Free cash flow
        roe: Return on equity
        roic: Return on invested capital
        debt_to_equity: Debt-to-equity ratio
        current_ratio: Current ratio
        revenue_growth: Year-over-year revenue growth
        earnings_growth: Year-over-year earnings growth
    """
    
    ticker: str
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[float] = None
    revenue: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    free_cash_flow: Optional[Decimal] = None
    roe: Optional[float] = None
    roic: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    
    @field_validator("ticker")
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Normalize ticker to uppercase."""
        return v.upper().strip()
    
    class Config:
        frozen = True


class MarketData(BaseModel):
    """
    Complete market data container for strategy analysis.
    
    Provides historical prices and fundamental data for a set of tickers.
    Uses pandas DataFrames for efficient time-series operations.
    
    Attributes:
        tickers: List of stock symbols
        start_date: Beginning of data range
        end_date: End of data range
        prices: DataFrame with columns [ticker, date, open, high, low, close, volume]
        fundamentals: Dictionary mapping ticker to Fundamentals
    """
    
    tickers: list[str]
    start_date: date
    end_date: date
    prices: pd.DataFrame
    fundamentals: dict[str, Fundamentals] = Field(default_factory=dict)
    
    @field_validator("tickers")
    @classmethod
    def normalize_tickers(cls, v: list[str]) -> list[str]:
        """Normalize all tickers to uppercase."""
        return [t.upper().strip() for t in v]
    
    def get_prices(self, ticker: str) -> pd.DataFrame:
        """Get price history for a specific ticker."""
        ticker = ticker.upper()
        if ticker not in self.tickers:
            raise ValueError(f"Ticker {ticker} not in dataset")
        return self.prices[self.prices["ticker"] == ticker].copy()
    
    def get_fundamentals(self, ticker: str) -> Optional[Fundamentals]:
        """Get fundamental data for a specific ticker."""
        return self.fundamentals.get(ticker.upper())
    
    def as_of(self, as_of_date: date) -> "MarketData":
        """
        Return MarketData with prices up to (and including) as_of_date.
        
        This enables point-in-time analysis for backtesting.
        """
        filtered_prices = self.prices[self.prices["date"] <= as_of_date].copy()
        
        return MarketData(
            tickers=self.tickers,
            start_date=self.start_date,
            end_date=as_of_date,
            prices=filtered_prices,
            fundamentals=self.fundamentals,
        )
    
    class Config:
        arbitrary_types_allowed = True  # Allow pandas DataFrame
