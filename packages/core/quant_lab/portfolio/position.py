"""
Position models for portfolio holdings.

A Position represents ownership (long) or obligation (short) of shares,
including the quantity, average cost basis, and current market value.
"""

from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class PositionSide(str, Enum):
    """Side of a position."""
    
    LONG = "long"
    SHORT = "short"


class Position(BaseModel):
    """
    A position in a single security.
    
    Attributes:
        ticker: Stock symbol
        side: Long (own shares) or short (borrowed shares)
        quantity: Number of shares
        avg_price: Average cost basis per share
        current_price: Current market price per share
    """
    
    ticker: str = Field(..., min_length=1, max_length=10)
    side: PositionSide
    quantity: Decimal = Field(gt=0)
    avg_price: Decimal = Field(gt=0)
    current_price: Decimal = Field(default=Decimal("0"), ge=0)
    
    @field_validator("ticker")
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Normalize ticker to uppercase."""
        return v.upper().strip()
    
    @field_validator("quantity", "avg_price", "current_price", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | int | Decimal) -> Decimal:
        """Convert numeric values to Decimal for precision."""
        return Decimal(str(v)) if not isinstance(v, Decimal) else v
    
    @property
    def cost_basis(self) -> Decimal:
        """Total cost basis (quantity × avg_price)."""
        return self.quantity * self.avg_price
    
    @property
    def market_value(self) -> Decimal:
        """Current market value (quantity × current_price)."""
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> Decimal:
        """
        Unrealized profit/loss.
        
        For long positions: (current_price - avg_price) × quantity
        For short positions: (avg_price - current_price) × quantity
        """
        if self.side == PositionSide.LONG:
            return (self.current_price - self.avg_price) * self.quantity
        else:  # SHORT
            return (self.avg_price - self.current_price) * self.quantity
    
    @property
    def return_pct(self) -> float:
        """Return percentage based on cost basis."""
        if self.avg_price == 0:
            return 0.0
        return float(self.unrealized_pnl / self.cost_basis)
    
    def update_price(self, new_price: Decimal) -> "Position":
        """Return new Position with updated current price."""
        return self.model_copy(update={"current_price": new_price})
    
    def add_shares(self, quantity: Decimal, price: Decimal) -> "Position":
        """
        Add shares to position (for longs) or increase short position.
        
        Recalculates average price using weighted average method.
        """
        new_quantity = self.quantity + quantity
        new_avg_price = (
            (self.quantity * self.avg_price + quantity * price) / new_quantity
        )
        
        return Position(
            ticker=self.ticker,
            side=self.side,
            quantity=new_quantity,
            avg_price=new_avg_price,
            current_price=self.current_price,
        )
    
    def remove_shares(self, quantity: Decimal) -> tuple[Optional["Position"], Decimal]:
        """
        Remove shares from position.
        
        Returns:
            - New Position if shares remain (None if fully closed)
            - Realized P&L from the sale
        """
        if quantity > self.quantity:
            raise ValueError(f"Cannot remove {quantity} shares from position of {self.quantity}")
        
        # Calculate realized P&L
        if self.side == PositionSide.LONG:
            realized_pnl = (self.current_price - self.avg_price) * quantity
        else:  # SHORT
            realized_pnl = (self.avg_price - self.current_price) * quantity
        
        # Check if position is fully closed
        remaining = self.quantity - quantity
        if remaining == 0:
            return None, realized_pnl
        
        # Return new position with reduced quantity (same avg_price)
        new_position = Position(
            ticker=self.ticker,
            side=self.side,
            quantity=remaining,
            avg_price=self.avg_price,
            current_price=self.current_price,
        )
        
        return new_position, realized_pnl
    
    class Config:
        frozen = True  # Immutable
        use_enum_values = True


from typing import Optional  # Move import to top in actual implementation
