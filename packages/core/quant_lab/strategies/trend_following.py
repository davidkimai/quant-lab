"""
Trend Following Strategy - Ride the momentum.

Classic momentum strategy using technical indicators:
- Moving averages (20, 50, 200 day)
- Price momentum
- Volume confirmation

Philosophy: "The trend is your friend" - Enter when momentum is strong,
exit when it reverses.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
import pandas as pd
import numpy as np

from quant_lab.models.market_data import MarketData
from quant_lab.models.signal import Signal, SignalAction
from quant_lab.portfolio.portfolio import Portfolio
from quant_lab.strategies.protocols import StrategyConfig


class TrendFollowingConfig(StrategyConfig):
    """Configuration for Trend Following strategy."""
    
    def __init__(
        self,
        short_window: int = 20,    # 20-day MA
        medium_window: int = 50,   # 50-day MA
        long_window: int = 200,    # 200-day MA
        volume_threshold: float = 1.2,  # 20% above average volume
        momentum_days: int = 20,   # Momentum lookback period
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.short_window = short_window
        self.medium_window = medium_window
        self.long_window = long_window
        self.volume_threshold = volume_threshold
        self.momentum_days = momentum_days


class TrendFollowingStrategy:
    """
    Trend Following Strategy - Momentum-based trading.
    
    Entry signals:
    - Golden Cross: 20-day MA crosses above 50-day MA
    - Strong momentum: Price > 200-day MA
    - Volume confirmation: Recent volume > average
    
    Exit signals:
    - Death Cross: 20-day MA crosses below 50-day MA
    - Momentum breakdown: Price < 200-day MA
    - Stop loss: -10% from entry
    """
    
    name = "Trend Following"
    description = "Momentum-based strategy using moving averages and trend indicators"
    
    def __init__(self, config: Optional[TrendFollowingConfig] = None):
        self.config = config or TrendFollowingConfig()
    
    def generate_signals(
        self,
        market_data: MarketData,
        portfolio: Portfolio,
        current_date: date,
    ) -> list[Signal]:
        """Generate signals based on momentum and trend indicators."""
        signals = []
        
        for ticker in market_data.tickers:
            # Get price history
            prices_df = market_data.get_prices(ticker)
            prices_df = prices_df[prices_df["date"] <= current_date]
            
            if len(prices_df) < self.config.long_window:
                # Not enough data for long-term MA
                continue
            
            # Calculate indicators
            indicators = self._calculate_indicators(prices_df)
            
            if indicators is None:
                continue
            
            # Generate signal
            signal = self._generate_signal_for_ticker(
                ticker=ticker,
                indicators=indicators,
                portfolio=portfolio,
            )
            
            if signal:
                signals.append(signal)
        
        return signals
    
    def _calculate_indicators(self, prices_df: pd.DataFrame) -> Optional[dict]:
        """Calculate technical indicators."""
        if len(prices_df) < self.config.long_window:
            return None
        
        # Extract price and volume data
        prices = prices_df["close"].values
        volumes = prices_df["volume"].values
        
        # Calculate moving averages
        ma_20 = self._moving_average(prices, self.config.short_window)
        ma_50 = self._moving_average(prices, self.config.medium_window)
        ma_200 = self._moving_average(prices, self.config.long_window)
        
        # Current values
        current_price = float(prices[-1])
        prev_ma_20 = ma_20[-2] if len(ma_20) >= 2 else None
        current_ma_20 = ma_20[-1]
        prev_ma_50 = ma_50[-2] if len(ma_50) >= 2 else None
        current_ma_50 = ma_50[-1]
        current_ma_200 = ma_200[-1]
        
        # Price momentum (% change over momentum_days)
        if len(prices) >= self.config.momentum_days:
            momentum = (prices[-1] / prices[-self.config.momentum_days] - 1) * 100
        else:
            momentum = 0.0
        
        # Volume analysis (recent 5 days vs 20-day average)
        recent_volume = np.mean(volumes[-5:]) if len(volumes) >= 5 else volumes[-1]
        avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1]
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Detect crossovers
        golden_cross = (
            prev_ma_20 is not None and 
            prev_ma_50 is not None and
            prev_ma_20 < prev_ma_50 and 
            current_ma_20 > current_ma_50
        )
        
        death_cross = (
            prev_ma_20 is not None and 
            prev_ma_50 is not None and
            prev_ma_20 > prev_ma_50 and 
            current_ma_20 < current_ma_50
        )
        
        return {
            "current_price": current_price,
            "ma_20": current_ma_20,
            "ma_50": current_ma_50,
            "ma_200": current_ma_200,
            "momentum": momentum,
            "volume_ratio": volume_ratio,
            "golden_cross": golden_cross,
            "death_cross": death_cross,
        }
    
    def _generate_signal_for_ticker(
        self,
        ticker: str,
        indicators: dict,
        portfolio: Portfolio,
    ) -> Optional[Signal]:
        """Generate buy/sell signal based on indicators."""
        position = portfolio.get_position(ticker)
        
        # Entry conditions
        if position is None:
            # Buy signals:
            # 1. Golden cross (20 MA crosses above 50 MA)
            # 2. Price above 200-day MA (long-term uptrend)
            # 3. Positive momentum
            # 4. Volume confirmation
            
            buy_score = 0.0
            reasons = []
            
            if indicators["golden_cross"]:
                buy_score += 0.4
                reasons.append("Golden Cross")
            
            if indicators["current_price"] > indicators["ma_200"]:
                buy_score += 0.3
                reasons.append("Above 200-MA")
            
            if indicators["momentum"] > 5:  # >5% momentum
                buy_score += 0.2
                reasons.append(f"{indicators['momentum']:.1f}% momentum")
            
            if indicators["volume_ratio"] > self.config.volume_threshold:
                buy_score += 0.1
                reasons.append("Volume surge")
            
            # Require minimum score to enter
            if buy_score >= 0.6:
                confidence = min(buy_score, 1.0)
                target_value = portfolio.total_value * Decimal(str(self.config.max_position_size))
                quantity = int(target_value / Decimal(str(indicators["current_price"])))
                
                if quantity > 0:
                    return Signal(
                        ticker=ticker,
                        action=SignalAction.BUY,
                        quantity=Decimal(str(quantity)),
                        confidence=confidence,
                        reasoning=", ".join(reasons),
                        metadata={
                            "buy_score": buy_score,
                            "momentum": indicators["momentum"],
                            "volume_ratio": indicators["volume_ratio"],
                        },
                    )
        
        # Exit conditions
        else:
            # Sell signals:
            # 1. Death cross (20 MA crosses below 50 MA)
            # 2. Price falls below 200-day MA
            # 3. Momentum turns negative
            
            sell_score = 0.0
            reasons = []
            
            if indicators["death_cross"]:
                sell_score += 0.5
                reasons.append("Death Cross")
            
            if indicators["current_price"] < indicators["ma_200"]:
                sell_score += 0.3
                reasons.append("Below 200-MA")
            
            if indicators["momentum"] < -5:  # Negative momentum
                sell_score += 0.2
                reasons.append(f"{indicators['momentum']:.1f}% momentum")
            
            # Check stop loss (-10% from avg price)
            current_price = Decimal(str(indicators["current_price"]))
            stop_loss_price = position.avg_price * Decimal("0.90")
            
            if current_price < stop_loss_price:
                sell_score = 1.0
                reasons.append(f"Stop loss hit ({-10:.1f}%)")
            
            # Exit if sell score is significant
            if sell_score >= 0.5:
                confidence = min(sell_score, 1.0)
                
                return Signal(
                    ticker=ticker,
                    action=SignalAction.SELL,
                    quantity=position.quantity,
                    confidence=confidence,
                    reasoning=", ".join(reasons),
                    metadata={
                        "sell_score": sell_score,
                        "momentum": indicators["momentum"],
                        "price_vs_200ma": indicators["current_price"] / indicators["ma_200"],
                    },
                )
        
        return None
    
    @staticmethod
    def _moving_average(prices: np.ndarray, window: int) -> np.ndarray:
        """Calculate simple moving average."""
        if len(prices) < window:
            return np.array([])
        
        # Use pandas for efficient rolling calculation
        series = pd.Series(prices)
        ma = series.rolling(window=window).mean()
        return ma.values
