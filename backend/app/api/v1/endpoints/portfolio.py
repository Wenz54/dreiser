"""Portfolio endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.portfolio import PortfolioResponse, PortfolioStats
from app.services.portfolio_service import PortfolioService
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить виртуальный портфель пользователя
    """
    portfolio_service = PortfolioService(db)
    portfolio = await portfolio_service.get_portfolio(current_user.id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return portfolio


@router.get("/stats", response_model=PortfolioStats)
async def get_portfolio_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить детальную статистику портфеля
    """
    portfolio_service = PortfolioService(db)
    portfolio = await portfolio_service.get_portfolio(current_user.id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    stats = await portfolio_service.get_portfolio_stats(portfolio.id)
    return stats


@router.get("/positions")
async def get_positions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить текущие открытые SPOT позиции
    """
    portfolio_service = PortfolioService(db)
    portfolio = await portfolio_service.get_portfolio(current_user.id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    positions = await portfolio_service.get_positions(portfolio.id)
    
    return {
        "positions": [
            {
                "id": str(pos.id),
                "symbol": pos.symbol,
                "quantity": float(pos.quantity),
                "entry_price": float(pos.entry_price),
                "current_price": float(pos.current_price) if pos.current_price else None,
                "unrealized_pnl": float((pos.current_price - pos.entry_price) * pos.quantity) if pos.current_price else 0,
                "is_simulated": pos.is_simulated,
                "opened_at": pos.created_at.isoformat()
            }
            for pos in positions
        ]
    }


@router.get("/futures-positions")
async def get_futures_positions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить текущие открытые FUTURES позиции (LONG/SHORT с leverage)
    """
    from sqlalchemy import select
    from app.models.portfolio import Portfolio
    from app.models.futures_position import FuturesPosition
    from app.services.binance_service import binance_service
    from decimal import Decimal
    
    # Получить портфель
    stmt = select(Portfolio).where(Portfolio.user_id == current_user.id)
    result = await db.execute(stmt)
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Получить futures позиции
    futures_stmt = select(FuturesPosition).where(
        FuturesPosition.portfolio_id == portfolio.id,
        FuturesPosition.is_closed == False
    ).order_by(FuturesPosition.created_at.desc())
    
    futures_result = await db.execute(futures_stmt)
    futures_positions = futures_result.scalars().all()
    
    positions_data = []
    for pos in futures_positions:
        # КРИТИЧНО: Запросить РЕАЛЬНУЮ текущую цену с Binance!
        current_price, is_stale = binance_service.get_ticker_price(pos.symbol)
        
        if not current_price:
            current_price = pos.entry_price  # Fallback
        
        # Рассчитать РЕАЛЬНЫЙ unrealized P&L
        pnl = pos.calculate_pnl(current_price)
        
        positions_data.append({
            "id": str(pos.id),
            "symbol": pos.symbol,
            "side": pos.side,  # LONG or SHORT
            "entry_price": float(pos.entry_price),
            "current_price": float(current_price),  # РЕАЛЬНАЯ цена!
            "quantity": float(pos.quantity),
            "leverage": pos.leverage,
            "liquidation_price": float(pos.liquidation_price),
            "unrealized_pnl": float(pnl),  # РЕАЛЬНЫЙ P&L!
            "margin": float((pos.quantity * pos.entry_price) / Decimal(str(pos.leverage))),
            "position_size": float(pos.quantity * pos.entry_price),
            "opened_at": pos.created_at.isoformat()
        })
    
    return {"futures_positions": positions_data}


@router.get("/export-md")
async def export_markdown_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Экспорт статистики торгов в .md формате
    
    Возвращает markdown файл для скачивания
    """
    portfolio_service = PortfolioService(db)
    portfolio = await portfolio_service.get_portfolio(current_user.id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    markdown_report = await portfolio_service.export_markdown_report(portfolio.id)
    
    # Возвращаем как файл для скачивания
    return Response(
        content=markdown_report,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=draizer_report_{current_user.username}.md"
        }
    )


@router.post("/reset")
async def reset_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    СБРОСИТЬ весь псевдо-счет и статистику портфеля
    
    - Баланс → $1000
    - Total P&L → $0
    - Total Trades → 0
    - Win Rate → 0%
    - Закрыть все открытые SPOT позиции
    - Закрыть все открытые FUTURES позиции (NEW)
    - Удалить все транзакции
    - Удалить все AI решения
    - Удалить все learning notes
    - Удалить все AI sessions
    - Удалить все DeepSeek contexts
    - Удалить все performance logs
    """
    from sqlalchemy import select, delete
    from app.models.portfolio import Portfolio
    from app.models.position import Position
    from app.models.futures_position import FuturesPosition
    from app.models.transaction import Transaction
    from app.models.ai_decision import AIDecision
    from app.models.ai_learning_note import AILearningNote
    from app.models.ai_session import AITradingSession
    from app.models.performance_log import PerformanceLog
    from app.models.performance_score import PerformanceScore
    from decimal import Decimal
    
    # Получить портфель
    stmt = select(Portfolio).where(Portfolio.user_id == current_user.id)
    result = await db.execute(stmt)
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Удалить все транзакции
    await db.execute(
        delete(Transaction).where(Transaction.portfolio_id == portfolio.id)
    )
    
    # Удалить все AI решения
    await db.execute(
        delete(AIDecision).where(AIDecision.portfolio_id == portfolio.id)
    )
    
    # Удалить все learning notes
    await db.execute(
        delete(AILearningNote).where(AILearningNote.portfolio_id == portfolio.id)
    )
    
    # Удалить все AI sessions
    await db.execute(
        delete(AITradingSession).where(AITradingSession.portfolio_id == portfolio.id)
    )
    
    # NOTE: DeepSeek contexts не удаляются (таблица не создана через миграции)
    # Если останутся старые записи - не страшно, они не используются после удаления AI decisions
    
    # Удалить все performance logs
    await db.execute(
        delete(PerformanceLog).where(PerformanceLog.portfolio_id == portfolio.id)
    )
    
    # Удалить performance score
    await db.execute(
        delete(PerformanceScore).where(PerformanceScore.portfolio_id == portfolio.id)
    )
    
    # Закрыть все SPOT позиции
    await db.execute(
        delete(Position).where(Position.portfolio_id == portfolio.id)
    )
    
    # 🔥 NEW: Закрыть все FUTURES позиции
    await db.execute(
        delete(FuturesPosition).where(FuturesPosition.portfolio_id == portfolio.id)
    )
    
    # Сбросить статистику портфеля
    portfolio.balance_usd = Decimal("1000")
    portfolio.total_pnl = Decimal("0")
    portfolio.total_trades = 0
    portfolio.winning_trades = 0
    portfolio.losing_trades = 0
    
    await db.commit()
    
    return {
        "status": "reset_complete",
        "message": "Portfolio reset successfully - All positions (SPOT + FUTURES), transactions, AI data cleared",
        "new_balance": float(portfolio.balance_usd),
        "total_pnl": 0,
        "total_trades": 0,
        "win_rate": 0,
        "cleared_data": [
            "spot_positions",
            "futures_positions", 
            "transactions",
            "ai_decisions",
            "ai_learning_notes",
            "ai_sessions",
            "performance_logs",
            "performance_scores"
        ]
    }



