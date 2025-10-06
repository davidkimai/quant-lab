"""
Yahoo Finance data provider using yfinance library.

This provider fetches real-time and historical data from Yahoo Finance,
including OHLCV data and basic fundamental metrics.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
import pandas as pd
import yfinance as yf

from quant_lab.data.protocols import (
    DataProvider,
    DataProviderError,
    DataNotFoundError,
    DataProviderConnectionError,
)
from quant_lab.models.market_data import Fundamentals


class YahooFinanceProvider:
    """
    Data provider for Yahoo Finance.
    
    Uses yfinance library to fetch historical prices and fundamental data.
    This is the recommended free data source for real-time backtesting.
    
    Args:
        timeout: Request timeout in seconds
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    async def fetch_prices(
        self,
        tickers: list[str],
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """
        Fetch historical price data from Yahoo Finance.
        
        Returns:
            DataFrame with columns: [ticker, date, open, high, low, close, volume]
        """
        if not tickers:
            raise ValueError("Tickers list cannot be empty")
        
        if start_date > end_date:
            raise ValueError(f"start_date {start_date} cannot be after end_date {end_date}")
        
        all_data = []
        
        for ticker in tickers:
            ticker = ticker.upper()
            
            try:
                # Download data from Yahoo Finance
                stock = yf.Ticker(ticker)
                df = stock.history(
                    start=start_date,
                    end=end_date,
                    timeout=self.timeout,
                )
                
                if df.empty:
                    raise DataNotFoundError(
                        f"No data returned for {ticker} in range {start_date} to {end_date}"
                    )
                
                # Reset index to make date a column
                df = df.reset_index()
                
                # Rename columns to match our schema
                df = df.rename(
                    columns={
                        "Date": "date",
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Volume": "volume",
                    }
                )
                
                # Convert date column
                df["date"] = pd.to_datetime(df["date"]).dt.date
                
                # Convert prices to Decimal
                for col in ["open", "high", "low", "close"]:
                    df[col] = df[col].apply(lambda x: Decimal(str(round(x, 2))))
                
                # Ensure volume is int
                df["volume"] = df["volume"].astype(int)
                
                # Add ticker column
                df["ticker"] = ticker
                
                # Select and order columns
                df = df[["ticker", "date", "open", "high", "low", "close", "volume"]]
                
                all_data.append(df)
            
            except Exception as e:
                if "No data found" in str(e) or "No price data found" in str(e):
                    raise DataNotFoundError(f"No data found for {ticker}: {str(e)}")
                elif "connection" in str(e).lower() or "timeout" in str(e).lower():
                    raise DataProviderConnectionError(
                        f"Connection error fetching {ticker}: {str(e)}"
                    )
                else:
                    raise DataProviderError(
                        f"Error fetching data for {ticker}: {str(e)}"
                    )
        
        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.sort_values(["ticker", "date"]).reset_index(drop=True)
        
        return combined_df
    
    async def fetch_fundamentals(
        self,
        tickers: list[str],
    ) -> dict[str, Fundamentals]:
        """
        Fetch fundamental data from Yahoo Finance.
        
        Note: Yahoo Finance provides limited fundamental data.
        For comprehensive fundamentals, consider using a dedicated provider.
        
        Returns:
            Dictionary mapping ticker to Fundamentals object
        """
        if not tickers:
            raise ValueError("Tickers list cannot be empty")
        
        fundamentals = {}
        
        for ticker in tickers:
            ticker = ticker.upper()
            
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                if not info:
                    continue
                
                # Extract available fundamental data
                fundamentals[ticker] = Fundamentals(
                    ticker=ticker,
                    market_cap=self._to_decimal(info.get("marketCap")),
                    pe_ratio=self._to_float(info.get("trailingPE")),
                    revenue=self._to_decimal(info.get("totalRevenue")),
                    net_income=self._to_decimal(info.get("netIncomeToCommon")),
                    total_assets=self._to_decimal(info.get("totalAssets")),
                    total_liabilities=self._to_decimal(info.get("totalDebt")),
                    free_cash_flow=self._to_decimal(info.get("freeCashflow")),
                    roe=self._to_float(info.get("returnOnEquity")),
                    roic=None,  # Not directly available
                    debt_to_equity=self._to_float(info.get("debtToEquity")),
                    current_ratio=self._to_float(info.get("currentRatio")),
                    revenue_growth=self._to_float(info.get("revenueGrowth")),
                    earnings_growth=self._to_float(info.get("earningsGrowth")),
                )
            
            except Exception as e:
                # Skip tickers that fail (don't halt entire fetch)
                print(f"Warning: Could not fetch fundamentals for {ticker}: {str(e)}")
                continue
        
        return fundamentals
    
    async def validate_tickers(self, tickers: list[str]) -> list[str]:
        """
        Validate tickers by attempting to fetch basic info.
        
        Returns:
            List of tickers that are valid and accessible
        """
        valid_tickers = []
        
        for ticker in tickers:
            ticker = ticker.upper()
            
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Check if we got valid data
                if info and "regularMarketPrice" in info:
                    valid_tickers.append(ticker)
            
            except Exception:
                # Invalid ticker, skip it
                continue
        
        return valid_tickers
    
    @staticmethod
    def _to_decimal(value: float | int | None) -> Optional[Decimal]:
        """Convert value to Decimal, handling None."""
        if value is None or pd.isna(value):
            return None
        return Decimal(str(value))
    
    @staticmethod
    def _to_float(value: float | int | None) -> Optional[float]:
        """Convert value to float, handling None."""
        if value is None or pd.isna(value):
            return None
        return float(value)
