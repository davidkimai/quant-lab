"""
CSV data provider for loading local historical data.

This provider reads OHLCV data from CSV files with a specific format:
- Filename: {ticker}.csv
- Columns: date, open, high, low, close, volume
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional
import pandas as pd

from quant_lab.data.protocols import (
    DataProvider,
    DataProviderError,
    DataNotFoundError,
)
from quant_lab.models.market_data import Fundamentals


class CSVDataProvider:
    """
    Data provider that loads OHLCV data from CSV files.
    
    Expected directory structure:
        data_dir/
            AAPL.csv
            MSFT.csv
            TSLA.csv
    
    Expected CSV format:
        date,open,high,low,close,volume
        2024-01-01,150.00,152.50,149.00,151.00,1000000
    
    Args:
        data_dir: Path to directory containing CSV files
        fundamentals_file: Optional path to fundamentals CSV
    """
    
    def __init__(
        self,
        data_dir: str | Path,
        fundamentals_file: Optional[str | Path] = None,
    ):
        self.data_dir = Path(data_dir)
        self.fundamentals_file = (
            Path(fundamentals_file) if fundamentals_file else None
        )
        
        if not self.data_dir.exists():
            raise DataProviderError(f"Data directory not found: {self.data_dir}")
    
    async def fetch_prices(
        self,
        tickers: list[str],
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """
        Load price data from CSV files.
        
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
            csv_path = self.data_dir / f"{ticker}.csv"
            
            if not csv_path.exists():
                raise DataNotFoundError(f"CSV file not found for {ticker}: {csv_path}")
            
            try:
                # Read CSV
                df = pd.read_csv(csv_path)
                
                # Validate required columns
                required_cols = ["date", "open", "high", "low", "close", "volume"]
                missing_cols = set(required_cols) - set(df.columns)
                if missing_cols:
                    raise DataProviderError(
                        f"CSV for {ticker} missing columns: {missing_cols}"
                    )
                
                # Parse dates
                df["date"] = pd.to_datetime(df["date"]).dt.date
                
                # Filter date range
                df = df[
                    (df["date"] >= start_date) & (df["date"] <= end_date)
                ].copy()
                
                if df.empty:
                    raise DataNotFoundError(
                        f"No data for {ticker} in range {start_date} to {end_date}"
                    )
                
                # Convert prices to Decimal
                for col in ["open", "high", "low", "close"]:
                    df[col] = df[col].apply(lambda x: Decimal(str(x)))
                
                # Ensure volume is int
                df["volume"] = df["volume"].astype(int)
                
                # Add ticker column
                df["ticker"] = ticker
                
                # Select and order columns
                df = df[["ticker", "date", "open", "high", "low", "close", "volume"]]
                
                all_data.append(df)
            
            except pd.errors.EmptyDataError:
                raise DataNotFoundError(f"CSV file for {ticker} is empty")
            except Exception as e:
                raise DataProviderError(
                    f"Error reading CSV for {ticker}: {str(e)}"
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
        Load fundamental data from CSV file.
        
        Expected CSV format:
            ticker,market_cap,pe_ratio,revenue,net_income,...
            AAPL,2500000000000,28.5,394000000000,99800000000,...
        
        Returns:
            Dictionary mapping ticker to Fundamentals object
        """
        if not tickers:
            raise ValueError("Tickers list cannot be empty")
        
        if not self.fundamentals_file or not self.fundamentals_file.exists():
            # Return empty dict if no fundamentals file
            return {}
        
        try:
            df = pd.read_csv(self.fundamentals_file)
            
            if "ticker" not in df.columns:
                raise DataProviderError("Fundamentals CSV must have 'ticker' column")
            
            # Normalize tickers
            df["ticker"] = df["ticker"].str.upper()
            tickers_upper = [t.upper() for t in tickers]
            
            # Filter to requested tickers
            df = df[df["ticker"].isin(tickers_upper)]
            
            fundamentals = {}
            
            for _, row in df.iterrows():
                ticker = row["ticker"]
                
                # Convert to Fundamentals object
                fundamentals[ticker] = Fundamentals(
                    ticker=ticker,
                    market_cap=self._to_decimal(row.get("market_cap")),
                    pe_ratio=self._to_float(row.get("pe_ratio")),
                    revenue=self._to_decimal(row.get("revenue")),
                    net_income=self._to_decimal(row.get("net_income")),
                    total_assets=self._to_decimal(row.get("total_assets")),
                    total_liabilities=self._to_decimal(row.get("total_liabilities")),
                    free_cash_flow=self._to_decimal(row.get("free_cash_flow")),
                    roe=self._to_float(row.get("roe")),
                    roic=self._to_float(row.get("roic")),
                    debt_to_equity=self._to_float(row.get("debt_to_equity")),
                    current_ratio=self._to_float(row.get("current_ratio")),
                    revenue_growth=self._to_float(row.get("revenue_growth")),
                    earnings_growth=self._to_float(row.get("earnings_growth")),
                )
            
            return fundamentals
        
        except Exception as e:
            raise DataProviderError(
                f"Error reading fundamentals CSV: {str(e)}"
            )
    
    async def validate_tickers(self, tickers: list[str]) -> list[str]:
        """Return list of tickers that have CSV files available."""
        valid_tickers = []
        
        for ticker in tickers:
            ticker = ticker.upper()
            csv_path = self.data_dir / f"{ticker}.csv"
            if csv_path.exists():
                valid_tickers.append(ticker)
        
        return valid_tickers
    
    @staticmethod
    def _to_decimal(value: float | str | None) -> Optional[Decimal]:
        """Convert value to Decimal, handling None and NaN."""
        if value is None or pd.isna(value):
            return None
        return Decimal(str(value))
    
    @staticmethod
    def _to_float(value: float | str | None) -> Optional[float]:
        """Convert value to float, handling None and NaN."""
        if value is None or pd.isna(value):
            return None
        return float(value)
