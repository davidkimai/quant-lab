"""
Trade models for portfolio transactions.

A Trade represents an executed transaction, including fees and slippage.
Trades are created from Signals and applied to Portfolio positions.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class TradeAction(str, Enum):
    """Trade action types."""
    
    BUY = "buy"          # Open long position
    SELL = "sell"        # Close long position
    SHORT = "short"      # Open short position
    COVER = "cover"      # Close short position


class Trade(BaseModel):
    """
    Executed trade transaction.
    
    Attributes:
        ticker: Stock symbol
        action: Trade action (buy/sell/short/cover)
        quantity: Number of shares
        price: Execution price per share
        fees: Transaction fees (commission + exchange fees)
        slippage: Price impact cost
        timestamp: Execution timestamp
        metadata: Additional trade-related data
    """
    
    ticker: str = Field(..., min_length=1, max_length=10)
    action: TradeAction
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    fees: Decimal = Field(default=Decimal("0"), ge=0)
    slippage: Decimal = Field(default=Decimal("0"), ge=0)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, float | str | int] = Field(default_factory=dict)
    
    @field_validator("ticker")
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Normalize ticker to uppercase."""
        return v.upper().strip()
    
    @field_validator("quantity", "price", "fees", "slippage", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | int | Decimal) -> Decimal:
        """Convert numeric values to Decimal for precision."""
        return Decimal(str(v)) if not isinstance(v, Decimal) else v
    
    @property
    def gross_value(self) -> Decimal:
        """Gross value of trade (quantity × price)."""
        return self.quantity * self.price
    
    @property
    def total_cost(self) -> Decimal:
        """Total cost including fees and slippage."""
        return self.gross_value + self.fees + self.slippage
    
    @property
    def is_opening(self) -> bool:
        """Check if trade opens a new position."""
        return self.action in (TradeAction.BUY, TradeAction.SHORT)
    
    @property
    def is_closing(self) -> bool:
        """Check if trade closes an existing position."""
        return self.action in (TradeAction.SELL, TradeAction.COVER)
    
    def effective_price(self) -> Decimal:
        """
        Effective price per share including fees and slippage.
        
        For buys/shorts: price is increased by costs
        For sells/covers: price is decreased by costs
        """
        cost_per_share = (self.fees + self.slippage) / self.quantity
        
        if self.is_opening:
            return self.price + cost_per_share
        else:  # Closing
            return self.price - cost_per_share
    
    class Config:
        frozen = True  # Immutable
        use_enum_values = True


class TradeBuilder:
    """
    Builder for creating Trade instances with automatic fee calculation.
    
    Usage:
        trade = (TradeBuilder("AAPL", TradeAction.BUY, 100, Decimal("150.00"))
                 .with_commission_bps(5)  # 5 basis points
                 .with_slippage_bps(2)     # 2 basis points
                 .build())
    """
    
    def __init__(
        self,
        ticker: str,
        action: TradeAction,
        quantity: Decimal | int | float,
        price: Decimal | int | float,
    ):
        self.ticker = ticker
        self.action = action
        self.quantity = Decimal(str(quantity))
        self.price = Decimal(str(price))
        self.fees = Decimal("0")
        self.slippage = Decimal("0")
        self.metadata: dict[str, float | str | int] = {}
    
    def with_commission(self, commission: Decimal | float) -> "TradeBuilder":
        """Add flat commission fee."""
        self.fees += Decimal(str(commission))
        return self
    
    def with_commission_bps(self, bps: float) -> "TradeBuilder":
        """Add commission as basis points of trade value (1 bps = 0.01%)."""
        gross_value = self.quantity * self.price
        commission = gross_value * Decimal(str(bps)) / Decimal("10000")
        self.fees += commission
        return self
    
    def with_slippage_bps(self, bps: float) -> "TradeBuilder":
        """Add slippage as basis points of trade value."""
        gross_value = self.quantity * self.price
        slippage = gross_value * Decimal(str(bps)) / Decimal("10000")
        self.slippage += slippage
        return self
    
    def with_metadata(self, key: str, value: float | str | int) -> "TradeBuilder":
        """Add metadata to trade."""
        self.metadata[key] = value
        return self
    
    def build(self) -> Trade:
        """Build the Trade instance."""
        return Trade(
            ticker=self.ticker,
            action=self.action,
            quantity=self.quantity,
            price=self.price,
            fees=self.fees,
            slippage=self.slippage,
            metadata=self.metadata,
        )
