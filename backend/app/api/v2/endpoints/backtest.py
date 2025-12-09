"""
Backtest API Endpoints - запуск и просмотр backtest результатов
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.backtest_result import BacktestResult
from app.services.backtest_service import BacktestEngine
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== SCHEMAS ====================

class BacktestRequest(BaseModel):
    """Request для запуска backtest"""
    start_time: Optional[datetime] = None  # If None, use last 1 hour
    end_time: Optional[datetime] = None    # If None, use now
    symbols: List[str] = ["BTCUSDT", "ETHUSDT"]
    exchanges: List[str] = ["binance", "bybit"]


class BacktestResponse(BaseModel):
    """Response с результатами backtest"""
    id: int
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    
    symbols: List[str]
    exchanges: List[str]
    
    # Strategy params
    min_spread_bps: float
    fee_bps: float
    slippage_bps: float
    
    # Results
    total_opportunities: int
    opportunities_per_minute: float
    
    avg_spread_bps: Optional[float]
    min_spread_bps_found: Optional[float]
    max_spread_bps_found: Optional[float]
    median_spread_bps: Optional[float]
    
    total_potential_profit_usd: float
    avg_profit_per_trade_usd: Optional[float]
    best_trade_profit_usd: Optional[float]
    
    symbol_stats: Optional[dict]
    
    completed: bool
    error_message: Optional[str]
    recommendation: Optional[str]
    created_at: datetime
    
    class Config:
        orm_mode = True


# ==================== ENDPOINTS ====================

@router.post("/run", response_model=BacktestResponse)
def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🔄 Запустить backtest на исторических данных
    
    Анализирует orderbook snapshots и ищет arbitrage opportunities
    """
    try:
        # Default time range: last 1 hour
        if request.start_time is None:
            request.start_time = datetime.utcnow() - timedelta(hours=1)
        if request.end_time is None:
            request.end_time = datetime.utcnow()
        
        # Validate time range
        if request.start_time >= request.end_time:
            raise HTTPException(status_code=400, detail="start_time must be before end_time")
        
        # Run backtest
        engine = BacktestEngine(db)
        result = engine.run_backtest(
            start_time=request.start_time,
            end_time=request.end_time,
            symbols=request.symbols,
            exchanges=request.exchanges
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results", response_model=List[BacktestResponse])
def get_backtest_results(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 Получить список последних backtest результатов
    """
    results = db.query(BacktestResult).order_by(
        BacktestResult.created_at.desc()
    ).limit(limit).all()
    
    return results


@router.get("/results/{backtest_id}", response_model=BacktestResponse)
def get_backtest_result(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📈 Получить результат конкретного backtest по ID
    """
    result = db.query(BacktestResult).filter(BacktestResult.id == backtest_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return result


@router.delete("/results/{backtest_id}")
def delete_backtest_result(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🗑️  Удалить backtest result
    """
    result = db.query(BacktestResult).filter(BacktestResult.id == backtest_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    db.delete(result)
    db.commit()
    
    return {"message": "Backtest result deleted"}
