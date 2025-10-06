"""
Backtest API routes with Server-Sent Events (SSE) streaming.

Endpoints:
- POST /api/backtest/run - Run backtest with SSE progress updates
- GET /api/backtest/{id} - Get backtest results by ID
- GET /api/backtest - List all backtests
- DELETE /api/backtest/{id} - Delete a backtest
"""

from typing import AsyncGenerator
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from quant_lab_api.database.base import get_db
from quant_lab_api.repositories.backtest_repository import BacktestRepository
from quant_lab_api.services.backtest_service import BacktestService
import json
import asyncio


router = APIRouter(prefix="/api/backtest", tags=["backtest"])


# Request/Response schemas
class BacktestRequest(BaseModel):
    """Request schema for running a backtest."""
    
    strategy_name: str = Field(..., description="Strategy to use (value_moat, trend_following, multi_factor)")
    tickers: list[str] = Field(..., min_length=1, description="List of stock symbols")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(default=100000.0, gt=0, description="Starting capital")
    commission_bps: float = Field(default=5.0, ge=0, description="Commission in basis points")
    slippage_bps: float = Field(default=2.0, ge=0, description="Slippage in basis points")
    rebalance_frequency: int = Field(default=5, gt=0, description="Days between rebalances")


class BacktestResponse(BaseModel):
    """Response schema for backtest results."""
    
    id: int
    strategy_name: str
    created_at: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    sharpe_ratio: float | None
    num_trades: int


@router.post("/run")
async def run_backtest_streaming(
    request: BacktestRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Run a backtest with SSE progress streaming.
    
    Returns a stream of Server-Sent Events with progress updates:
    - stage: loading_data, initializing, running, computing_metrics, complete
    - progress: 0.0 to 1.0
    - message: Human-readable status message
    - results: Final results (only in 'complete' event)
    """
    
    service = BacktestService()
    repository = BacktestRepository(db)
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for backtest progress."""
        
        try:
            # Parse dates
            start_date = date.fromisoformat(request.start_date)
            end_date = date.fromisoformat(request.end_date)
            
            # Progress callback for SSE
            async def send_progress(data: dict) -> None:
                """Send progress event to client."""
                event = f"data: {json.dumps(data)}\n\n"
                yield event
            
            # Create generator for progress updates
            progress_queue: asyncio.Queue = asyncio.Queue()
            
            async def progress_callback(data: dict) -> None:
                await progress_queue.put(data)
            
            # Start backtest in background task
            async def run_backtest_task() -> None:
                try:
                    results = await service.run_backtest(
                        strategy_name=request.strategy_name,
                        tickers=request.tickers,
                        start_date=start_date,
                        end_date=end_date,
                        initial_capital=request.initial_capital,
                        commission_bps=request.commission_bps,
                        slippage_bps=request.slippage_bps,
                        rebalance_frequency=request.rebalance_frequency,
                        progress_callback=progress_callback,
                    )
                    
                    # Save results to database
                    repository.create(
                        strategy_name=results["strategy_name"],
                        start_date=results["start_date"],
                        end_date=results["end_date"],
                        duration_days=results["duration_days"],
                        initial_capital=results["initial_capital"],
                        tickers=results["tickers"],
                        final_value=results["final_value"],
                        total_return=results["metrics"]["total_return"],
                        annualized_return=results["metrics"]["annualized_return"],
                        metrics=results["metrics"],
                        equity_curve=results["equity_curve"],
                        trade_history=results["trade_history"],
                    )
                    
                    await progress_queue.put(None)  # Signal completion
                
                except Exception as e:
                    await progress_queue.put({"error": str(e)})
                    await progress_queue.put(None)
            
            # Start backtest task
            task = asyncio.create_task(run_backtest_task())
            
            # Stream progress events
            while True:
                data = await progress_queue.get()
                
                if data is None:
                    break
                
                if "error" in data:
                    yield f"event: error\ndata: {json.dumps({'error': data['error']})}\n\n"
                    break
                
                yield f"data: {json.dumps(data)}\n\n"
            
            await task  # Ensure task completes
        
        except ValueError as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': f'Internal error: {str(e)}'})} \n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        },
    )


@router.get("/{backtest_id}")
def get_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Get backtest results by ID."""
    
    repository = BacktestRepository(db)
    backtest = repository.get_by_id(backtest_id)
    
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return {
        "id": backtest.id,
        "strategy_name": backtest.strategy_name,
        "created_at": backtest.created_at.isoformat(),
        "start_date": backtest.start_date,
        "end_date": backtest.end_date,
        "duration_days": backtest.duration_days,
        "initial_capital": backtest.initial_capital,
        "final_value": backtest.final_value,
        "metrics": backtest.metrics,
        "equity_curve": backtest.equity_curve,
        "trade_history": backtest.trade_history,
        "tickers": backtest.tickers,
        "status": backtest.status,
    }


@router.get("")
def list_backtests(
    skip: int = 0,
    limit: int = 20,
    strategy_name: str | None = None,
    db: Session = Depends(get_db),
) -> list[BacktestResponse]:
    """List all backtests with pagination."""
    
    repository = BacktestRepository(db)
    backtests = repository.get_all(skip=skip, limit=limit, strategy_name=strategy_name)
    
    return [
        BacktestResponse(
            id=b.id,
            strategy_name=b.strategy_name,
            created_at=b.created_at.isoformat(),
            start_date=b.start_date,
            end_date=b.end_date,
            initial_capital=b.initial_capital,
            final_value=b.final_value,
            total_return=b.total_return,
            sharpe_ratio=b.sharpe_ratio,
            num_trades=b.num_trades,
        )
        for b in backtests
    ]


@router.delete("/{backtest_id}")
def delete_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a backtest."""
    
    repository = BacktestRepository(db)
    deleted = repository.delete(backtest_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return {"message": "Backtest deleted successfully"}
