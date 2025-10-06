"""
Data provider protocols for pluggable data sources.

The DataProvider protocol defines a common interface for fetching market data
from various sources (CSV files, Yahoo Finance, Alpha Vantage, Polygon, etc.).
"""

from datetime import date
from typing import Protocol, runtime_checkable
import pandas as pd

from quant_lab.models.market_data import Fundamentals


@runtime_checkable
class DataProvider(Protocol):
    """
    Protocol for market data providers.
    
    All data providers must implement these methods to be compatible
    with the backtesting engine and strategies.
    """
    
    async def fetch_prices(
        self,
        tickers: list[str],
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """
        Fetch historical price data for tickers.
        
        Args:
            tickers: List of stock symbols
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
        
        Returns:
            DataFrame with columns: [ticker, date, open, high, low, close, volume]
            All price columns should be Decimal type.
            
        Raises:
            ValueError: If tickers list is empty or dates are invalid
            DataProviderError: If data fetch fails
        """
        ...
    
    async def fetch_fundamentals(
        self,
        tickers: list[str],
    ) -> dict[str, Fundamentals]:
        """
        Fetch fundamental data for tickers.
        
        Args:
            tickers: List of stock symbols
        
        Returns:
            Dictionary mapping ticker to Fundamentals object.
            Missing tickers will not be in the dictionary.
            
        Raises:
            ValueError: If tickers list is empty
            DataProviderError: If data fetch fails
        """
        ...
    
    async def validate_tickers(self, tickers: list[str]) -> list[str]:
        """
        Validate and return list of available tickers.
        
        Args:
            tickers: List of stock symbols to validate
        
        Returns:
            List of valid tickers (may be subset of input)
        """
        ...


class DataProviderError(Exception):
    """Base exception for data provider errors."""
    
    pass


class DataNotFoundError(DataProviderError):
    """Raised when requested data is not available."""
    
    pass


class DataProviderConnectionError(DataProviderError):
    """Raised when provider cannot be reached."""
    
    pass


class DataProviderRateLimitError(DataProviderError):
    """Raised when rate limit is exceeded."""
    
    pass
