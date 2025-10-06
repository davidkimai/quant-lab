"""
Multi-Factor Strategy - Combine multiple signals.

Integrates value, momentum, and quality factors into a unified scoring system.
This hybrid approach aims to capture different return drivers:
- Value: Buy undervalued assets
- Momentum: Ride existing trends
- Quality: Focus on strong businesses

Academic foundation: Fama-French factors + momentum (Carhart 4-factor model)
"""

from datetime import date
from decimal import Decimal
from typing import Optional
import pandas as pd
import numpy as np

from quant_lab.models.market_data import MarketData, Fundamentals
from quant_lab.models.signal import Signal, SignalAction
from quant_lab.portfolio.portfolio import Portfolio
from quant_lab.strategies.protocols import StrategyConfig


class MultiFactorConfig(StrategyConfig):
    """Configuration for Multi-Factor strategy."""
    
    def __init__(
        self,
        value_weight: float = 0.35,      # 35% weight on value
        momentum_weight: float = 0.35,   # 35% weight on momentum
        quality_weight: float = 0.30,    # 30% weight on quality
        momentum_window: int = 90,       # 90-day momentum
        entry_threshold: float = 0.65,   # Enter when score >= 0.65
        exit_threshold: float = 0.35,    # Exit when score < 0.35
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.value_weight = value_weight
        self.momentum_weight = momentum_weight
        self.quality_weight = quality_weight
        self.momentum_window = momentum_window
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold


class MultiFactorStrategy:
    """
    Multi-Factor Strategy - Systematic factor investing.
    
    Factor definitions:
    - Value: P/E ratio, P/B ratio relative to peers
    - Momentum: Price performance over 90 days
    - Quality: ROE, profit margins, debt levels
    
    Signals:
    - BUY when combined score >= 0.65
    - SELL when combined score < 0.35
    - Rebalance positions based on relative scores
    """
    
    name = "Multi-Factor"
    description = "Systematic strategy combining value, momentum, and quality factors"
    
    def __init__(self, config: Optional[MultiFactorConfig] = None):
        self.config = config or MultiFactorConfig()
    
    def generate_signals(
        self,
        market_data: MarketData,
        portfolio: Portfolio,
        current_date: date,
    ) -> list[Signal]:
        """Generate signals based on multi-factor scores."""
        # Calculate scores for all tickers
        ticker_scores = {}
        
        for ticker in market_data.tickers:
            score_data = self._calculate_scores(
                ticker=ticker,
                market_data=market_data,
                current_date=current_date,
            )
            
            if score_data:
                ticker_scores[ticker] = score_data
        
        if not ticker_scores:
            return []
        
        # Rank tickers by combined score
        ranked_tickers = sorted(
            ticker_scores.items(),
            key=lambda x: x[1]["combined_score"],
            reverse=True,
        )
        
        # Generate signals
        signals = []
        
        for ticker, scores in ranked_tickers:
            signal = self._generate_signal_for_ticker(
                ticker=ticker,
                scores=scores,
                portfolio=portfolio,
                current_price=scores["current_price"],
            )
            
            if signal:
                signals.append(signal)
        
        return signals
    
    def _calculate_scores(
        self,
        ticker: str,
        market_data: MarketData,
        current_date: date,
    ) -> Optional[dict]:
        """Calculate value, momentum, and quality scores."""
        # Get price data
        prices_df = market_data.get_prices(ticker)
        prices_df = prices_df[prices_df["date"] <= current_date]
        
        if prices_df.empty:
            return None
        
        current_price = float(prices_df.iloc[-1]["close"])
        
        # Get fundamentals
        fundamentals = market_data.get_fundamentals(ticker)
        
        # Calculate individual factor scores
        value_score = self._calculate_value_score(fundamentals)
        momentum_score = self._calculate_momentum_score(prices_df)
        quality_score = self._calculate_quality_score(fundamentals)
        
        # Combined score
        combined_score = (
            value_score * self.config.value_weight +
            momentum_score * self.config.momentum_weight +
            quality_score * self.config.quality_weight
        )
        
        return {
            "value_score": value_score,
            "momentum_score": momentum_score,
            "quality_score": quality_score,
            "combined_score": combined_score,
            "current_price": current_price,
        }
    
    def _calculate_value_score(self, fundamentals: Optional[Fundamentals]) -> float:
        """
        Calculate value score (0.0 to 1.0).
        
        Lower valuation = higher score.
        Components:
        - P/E ratio (lower is better)
        - P/B ratio if available
        """
        if not fundamentals:
            return 0.5  # Neutral if no data
        
        scores = []
        
        # P/E component (inverted - lower is better)
        if fundamentals.pe_ratio is not None and fundamentals.pe_ratio > 0:
            # P/E of 15 = 0.5, P/E of 10 = 0.75, P/E of 20 = 0.25
            pe_score = max(0, 1.0 - (fundamentals.pe_ratio / 30.0))
            scores.append(pe_score)
        
        # Earnings yield component
        if fundamentals.pe_ratio is not None and fundamentals.pe_ratio > 0:
            earnings_yield = 1.0 / fundamentals.pe_ratio
            # Normalize: 10% yield = 1.0, 5% = 0.5
            yield_score = min(earnings_yield / 0.10, 1.0)
            scores.append(yield_score)
        
        if not scores:
            return 0.5
        
        return sum(scores) / len(scores)
    
    def _calculate_momentum_score(self, prices_df: pd.DataFrame) -> float:
        """
        Calculate momentum score (0.0 to 1.0).
        
        Higher recent returns = higher score.
        """
        if len(prices_df) < self.config.momentum_window:
            return 0.5  # Neutral if insufficient data
        
        # Calculate return over momentum window
        recent_prices = prices_df.tail(self.config.momentum_window)
        start_price = float(recent_prices.iloc[0]["close"])
        end_price = float(recent_prices.iloc[-1]["close"])
        
        momentum_return = (end_price / start_price - 1.0) * 100  # Percentage
        
        # Normalize: +20% = 1.0, 0% = 0.5, -20% = 0.0
        normalized_score = 0.5 + (momentum_return / 40.0)
        
        return max(0.0, min(1.0, normalized_score))
    
    def _calculate_quality_score(self, fundamentals: Optional[Fundamentals]) -> float:
        """
        Calculate quality score (0.0 to 1.0).
        
        Components:
        - ROE (return on equity)
        - Debt-to-equity (lower is better)
        - Current ratio (liquidity)
        """
        if not fundamentals:
            return 0.5  # Neutral if no data
        
        scores = []
        weights = []
        
        # ROE component
        if fundamentals.roe is not None:
            roe_score = min(fundamentals.roe / 0.25, 1.0)  # 25% ROE = max
            scores.append(roe_score)
            weights.append(0.5)
        
        # Debt-to-equity component (inverted - lower is better)
        if fundamentals.debt_to_equity is not None:
            # D/E of 0.5 = 0.75, D/E of 1.0 = 0.5, D/E of 2.0 = 0.0
            de_score = max(0, 1.0 - (fundamentals.debt_to_equity / 2.0))
            scores.append(de_score)
            weights.append(0.3)
        
        # Current ratio component (liquidity)
        if fundamentals.current_ratio is not None:
            # Current ratio > 2.0 = 1.0, 1.0 = 0.5, < 1.0 = 0.0
            cr_score = min(fundamentals.current_ratio / 2.0, 1.0)
            scores.append(cr_score)
            weights.append(0.2)
        
        if not scores:
            return 0.5
        
        # Weighted average
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def _generate_signal_for_ticker(
        self,
        ticker: str,
        scores: dict,
        portfolio: Portfolio,
        current_price: float,
    ) -> Optional[Signal]:
        """Generate buy/sell signal based on multi-factor scores."""
        position = portfolio.get_position(ticker)
        combined_score = scores["combined_score"]
        
        # Entry: high combined score, no position
        if combined_score >= self.config.entry_threshold and position is None:
            confidence = combined_score
            target_value = portfolio.total_value * Decimal(str(self.config.max_position_size))
            quantity = int(target_value / Decimal(str(current_price)))
            
            if quantity > 0:
                return Signal(
                    ticker=ticker,
                    action=SignalAction.BUY,
                    quantity=Decimal(str(quantity)),
                    confidence=confidence,
                    reasoning=self._format_reasoning(scores),
                    metadata=scores,
                )
        
        # Exit: low combined score, have position
        elif combined_score < self.config.exit_threshold and position is not None:
            confidence = 1.0 - combined_score  # Low score = high confidence to sell
            
            return Signal(
                ticker=ticker,
                action=SignalAction.SELL,
                quantity=position.quantity,
                confidence=confidence,
                reasoning=f"Score dropped to {combined_score:.2f}. {self._format_reasoning(scores)}",
                metadata=scores,
            )
        
        return None
    
    @staticmethod
    def _format_reasoning(scores: dict) -> str:
        """Format score breakdown for reasoning field."""
        return (
            f"Value: {scores['value_score']:.2f}, "
            f"Momentum: {scores['momentum_score']:.2f}, "
            f"Quality: {scores['quality_score']:.2f}"
        )
