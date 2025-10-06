"""
Portfolio management with immutable state and pure functions.

The Portfolio class tracks cash, positions, and realized P&L.
All operations return new Portfolio instances (immutability).
"""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from quant_lab.portfolio.position import Position, PositionSide
from quant_lab.portfolio.trade import Trade, TradeAction


class Portfolio(BaseModel):
    """
    Immutable portfolio state.
    
    Attributes:
        cash: Available cash for trading
        positions: Dictionary of open positions {ticker: Position}
        realized_pnl: Cumulative realized profit/loss
        initial_capital: Starting capital (for return calculation)
    """
    
    cash: Decimal = Field(gt=0)
    positions: dict[str, Position] = Field(default_factory=dict)
    realized_pnl: Decimal = Field(default=Decimal("0"))
    initial_capital: Decimal = Field(gt=0)
    
    @field_validator("cash", "realized_pnl", "initial_capital", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | int | Decimal) -> Decimal:
        """Convert numeric values to Decimal for precision."""
        return Decimal(str(v)) if not isinstance(v, Decimal) else v
    
    @classmethod
    def create(cls, initial_capital: Decimal | float | int) -> "Portfolio":
        """Create a new portfolio with initial capital."""
        capital = Decimal(str(initial_capital))
        return cls(cash=capital, initial_capital=capital)
    
    @property
    def total_value(self) -> Decimal:
        """Total portfolio value (cash + market value of positions)."""
        positions_value = sum(
            pos.market_value for pos in self.positions.values()
        )
        return self.cash + positions_value
    
    @property
    def unrealized_pnl(self) -> Decimal:
        """Total unrealized profit/loss across all positions."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    @property
    def total_pnl(self) -> Decimal:
        """Total profit/loss (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def return_pct(self) -> float:
        """Total return percentage based on initial capital."""
        return float(self.total_pnl / self.initial_capital)
    
    @property
    def long_exposure(self) -> Decimal:
        """Market value of all long positions."""
        return sum(
            pos.market_value
            for pos in self.positions.values()
            if pos.side == PositionSide.LONG
        )
    
    @property
    def short_exposure(self) -> Decimal:
        """Market value of all short positions."""
        return sum(
            pos.market_value
            for pos in self.positions.values()
            if pos.side == PositionSide.SHORT
        )
    
    @property
    def net_exposure(self) -> Decimal:
        """Net exposure (long - short)."""
        return self.long_exposure - self.short_exposure
    
    @property
    def gross_exposure(self) -> Decimal:
        """Gross exposure (long + short)."""
        return self.long_exposure + self.short_exposure
    
    def get_position(self, ticker: str) -> Optional[Position]:
        """Get position for ticker (None if no position)."""
        return self.positions.get(ticker.upper())
    
    def update_prices(self, prices: dict[str, Decimal]) -> "Portfolio":
        """
        Update market prices for all positions.
        
        Args:
            prices: Dictionary mapping ticker to current price
        
        Returns:
            New Portfolio with updated position prices
        """
        updated_positions = {}
        
        for ticker, position in self.positions.items():
            if ticker in prices:
                updated_positions[ticker] = position.update_price(prices[ticker])
            else:
                updated_positions[ticker] = position
        
        return self.model_copy(update={"positions": updated_positions})
    
    def apply_trade(self, trade: Trade) -> "Portfolio":
        """
        Apply a trade to the portfolio.
        
        Returns:
            New Portfolio instance with updated state
        
        Raises:
            ValueError: If trade cannot be executed (insufficient cash/position)
        """
        ticker = trade.ticker.upper()
        
        if trade.action == TradeAction.BUY:
            return self._execute_buy(trade)
        elif trade.action == TradeAction.SELL:
            return self._execute_sell(trade)
        elif trade.action == TradeAction.SHORT:
            return self._execute_short(trade)
        elif trade.action == TradeAction.COVER:
            return self._execute_cover(trade)
        else:
            raise ValueError(f"Unknown trade action: {trade.action}")
    
    def _execute_buy(self, trade: Trade) -> "Portfolio":
        """Execute a buy order (open/increase long position)."""
        ticker = trade.ticker.upper()
        required_cash = trade.total_cost
        
        if required_cash > self.cash:
            raise ValueError(
                f"Insufficient cash for buy: need {required_cash}, have {self.cash}"
            )
        
        # Update cash
        new_cash = self.cash - required_cash
        
        # Update or create position
        new_positions = dict(self.positions)
        existing_position = self.get_position(ticker)
        
        if existing_position and existing_position.side == PositionSide.LONG:
            # Add to existing long position
            new_positions[ticker] = existing_position.add_shares(
                trade.quantity, trade.effective_price()
            )
        elif existing_position and existing_position.side == PositionSide.SHORT:
            raise ValueError(
                f"Cannot buy {ticker}: existing short position. Use COVER first."
            )
        else:
            # Create new long position
            new_positions[ticker] = Position(
                ticker=ticker,
                side=PositionSide.LONG,
                quantity=trade.quantity,
                avg_price=trade.effective_price(),
                current_price=trade.price,
            )
        
        return self.model_copy(update={"cash": new_cash, "positions": new_positions})
    
    def _execute_sell(self, trade: Trade) -> "Portfolio":
        """Execute a sell order (close/reduce long position)."""
        ticker = trade.ticker.upper()
        position = self.get_position(ticker)
        
        if not position or position.side != PositionSide.LONG:
            raise ValueError(f"No long position in {ticker} to sell")
        
        if trade.quantity > position.quantity:
            raise ValueError(
                f"Cannot sell {trade.quantity} shares: only have {position.quantity}"
            )
        
        # Update position and calculate realized P&L
        new_positions = dict(self.positions)
        remaining_position, realized_pnl = position.remove_shares(trade.quantity)
        
        if remaining_position:
            new_positions[ticker] = remaining_position.update_price(trade.price)
        else:
            del new_positions[ticker]
        
        # Update cash (receive proceeds from sale, minus costs)
        proceeds = trade.quantity * trade.price - trade.fees - trade.slippage
        new_cash = self.cash + proceeds
        new_realized_pnl = self.realized_pnl + realized_pnl
        
        return self.model_copy(
            update={
                "cash": new_cash,
                "positions": new_positions,
                "realized_pnl": new_realized_pnl,
            }
        )
    
    def _execute_short(self, trade: Trade) -> "Portfolio":
        """Execute a short order (open/increase short position)."""
        ticker = trade.ticker.upper()
        
        # Receive cash from short sale (we "borrow" shares and sell them)
        proceeds = trade.quantity * trade.price - trade.fees - trade.slippage
        new_cash = self.cash + proceeds
        
        # Update or create position
        new_positions = dict(self.positions)
        existing_position = self.get_position(ticker)
        
        if existing_position and existing_position.side == PositionSide.SHORT:
            # Add to existing short position
            new_positions[ticker] = existing_position.add_shares(
                trade.quantity, trade.effective_price()
            )
        elif existing_position and existing_position.side == PositionSide.LONG:
            raise ValueError(
                f"Cannot short {ticker}: existing long position. Use SELL first."
            )
        else:
            # Create new short position
            new_positions[ticker] = Position(
                ticker=ticker,
                side=PositionSide.SHORT,
                quantity=trade.quantity,
                avg_price=trade.effective_price(),
                current_price=trade.price,
            )
        
        return self.model_copy(update={"cash": new_cash, "positions": new_positions})
    
    def _execute_cover(self, trade: Trade) -> "Portfolio":
        """Execute a cover order (close/reduce short position)."""
        ticker = trade.ticker.upper()
        position = self.get_position(ticker)
        
        if not position or position.side != PositionSide.SHORT:
            raise ValueError(f"No short position in {ticker} to cover")
        
        if trade.quantity > position.quantity:
            raise ValueError(
                f"Cannot cover {trade.quantity} shares: only have {position.quantity}"
            )
        
        # Calculate cost to buy back shares
        cost_to_cover = trade.total_cost
        
        if cost_to_cover > self.cash:
            raise ValueError(
                f"Insufficient cash to cover: need {cost_to_cover}, have {self.cash}"
            )
        
        # Update position and calculate realized P&L
        new_positions = dict(self.positions)
        remaining_position, realized_pnl = position.remove_shares(trade.quantity)
        
        if remaining_position:
            new_positions[ticker] = remaining_position.update_price(trade.price)
        else:
            del new_positions[ticker]
        
        # Update cash (pay to buy back shares)
        new_cash = self.cash - cost_to_cover
        new_realized_pnl = self.realized_pnl + realized_pnl
        
        return self.model_copy(
            update={
                "cash": new_cash,
                "positions": new_positions,
                "realized_pnl": new_realized_pnl,
            }
        )
    
    def can_execute_trade(self, trade: Trade) -> tuple[bool, str]:
        """
        Check if trade can be executed without raising an exception.
        
        Returns:
            (can_execute, reason) - reason is empty string if executable
        """
        ticker = trade.ticker.upper()
        
        try:
            if trade.action == TradeAction.BUY:
                if trade.total_cost > self.cash:
                    return False, f"Insufficient cash: need {trade.total_cost}, have {self.cash}"
                
                position = self.get_position(ticker)
                if position and position.side == PositionSide.SHORT:
                    return False, f"Cannot buy: short position exists in {ticker}"
            
            elif trade.action == TradeAction.SELL:
                position = self.get_position(ticker)
                if not position or position.side != PositionSide.LONG:
                    return False, f"No long position in {ticker}"
                if trade.quantity > position.quantity:
                    return False, f"Insufficient shares: need {trade.quantity}, have {position.quantity}"
            
            elif trade.action == TradeAction.SHORT:
                position = self.get_position(ticker)
                if position and position.side == PositionSide.LONG:
                    return False, f"Cannot short: long position exists in {ticker}"
            
            elif trade.action == TradeAction.COVER:
                position = self.get_position(ticker)
                if not position or position.side != PositionSide.SHORT:
                    return False, f"No short position in {ticker}"
                if trade.quantity > position.quantity:
                    return False, f"Insufficient shares: need {trade.quantity}, have {position.quantity}"
                if trade.total_cost > self.cash:
                    return False, f"Insufficient cash to cover: need {trade.total_cost}, have {self.cash}"
            
            return True, ""
        
        except Exception as e:
            return False, str(e)
    
    class Config:
        frozen = True  # Immutable
        arbitrary_types_allowed = True
