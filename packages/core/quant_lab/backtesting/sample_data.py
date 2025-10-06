"""
Generate sample CSV data for backtesting validation.

Creates realistic-looking price data for AAPL, MSFT, TSLA
covering 6 months (120 trading days) for testing.
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
from decimal import Decimal

# Set random seed for reproducibility
np.random.seed(42)

def generate_price_data(ticker, start_price, days=120, trend=0.001, volatility=0.02):
    """Generate synthetic OHLCV data with trend and noise."""
    
    # Generate trading days (skip weekends)
    dates = []
    current_date = date(2024, 1, 2)  # Start on a Tuesday
    while len(dates) < days:
        if current_date.weekday() < 5:  # Monday-Friday
            dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Generate prices with geometric Brownian motion
    prices = [start_price]
    for i in range(1, days):
        daily_return = trend + volatility * np.random.randn()
        new_price = prices[-1] * (1 + daily_return)
        prices.append(max(new_price, 1.0))  # Ensure positive prices
    
    # Generate OHLCV data
    data = []
    for i, (d, close) in enumerate(zip(dates, prices)):
        # Open near previous close with small gap
        open_price = close * (1 + np.random.uniform(-0.005, 0.005))
        
        # High and low based on intraday volatility
        high = close * (1 + abs(np.random.uniform(0, 0.015)))
        low = close * (1 - abs(np.random.uniform(0, 0.015)))
        
        # Ensure OHLC relationships
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Volume with realistic variation
        base_volume = 50000000
        volume = int(base_volume * (1 + np.random.uniform(-0.3, 0.5)))
        
        data.append({
            "date": d,
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": volume,
        })
    
    return pd.DataFrame(data)

# Generate data for each ticker
print("Generating sample CSV data...")

# AAPL: Moderate growth
aapl_df = generate_price_data("AAPL", start_price=150.0, trend=0.0015, volatility=0.018)
aapl_df.to_csv("/home/claude/quant-lab/data/AAPL.csv", index=False)
print(f"✓ Created AAPL.csv ({len(aapl_df)} days)")

# MSFT: Steady growth
msft_df = generate_price_data("MSFT", start_price=350.0, trend=0.0012, volatility=0.015)
msft_df.to_csv("/home/claude/quant-lab/data/MSFT.csv", index=False)
print(f"✓ Created MSFT.csv ({len(msft_df)} days)")

# TSLA: High volatility
tsla_df = generate_price_data("TSLA", start_price=200.0, trend=0.002, volatility=0.035)
tsla_df.to_csv("/home/claude/quant-lab/data/TSLA.csv", index=False)
print(f"✓ Created TSLA.csv ({len(tsla_df)} days)")

# Create fundamentals data
fundamentals_data = [
    {
        "ticker": "AAPL",
        "market_cap": 2800000000000,
        "pe_ratio": 28.5,
        "revenue": 394000000000,
        "net_income": 99800000000,
        "total_assets": 352000000000,
        "total_liabilities": 290000000000,
        "free_cash_flow": 99000000000,
        "roe": 0.28,
        "roic": 0.35,
        "debt_to_equity": 0.85,
        "current_ratio": 1.1,
        "revenue_growth": 0.11,
        "earnings_growth": 0.13,
    },
    {
        "ticker": "MSFT",
        "market_cap": 2900000000000,
        "pe_ratio": 32.0,
        "revenue": 211000000000,
        "net_income": 72000000000,
        "total_assets": 411000000000,
        "total_liabilities": 198000000000,
        "free_cash_flow": 65000000000,
        "roe": 0.34,
        "roic": 0.28,
        "debt_to_equity": 0.45,
        "current_ratio": 1.8,
        "revenue_growth": 0.12,
        "earnings_growth": 0.15,
    },
    {
        "ticker": "TSLA",
        "market_cap": 700000000000,
        "pe_ratio": 65.0,
        "revenue": 96000000000,
        "net_income": 12000000000,
        "total_assets": 106000000000,
        "total_liabilities": 43000000000,
        "free_cash_flow": 8000000000,
        "roe": 0.19,
        "roic": 0.15,
        "debt_to_equity": 0.15,
        "current_ratio": 1.5,
        "revenue_growth": 0.51,
        "earnings_growth": 0.42,
    },
]

fundamentals_df = pd.DataFrame(fundamentals_data)
fundamentals_df.to_csv("/home/claude/quant-lab/data/fundamentals.csv", index=False)
print(f"✓ Created fundamentals.csv")

print("\nSample data generation complete!")
print(f"Location: /home/claude/quant-lab/data/")
