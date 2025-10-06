"""
Value Moat Strategy - Quality companies at reasonable prices.

Inspired by Warren Buffett's investment philosophy:
- High-quality business (strong ROE, consistent growth)
- Durable competitive advantage (moat)
- Reasonable valuation (not overpaying)

Scoring methodology:
- Quality Score (50%): ROE, revenue growth, profitability
- Valuation Score (50%): P/E ratio relative to growth
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from quant_lab.models.market_data import MarketData, Fundamentals
from quant_lab.models.signal import Signal, SignalAction
from quant_lab.portfolio.portfolio import Portfolio
from quant_lab.strategies.protocols import StrategyConfig


class ValueMoatConfig(StrategyConfig):
    """Configuration for Value Moat strategy."""
    
    def __init__(
        self,
        min_roe: float = 0.15,           # Minimum 15% ROE
        min_revenue_growth: float = 0.10, # Minimum 10% revenue growth
        max_pe: float = 30.0,            # Maximum P/E ratio
        quality_weight: float = 0.5,     # 50% weight on quality
        valuation_weight: float = 0.5,   # 50% weight on valuation
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.min_roe = min_roe
        self.min_revenue_growth = min_revenue_growth
        self.max_pe = max_pe
        self.quality_weight = quality_weight
        self.valuation_weight = valuation_weight


class ValueMoatStrategy:
    """
    Value Moat Strategy - Buy quality businesses at fair prices.
    
    Entry criteria:
    - ROE >= 15% (profitable use of equity)
    - Revenue growth >= 10% (growing business)
    - P/E ratio reasonable (not overvalued)
    - Combined score >= 0.6
    
    Exit criteria:
    - Combined score < 0.4 (fundamentals deteriorated)
    - Better opportunities available
    """
    
    name = "Value Moat"
    description = "Quality companies with competitive advantages at reasonable valuations"
    
    def __init__(self, config: Optional[ValueMoatConfig] = None):
        self.config = config or ValueMoatConfig()
    
    def generate_signals(
        self,
        market_data: MarketData,
        portfolio: Portfolio,
        current_date: date,
    ) -> list[Signal]:
        """Generate signals based on quality and valuation scores."""
        signals = []
        
        # Get latest prices
        latest_prices = self._get_latest_prices(market_data, current_date)
        
        for ticker in market_data.tickers:
            fundamentals = market_data.get_fundamentals(ticker)
            
            if not fundamentals or ticker not in latest_prices:
                continue
            
            # Calculate scores
            quality_score = self._calculate_quality_score(fundamentals)
            valuation_score = self._calculate_valuation_score(fundamentals)
            
            # Combined score
            combined_score = (
                quality_score * self.config.quality_weight +
                valuation_score * self.config.valuation_weight
            )
            
            # Generate signal
            signal = self._generate_signal_for_ticker(
                ticker=ticker,
                combined_score=combined_score,
                quality_score=quality_score,
                valuation_score=valuation_score,
                portfolio=portfolio,
                current_price=latest_prices[ticker],
            )
            
            if signal:
                signals.append(signal)
        
        return signals
    
    def _calculate_quality_score(self, fundamentals: Fundamentals) -> float:
        """
        Calculate quality score (0.0 to 1.0).
        
        Components:
        - ROE (40%): Return on equity
        - Revenue Growth (30%): Year-over-year growth
        - Profitability (30%): Net income margin
        """
        scores = []
        weights = []
        
        # ROE component (normalized to 0-1 scale, 15% ROE = 0.5)
        if fundamentals.roe is not None:
            roe_score = min(fundamentals.roe / 0.30, 1.0)  # Cap at 30% ROE
            scores.append(roe_score)
            weights.append(0.4)
        
        # Revenue growth component (10% growth = 0.5)
        if fundamentals.revenue_growth is not None:
            growth_score = min(fundamentals.revenue_growth / 0.20, 1.0)  # Cap at 20%
            scores.append(growth_score)
            weights.append(0.3)
        
        # Profitability component (net margin)
        if fundamentals.revenue and fundamentals.net_income:
            if fundamentals.revenue > 0:
                net_margin = float(fundamentals.net_income / fundamentals.revenue)
                margin_score = min(net_margin / 0.20, 1.0)  # Cap at 20% margin
                scores.append(margin_score)
                weights.append(0.3)
        
        if not scores:
            return 0.0
        
        # Weighted average
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _calculate_valuation_score(self, fundamentals: Fundamentals) -> float:
        """
        Calculate valuation score (0.0 to 1.0).
        
        Uses PEG-like ratio: P/E relative to growth rate.
        Lower P/E with higher growth = better score.
        """
        if fundamentals.pe_ratio is None or fundamentals.revenue_growth is None:
            return 0.5  # Neutral if data missing
        
        # Avoid division by zero
        if fundamentals.revenue_growth <= 0:
            return 0.0  # No growth or negative growth
        
        # PEG ratio = P/E / (Growth Rate * 100)
        # PEG < 1.0 is attractive, PEG > 2.0 is expensive
        peg_ratio = fundamentals.pe_ratio / (fundamentals.revenue_growth * 100)
        
        if peg_ratio < 1.0:
            return 1.0  # Excellent value
        elif peg_ratio < 1.5:
            return 0.75  # Good value
        elif peg_ratio < 2.0:
            return 0.5   # Fair value
        else:
            return 0.25  # Expensive
    
    def _generate_signal_for_ticker(
        self,
        ticker: str,
        combined_score: float,
        quality_score: float,
        valuation_score: float,
        portfolio: Portfolio,
        current_price: Decimal,
    ) -> Optional[Signal]:
        """Generate buy/sell/hold signal for a ticker."""
        position = portfolio.get_position(ticker)
        
        # Entry criteria: high score, no existing position
        if combined_score >= 0.6 and position is None:
            # Calculate position size based on confidence
            confidence = combined_score
            target_value = portfolio.total_value * Decimal(str(self.config.max_position_size))
            quantity = int(target_value / current_price)
            
            if quantity > 0:
                return Signal(
                    ticker=ticker,
                    action=SignalAction.BUY,
                    quantity=Decimal(str(quantity)),
                    confidence=confidence,
                    reasoning=f"Quality Score: {quality_score:.2f}, Valuation Score: {valuation_score:.2f}",
                    metadata={
                        "quality_score": quality_score,
                        "valuation_score": valuation_score,
                        "combined_score": combined_score,
                    },
                )
        
        # Exit criteria: score deteriorated significantly
        elif combined_score < 0.4 and position is not None:
            return Signal(
                ticker=ticker,
                action=SignalAction.SELL,
                quantity=position.quantity,
                confidence=1.0 - combined_score,  # Higher confidence to sell if score is low
                reasoning=f"Score dropped to {combined_score:.2f} (Quality: {quality_score:.2f}, Valuation: {valuation_score:.2f})",
                metadata={
                    "quality_score": quality_score,
                    "valuation_score": valuation_score,
                    "combined_score": combined_score,
                },
            )
        
        # Hold otherwise
        return None
    
    def _get_latest_prices(
        self,
        market_data: MarketData,
        current_date: date,
    ) -> dict[str, Decimal]:
        """Get latest available price for each ticker."""
        latest_prices = {}
        
        for ticker in market_data.tickers:
            ticker_prices = market_data.get_prices(ticker)
            ticker_prices = ticker_prices[ticker_prices["date"] <= current_date]
            
            if not ticker_prices.empty:
                latest_row = ticker_prices.iloc[-1]
                latest_prices[ticker] = latest_row["close"]
        
        return latest_prices
