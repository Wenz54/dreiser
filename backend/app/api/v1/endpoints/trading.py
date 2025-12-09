"""Trading endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from decimal import Decimal

from app.db.session import get_db
from app.services.trading_service import TradingService
from app.services.portfolio_service import PortfolioService
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/trading", tags=["Trading"])


class ManualTradeRequest(BaseModel):
    """Manual trade request"""
    action: str  # "BUY" or "SELL"
    symbol: str
    amount_usd: float  # For BUY
    quantity: float = None  # For SELL (optional, None = sell all)


@router.get("/history")
async def get_trading_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить историю виртуальных сделок
    """
    portfolio_service = PortfolioService(db)
    portfolio = await portfolio_service.get_portfolio(current_user.id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    transactions = await portfolio_service.get_transactions(portfolio.id, limit, offset)
    
    return {
        "transactions": [
            {
                "id": str(tx.id),
                "type": tx.type,  # Already a string
                "symbol": tx.symbol,
                "quantity": float(tx.quantity),
                "price": float(tx.price),
                "total_value": float(tx.total_value),
                "pnl": float(tx.pnl) if tx.pnl else None,
                "fee": float(tx.fee) if tx.fee else 0,
                "is_simulated": tx.is_simulated,
                "executed_at": tx.created_at.isoformat()
            }
            for tx in transactions
        ]
    }


@router.post("/manual-trade")
async def manual_trade(
    trade_request: ManualTradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ручная виртуальная сделка (для тестирования)
    
    ⚠️ Это ВИРТУАЛЬНАЯ сделка (симуляция)
    """
    portfolio_service = PortfolioService(db)
    portfolio = await portfolio_service.get_portfolio(current_user.id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    trading_service = TradingService(db)
    
    try:
        if trade_request.action.upper() == "BUY":
            transaction = await trading_service.execute_buy(
                portfolio=portfolio,
                symbol=trade_request.symbol,
                amount_usd=Decimal(str(trade_request.amount_usd))
            )
        elif trade_request.action.upper() == "SELL":
            quantity = Decimal(str(trade_request.quantity)) if trade_request.quantity else None
            transaction = await trading_service.execute_sell(
                portfolio=portfolio,
                symbol=trade_request.symbol,
                quantity=quantity
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'BUY' or 'SELL'")
        
        await db.commit()
        
        return {
            "message": f"Virtual {trade_request.action} executed successfully",
            "transaction": {
                "id": str(transaction.id),
                "type": transaction.type,  # Already a string
                "symbol": transaction.symbol,
                "quantity": float(transaction.quantity),
                "price": float(transaction.price),
                "total_value": float(transaction.total_value),
                "pnl": float(transaction.pnl) if transaction.pnl else None,
                "is_simulated": transaction.is_simulated
            }
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))






