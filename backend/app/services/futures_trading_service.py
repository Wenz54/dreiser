"""Futures Trading Service - фьючерсная торговля с leverage 3x"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from typing import Optional
import uuid
from datetime import datetime

from app.models.portfolio import Portfolio
from app.models.futures_position import FuturesPosition
from app.models.transaction import Transaction, TransactionType
from app.services.binance_service import binance_service
from app.services.performance_score_service import performance_score_service


class FuturesTradingService:
    """
    Futures trading service (VIRTUAL, 3x leverage)
    
    LONG: Profit when price UP
    SHORT: Profit when price DOWN
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.binance = binance_service
        self.leverage = 3  # Fixed 3x leverage для безопасности
    
    async def execute_long(
        self,
        portfolio: Portfolio,
        symbol: str,
        amount_usd: Decimal,
        ai_decision_id: Optional[uuid.UUID] = None,
        entry_volume_ratio: Optional[Decimal] = None
    ) -> FuturesPosition:
        """
        VIRTUAL LONG position (ставка на рост)
        
        Args:
            portfolio: Портфель
            symbol: Пара (e.g. BTCUSDT)
            amount_usd: Размер позиции в USD
            ai_decision_id: ID AI решения
            entry_volume_ratio: Volume ratio (5m/avg_15m) at entry (для AI context)
        
        Returns:
            FuturesPosition
        """
        # 1. Получить текущую цену
        current_price, is_stale = self.binance.get_ticker_price(symbol)
        if not current_price:
            raise Exception("Failed to get market price")
        
        # 1.5 🚨 VOLUME FILTER: Блокировать LONG при низком volume!
        MIN_VOLUME_RATIO = Decimal("0.8")
        if entry_volume_ratio is not None and entry_volume_ratio < MIN_VOLUME_RATIO:
            vol_str = f"{float(entry_volume_ratio):.2f}"
            print(f"❌ BLOCKED LONG for {symbol}: Volume too low (×{vol_str}), require ×{float(MIN_VOLUME_RATIO):.1f}+")
            print(f"   Reason: Low volume = weak signal, likely false breakout!")
            raise Exception(f"VOLUME_FILTER_BLOCKED: Entry volume ×{vol_str} < required ×{float(MIN_VOLUME_RATIO):.1f}")
        
        # 2. Проверить futures баланс
        if portfolio.balance_usd < amount_usd:
            raise Exception(f"Insufficient balance for margin: ${portfolio.balance_usd} < ${amount_usd}")
        
        # 3. Рассчитать quantity (с учетом leverage)
        # С 3x leverage: позиция на $300 требует только $100 маржи
        position_size = amount_usd * Decimal(str(self.leverage))
        quantity = position_size / current_price
        
        # 4. Создать LONG позицию
        position = FuturesPosition(
            portfolio_id=portfolio.id,
            symbol=symbol,
            side="LONG",
            entry_price=current_price,
            quantity=quantity,
            leverage=self.leverage,
            current_price=current_price,
            liquidation_price=current_price * Decimal("0.67"),  # -33% = liquidation
            entry_volume_ratio=entry_volume_ratio,  # НОВОЕ: сохраняем entry volume
            is_simulated=True
        )
        
        # 5. Списать маржу с futures баланса
        portfolio.balance_usd -= amount_usd
        
        # 6. Сохранить (НЕ делаем commit здесь - он будет в trading_service!)
        self.db.add(position)
        await self.db.flush()
        
        # 7. Записать транзакцию LONG
        transaction = Transaction(
            portfolio_id=portfolio.id,
            position_id=None,  # Futures positions separate
            ai_decision_id=ai_decision_id,
            type=TransactionType.LONG.value,
            symbol=symbol,
            quantity=quantity,
            price=current_price,
            total_value=position_size,
            fee=Decimal("0"),
            pnl=None,
            is_simulated=True,
            simulated_price=current_price,
            extra_metadata={"margin": float(amount_usd), "leverage": self.leverage, "liquidation_price": float(position.liquidation_price)}
        )
        self.db.add(transaction)
        await self.db.flush()
        
        print(f"  ✅ LONG OPENED: {symbol} @ ${float(current_price):.2f}, size=${float(position_size):.2f} (margin=${float(amount_usd):.2f}, {self.leverage}x leverage)")
        print(f"     Liquidation price: ${float(position.liquidation_price):.2f}")
        
        return position
    
    async def execute_short(
        self,
        portfolio: Portfolio,
        symbol: str,
        amount_usd: Decimal,
        ai_decision_id: Optional[uuid.UUID] = None,
        entry_volume_ratio: Optional[Decimal] = None
    ) -> FuturesPosition:
        """
        VIRTUAL SHORT position (ставка на падение)
        
        Args:
            portfolio: Портфель
            symbol: Пара
            amount_usd: Размер позиции в USD
            ai_decision_id: ID AI решения
            entry_volume_ratio: Volume ratio (5m/avg_15m) at entry (для AI context)
        
        Returns:
            FuturesPosition
        """
        # 1. Получить текущую цену
        current_price, is_stale = self.binance.get_ticker_price(symbol)
        if not current_price:
            raise Exception("Failed to get market price")
        
        # 1.5 🚨 VOLUME FILTER: Блокировать SHORT при низком volume!
        # КРИТИЧНО: Падение БЕЗ volume = ложный сигнал! Легко разворачивается!
        MIN_VOLUME_RATIO = Decimal("0.8")
        if entry_volume_ratio is not None and entry_volume_ratio < MIN_VOLUME_RATIO:
            vol_str = f"{float(entry_volume_ratio):.2f}"
            print(f"❌ BLOCKED SHORT for {symbol}: Volume too low (×{vol_str}), require ×{float(MIN_VOLUME_RATIO):.1f}+")
            print(f"   Reason: Падение БЕЗ volume = 'вакуум', НЕ давление продавцов! Легко развернётся!")
            raise Exception(f"VOLUME_FILTER_BLOCKED: Entry volume ×{vol_str} < required ×{float(MIN_VOLUME_RATIO):.1f}")
        
        # 2. Проверить futures баланс
        if portfolio.balance_usd < amount_usd:
            raise Exception(f"Insufficient balance for margin: ${portfolio.balance_usd} < ${amount_usd}")
        
        # 3. Рассчитать quantity (с учетом leverage)
        position_size = amount_usd * Decimal(str(self.leverage))
        quantity = position_size / current_price
        
        # 4. Создать SHORT позицию
        position = FuturesPosition(
            portfolio_id=portfolio.id,
            symbol=symbol,
            side="SHORT",
            entry_price=current_price,
            quantity=quantity,
            leverage=self.leverage,
            current_price=current_price,
            liquidation_price=current_price * Decimal("1.33"),  # +33% = liquidation
            entry_volume_ratio=entry_volume_ratio,  # НОВОЕ: сохраняем entry volume
            is_simulated=True
        )
        
        # 5. Списать маржу с futures баланса
        portfolio.balance_usd -= amount_usd
        
        # 6. Сохранить (НЕ делаем commit здесь - он будет в trading_service!)
        self.db.add(position)
        await self.db.flush()
        
        # 7. Записать транзакцию SHORT
        transaction = Transaction(
            portfolio_id=portfolio.id,
            position_id=None,  # Futures positions separate
            ai_decision_id=ai_decision_id,
            type=TransactionType.SHORT.value,
            symbol=symbol,
            quantity=quantity,
            price=current_price,
            total_value=position_size,
            fee=Decimal("0"),
            pnl=None,
            is_simulated=True,
            simulated_price=current_price,
            extra_metadata={"margin": float(amount_usd), "leverage": self.leverage, "liquidation_price": float(position.liquidation_price)}
        )
        self.db.add(transaction)
        await self.db.flush()
        
        print(f"  ✅ SHORT OPENED: {symbol} @ ${float(current_price):.2f}, size=${float(position_size):.2f} (margin=${float(amount_usd):.2f}, {self.leverage}x leverage)")
        print(f"     Liquidation price: ${float(position.liquidation_price):.2f}")
        
        return position
    
    async def close_position(
        self,
        portfolio: Portfolio,
        position: FuturesPosition
    ) -> Decimal:
        """
        Закрыть futures позицию
        
        Returns:
            Realized P&L
        """
        # 1. Получить текущую цену
        current_price, is_stale = self.binance.get_ticker_price(position.symbol)
        if not current_price:
            raise Exception("Failed to get market price")
        
        # 2. Рассчитать P&L
        pnl = position.calculate_pnl(current_price)
        
        # 3. Обновить позицию
        position.is_closed = True
        position.exit_price = current_price
        position.realized_pnl = pnl
        position.closed_at = datetime.utcnow()
        
        # 4. Вернуть маржу + P&L в общий баланс
        margin = (position.quantity * position.entry_price) / Decimal(str(self.leverage))
        portfolio.balance_usd += (margin + pnl)
        portfolio.total_pnl += pnl
        
        # 5. Статистика
        portfolio.total_trades += 1
        if pnl > Decimal("0"):
            portfolio.winning_trades += 1
        else:
            portfolio.losing_trades += 1
        
        # 6. Обновить Performance Score
        pnl_percent = (pnl / margin) * Decimal("100") if margin > 0 else Decimal("0")
        await performance_score_service.update_after_trade(
            db=self.db,
            portfolio_id=portfolio.id,
            pnl=pnl,
            pnl_percent=pnl_percent,
            was_profitable=(pnl > Decimal("0"))
        )
        
        # 7. Записать транзакцию закрытия
        transaction_type = TransactionType.CLOSE_LONG if position.side == "LONG" else TransactionType.CLOSE_SHORT
        transaction = Transaction(
            portfolio_id=portfolio.id,
            position_id=None,
            ai_decision_id=None,
            type=transaction_type.value,
            symbol=position.symbol,
            quantity=position.quantity,
            price=current_price,
            total_value=(position.quantity * current_price) / Decimal(str(self.leverage)),
            fee=Decimal("0"),
            pnl=pnl,
            is_simulated=True,
            simulated_price=current_price,
            extra_metadata={"entry_price": float(position.entry_price), "margin": float(margin), "leverage": self.leverage}
        )
        self.db.add(transaction)
        await self.db.flush()
        
        # 9. КРИТИЧНО: Сохранить СНАЧАЛА позицию и транзакцию!
        await self.db.commit()
        
        # 10. Генерировать AI learning note (post-mortem для FUTURES)
        # ВАЖНО: Обернуто в try-except, чтобы ошибка не откатила закрытие позиции!
        try:
            await self._generate_futures_learning_note(
                portfolio=portfolio,
                transaction=transaction,
                position=position,
                pnl_percent=pnl_percent
            )
            await self.db.commit()  # Commit learning note отдельно
        except Exception as e:
            print(f"  ⚠️ Failed to save learning note (non-critical): {e}")
            # Откатить только learning note, позиция уже закрыта!
            await self.db.rollback()
        
        side_str = "LONG" if position.side == "LONG" else "SHORT"
        pnl_pct = float(pnl_percent)
        print(f"  ✅ {side_str} CLOSED: {position.symbol} @ ${float(current_price):.2f}, P&L ${float(pnl):+.2f} ({pnl_pct:+.2f}%)")
        
        return pnl
    
    async def check_liquidation(
        self,
        portfolio: Portfolio,
        position: FuturesPosition,
        current_price: Decimal
    ) -> bool:
        """
        Проверить ликвидацию позиции
        
        Returns:
            True если ликвидирована
        """
        if position.is_closed:
            return False
        
        is_liquidated = False
        
        if position.side == "LONG":
            # LONG ликвидируется при падении цены
            if current_price <= position.liquidation_price:
                is_liquidated = True
        else:  # SHORT
            # SHORT ликвидируется при росте цены
            if current_price >= position.liquidation_price:
                is_liquidated = True
        
        if is_liquidated:
            # Ликвидация = потеря всей маржи
            margin = (position.quantity * position.entry_price) / Decimal(str(self.leverage))
            pnl = -margin
            
            position.is_closed = True
            position.exit_price = current_price
            position.realized_pnl = pnl
            position.closed_at = datetime.utcnow()
            
            portfolio.total_pnl += pnl
            portfolio.total_trades += 1
            portfolio.losing_trades += 1
            
            # Обновить Performance Score
            pnl_percent = Decimal("-100")  # Полная потеря маржи
            await performance_score_service.update_after_trade(
                db=self.db,
                portfolio_id=portfolio.id,
                pnl=pnl,
                pnl_percent=pnl_percent,
                was_profitable=False
            )
            
            await self.db.flush()
            
            side_str = "LONG" if position.side == "LONG" else "SHORT"
            print(f"  ⚠️ LIQUIDATED: {side_str} {position.symbol} @ ${float(current_price):.2f}, Loss ${float(pnl):+.2f}")
        
        return is_liquidated
    
    async def update_unrealized_pnl(
        self,
        position: FuturesPosition,
        current_price: Decimal
    ):
        """Обновить unrealized P&L"""
        if not position.is_closed:
            position.current_price = current_price
            position.unrealized_pnl = position.calculate_pnl(current_price)
            await self.db.flush()
    
    async def _generate_futures_learning_note(
        self,
        portfolio: Portfolio,
        transaction: "Transaction",
        position: FuturesPosition,
        pnl_percent: Decimal
    ):
        """
        Генерирует AI learning note для закрытой FUTURES позиции
        """
        from app.services.ai_learning_service import ai_learning_service
        from app.models.ai_learning_note import AILearningNote
        from app.models.ai_decision import AIDecision
        from datetime import datetime
        from sqlalchemy import select, desc
        
        try:
            # НОВОЕ: Попытаться получить AI decision для FUTURES
            entry_reasoning = None
            entry_confidence = None
            ai_decision_id = None
            
            # Найти последнее решение AI по этому символу (LONG/SHORT)
            decision_type_str = f"CLOSE_{position.side}"  # CLOSE_LONG или CLOSE_SHORT
            ai_decision_stmt = select(AIDecision).where(
                AIDecision.symbol == transaction.symbol,
                AIDecision.decision_type.in_(["LONG", "SHORT"])  # Ищем открывающее решение
            ).order_by(desc(AIDecision.created_at)).limit(1)
            
            ai_decision_result = await self.db.execute(ai_decision_stmt)
            ai_decision = ai_decision_result.scalar_one_or_none()
            
            if ai_decision:
                entry_reasoning = ai_decision.reasoning
                entry_confidence = ai_decision.confidence
                ai_decision_id = ai_decision.id
            
            # Рассчитать длительность сделки
            duration_minutes = None
            if position.created_at:
                duration = datetime.utcnow() - position.created_at
                duration_minutes = int(duration.total_seconds() / 60)
            
            # Получить market conditions
            ticker, _ = self.binance.get_24h_ticker(transaction.symbol)
            market_conditions = {
                "symbol": transaction.symbol,
                "price_at_exit": float(transaction.price),
                "change_24h": float(ticker.get("change_24h", 0)) if ticker else 0,
                "volume_24h": float(ticker.get("volume_24h", 0)) if ticker else 0,
                "position_type": position.side,
                "leverage": position.leverage
            }
            
            # НОВОЕ: Получить news context для более глубокого анализа
            from app.services.trading_service import TradingService
            trading_service_temp = TradingService(self.db)
            news_context = await trading_service_temp._get_latest_news_context()
            
            # Генерировать AI analysis
            analysis = await ai_learning_service.generate_learning_note(
                symbol=transaction.symbol,
                entry_price=Decimal(str(position.entry_price)),
                exit_price=Decimal(str(transaction.price)),
                pnl=transaction.pnl or Decimal("0"),
                pnl_percent=pnl_percent,
                duration_minutes=duration_minutes or 0,
                entry_reasoning=entry_reasoning,  # НОВОЕ: теперь передаём!
                entry_confidence=entry_confidence,  # НОВОЕ: теперь передаём!
                market_conditions=market_conditions,
                news_context=news_context,  # НОВОЕ: теперь передаём!
                position_type=position.side  # LONG или SHORT
            )
            
            # НОВОЕ: СОХРАНЯТЬ learning note в БД (ранее только генерировали!)
            learning_note = AILearningNote(
                portfolio_id=portfolio.id,
                trade_id=transaction.id,
                decision_id=ai_decision_id,
                symbol=transaction.symbol,
                position_type=position.side,  # КРИТИЧНО: LONG или SHORT
                trade_result="WIN" if (transaction.pnl and transaction.pnl > 0) else "LOSS",
                profit_loss=transaction.pnl or Decimal("0"),
                entry_price=position.entry_price,
                exit_price=transaction.price,
                pnl=transaction.pnl or Decimal("0"),
                pnl_percent=pnl_percent,
                duration_minutes=duration_minutes,
                was_profitable=transaction.pnl > 0 if transaction.pnl else False,
                what_went_right=analysis["what_went_right"],
                what_went_wrong=analysis["what_went_wrong"],
                lesson_learned=analysis["lesson_learned"],  # В КАПСЕ!
                improvement_suggestion=analysis["improvement_suggestion"],
                market_conditions=market_conditions,
                news_context=news_context[:500] if news_context else None,
                ai_confidence_at_entry=entry_confidence,
                ai_reasoning_at_entry=entry_reasoning
            )
            
            self.db.add(learning_note)
            await self.db.flush()
            
            print(f"  📝 AI Learning note SAVED for {position.side} {transaction.symbol}: {analysis.get('lesson_learned', 'N/A')[:50]}...")
            
        except Exception as e:
            print(f"  ⚠️ Failed to generate futures learning note: {e}")


# Singleton
futures_trading_service = FuturesTradingService

