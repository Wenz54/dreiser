"""Portfolio service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
from typing import Optional, Dict, Any, List
import uuid

from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.position import Position
from app.core.config import settings


class PortfolioService:
    """Portfolio management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_portfolio(self, user_id: uuid.UUID) -> Portfolio:
        """
        Создать виртуальный портфель для нового пользователя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Portfolio с начальным балансом $1000
        """
        portfolio = Portfolio(
            user_id=user_id,
            balance_usd=Decimal(str(settings.INITIAL_BALANCE_USD)),
            initial_balance=Decimal(str(settings.INITIAL_BALANCE_USD)),
            total_pnl=Decimal("0"),
            total_trades=0,
            winning_trades=0,
            losing_trades=0
        )
        
        self.db.add(portfolio)
        await self.db.flush()
        return portfolio
    
    async def get_portfolio(self, user_id: uuid.UUID) -> Optional[Portfolio]:
        """Получить портфель пользователя"""
        stmt = select(Portfolio).where(Portfolio.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_portfolio_stats(self, portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """
        Получить полную статистику портфеля
        
        Returns:
            Детальная статистика
        """
        stmt = select(Portfolio).where(Portfolio.id == portfolio_id)
        result = await self.db.execute(stmt)
        portfolio = result.scalar_one_or_none()
        
        if not portfolio:
            raise Exception("Portfolio not found")
        
        # Получить лучшую/худшую сделку
        transactions_stmt = select(Transaction).where(
            Transaction.portfolio_id == portfolio_id,
            Transaction.pnl.isnot(None)
        )
        transactions_result = await self.db.execute(transactions_stmt)
        transactions = transactions_result.scalars().all()
        
        best_trade = max([t.pnl for t in transactions], default=Decimal("0"))
        worst_trade = min([t.pnl for t in transactions], default=Decimal("0"))
        
        # Средние значения
        winning_trades = [t for t in transactions if t.pnl > 0]
        losing_trades = [t for t in transactions if t.pnl < 0]
        
        avg_win = (
            sum([t.pnl for t in winning_trades]) / len(winning_trades) 
            if winning_trades else Decimal("0")
        )
        avg_loss = (
            sum([t.pnl for t in losing_trades]) / len(losing_trades)
            if losing_trades else Decimal("0")
        )
        
        # Win rate - считаем от фактических сделок с результатом (плюс + минус)
        total_closed_trades = portfolio.winning_trades + portfolio.losing_trades
        win_rate = (
            (portfolio.winning_trades / total_closed_trades * 100)
            if total_closed_trades > 0 else Decimal("0")
        )
        
        # P&L percentage
        pnl_percent = (
            (portfolio.total_pnl / portfolio.initial_balance * 100)
            if portfolio.initial_balance > 0 else Decimal("0")
        )
        
        return {
            "balance_usd": portfolio.balance_usd,
            "initial_balance": portfolio.initial_balance,
            "total_pnl": portfolio.total_pnl,
            "total_pnl_percent": pnl_percent,
            "total_trades": portfolio.total_trades,
            "winning_trades": portfolio.winning_trades,
            "losing_trades": portfolio.losing_trades,
            "win_rate": win_rate,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "avg_win": avg_win,
            "avg_loss": avg_loss
        }
    
    async def get_positions(self, portfolio_id: uuid.UUID) -> List[Position]:
        """Получить все открытые позиции"""
        stmt = select(Position).where(
            Position.portfolio_id == portfolio_id,
            Position.is_closed == False
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_transactions(
        self, 
        portfolio_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transaction]:
        """Получить историю транзакций"""
        stmt = (
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def export_markdown_report(self, portfolio_id: uuid.UUID) -> str:
        """
        Экспорт статистики в .md формате
        
        Returns:
            Markdown formatted report
        """
        # Получить данные
        portfolio_stmt = select(Portfolio).where(Portfolio.id == portfolio_id)
        portfolio_result = await self.db.execute(portfolio_stmt)
        portfolio = portfolio_result.scalar_one_or_none()
        
        if not portfolio:
            raise Exception("Portfolio not found")
        
        stats = await self.get_portfolio_stats(portfolio_id)
        positions = await self.get_positions(portfolio_id)
        transactions = await self.get_transactions(portfolio_id, limit=30)
        
        # Формируем markdown
        from datetime import datetime
        
        report = f"""# Draizer AI Trading Report

**User**: @{portfolio.user.username}  
**Export Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  
**Account Age**: {(datetime.utcnow() - portfolio.created_at).days} days  

---

## Portfolio Summary

| Metric | Value |
|--------|-------|
| Current Balance | ${stats['balance_usd']:,.2f} |
| Initial Balance | ${stats['initial_balance']:,.2f} |
| Total P&L | ${stats['total_pnl']:+,.2f} ({stats['total_pnl_percent']:+.2f}%) |
| Total Trades | {stats['total_trades']} |
| Winning Trades | {stats['winning_trades']} ({stats['win_rate']:.1f}%) |
| Losing Trades | {stats['losing_trades']} |
| Best Trade | ${stats['best_trade']:+,.2f} |
| Worst Trade | ${stats['worst_trade']:+,.2f} |
| Average Win | ${stats['avg_win']:+,.2f} |
| Average Loss | ${stats['avg_loss']:+,.2f} |

---

## Current Positions

"""
        
        if positions:
            for pos in positions:
                unrealized_pnl = (pos.current_price - pos.entry_price) * pos.quantity if pos.current_price else Decimal("0")
                unrealized_pnl_pct = (unrealized_pnl / (pos.entry_price * pos.quantity) * 100) if pos.entry_price > 0 else Decimal("0")
                
                report += f"""
### {pos.symbol}
- **Quantity**: {pos.quantity:.8f}
- **Entry Price**: ${pos.entry_price:,.2f}
- **Current Price**: ${pos.current_price:,.2f}
- **Unrealized P&L**: ${unrealized_pnl:+,.2f} ({unrealized_pnl_pct:+.2f}%)
- **Status**: Open 🟢

"""
        else:
            report += "\n*No open positions*\n"
        
        report += "\n---\n\n## Trading History (Last 30 trades)\n\n"
        
        for i, tx in enumerate(transactions, 1):
            report += f"""
### Trade #{i} - {tx.symbol}
- **Date**: {tx.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **Type**: {tx.type}
- **Quantity**: {tx.quantity:.8f}
- **Price**: ${tx.price:,.2f}
- **Total Value**: ${tx.total_value:,.2f}
"""
            
            if tx.pnl is not None:
                pnl_pct = (tx.pnl / (tx.price * tx.quantity) * 100) if tx.price > 0 else Decimal("0")
                report += f"""- **P&L**: ${tx.pnl:+,.2f} ({pnl_pct:+.2f}%)
"""
                if tx.fee:
                    report += f"- **Fee**: ${tx.fee:,.2f}\n"
            
            report += "\n"
        
        report += """
---

## Notes

⚠️ **IMPORTANT DISCLAIMER**:
This report represents VIRTUAL TRADING SIMULATION only. All trades, P&L, and balances are simulated using real market data from Binance. No actual money was traded. Past performance does not guarantee future results.

**Risk Warning**: Cryptocurrency trading carries significant risk. This simulation does not account for:
- Real market slippage
- Exchange fees and limitations
- Emotional factors in real trading
- Black swan events
- Liquidity constraints

Use this data for educational purposes only.

---

*Generated by Draizer AI Trading Platform*  
*Report Version: 1.0*
"""
        
        return report






