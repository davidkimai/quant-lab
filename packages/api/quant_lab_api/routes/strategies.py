"""
Strategy API routes.

Endpoints:
- GET /api/strategies - List all available strategies
"""

from fastapi import APIRouter
from pydantic import BaseModel

from quant_lab_api.services.backtest_service import BacktestService


router = APIRouter(prefix="/api/strategies", tags=["strategies"])


class StrategyInfo(BaseModel):
    """Strategy metadata."""
    
    id: str
    name: str
    description: str


@router.get("", response_model=list[StrategyInfo])
def list_strategies() -> list[StrategyInfo]:
    """
    List all available trading strategies.
    
    Returns strategy metadata including:
    - id: Unique identifier for API requests
    - name: Human-readable name
    - description: Strategy description
    """
    service = BacktestService()
    strategies = service.get_available_strategies()
    
    return [
        StrategyInfo(
            id=s["id"],
            name=s["name"],
            description=s["description"],
        )
        for s in strategies
    ]
