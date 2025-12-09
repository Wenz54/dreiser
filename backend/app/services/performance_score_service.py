"""Performance Score Service - управление рейтингом AI"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from typing import Optional
from datetime import datetime, timedelta
import uuid

from app.models.performance_score import PerformanceScore
from app.models.portfolio import Portfolio
from app.models.ai_session import AITradingSession


class PerformanceScoreService:
    """Сервис управления рейтингом производительности AI (0-100)"""
    
    @staticmethod
    async def get_or_create(db: AsyncSession, portfolio_id: uuid.UUID) -> PerformanceScore:
        """Получить или создать рейтинг для портфеля (with race condition protection)"""
        stmt = select(PerformanceScore).where(PerformanceScore.portfolio_id == portfolio_id)
        result = await db.execute(stmt)
        score = result.scalar_one_or_none()
        
        if not score:
            try:
                score = PerformanceScore(portfolio_id=portfolio_id, score=50)
                db.add(score)
                await db.flush()
            except Exception as e:
                # Race condition: другой процесс уже создал запись
                # Откатываем и пробуем ещё раз
                await db.rollback()
                result = await db.execute(stmt)
                score = result.scalar_one_or_none()
                if not score:
                    # Всё ещё нет? Что-то пошло не так
                    raise Exception(f"Failed to get_or_create PerformanceScore: {e}")
        
        return score
    
    @staticmethod
    async def update_after_trade(
        db: AsyncSession,
        portfolio_id: uuid.UUID,
        pnl: Decimal,
        pnl_percent: Decimal,
        was_profitable: bool
    ):
        """Обновить рейтинг после сделки"""
        score = await PerformanceScoreService.get_or_create(db, portfolio_id)
        
        # Update stats
        score.total_trades += 1
        if was_profitable:
            score.winning_trades += 1
        score.total_pnl = Decimal(str(score.total_pnl)) + pnl
        
        # Calculate score change
        if was_profitable:
            # +1 за выигрыш, +бонус за размер прибыли
            bonus = min(int(float(pnl_percent) / 2), 5)  # Макс +5 за > 10% прибыли
            change = 1 + bonus
            reason = f"Прибыль {pnl_percent:.2f}%: +{change} pts"
        else:
            # -1 за проигрыш, -штраф за размер убытка
            penalty = min(int(abs(float(pnl_percent)) / 2), 5)  # Макс -5 за > -10%
            change = -(1 + penalty)
            reason = f"Убыток {pnl_percent:.2f}%: {change} pts"
        
        # Apply change
        new_score = max(0, min(100, score.score + change))
        score.score = new_score
        score.last_change_reason = reason
        
        # Обновить время последней сделки (сбросить таймер простоя)
        score.last_trade_at = datetime.utcnow()
        
        await db.flush()
        return score
    
    @staticmethod
    async def penalize_rule_violation(
        db: AsyncSession,
        portfolio_id: uuid.UUID,
        violation_type: str
    ):
        """Штраф за нарушение правил"""
        score = await PerformanceScoreService.get_or_create(db, portfolio_id)
        
        score.rule_violations += 1
        penalty = 3  # -3 pts за нарушение
        new_score = max(0, score.score - penalty)
        score.score = new_score
        score.last_change_reason = f"Нарушение: {violation_type} (-{penalty} pts)"
        
        await db.flush()
        return score
    
    @staticmethod
    async def check_inactivity_penalty(
        db: AsyncSession,
        portfolio_id: uuid.UUID
    ):
        """
        Проверить и применить штраф за простой (1 час без сделок)
        
        ⚠️ НЕ применяется в observation mode (learning период)!
        ⏱️ Проверка происходит максимум раз в 59 минут
        """
        score = await PerformanceScoreService.get_or_create(db, portfolio_id)
        now = datetime.utcnow()
        
        # 0. Проверить прошло ли 59 минут с последней проверки
        if score.last_inactivity_check_at:
            time_since_last_check = now - score.last_inactivity_check_at
            if time_since_last_check < timedelta(minutes=59):
                # Слишком рано проверять снова
                return score
        
        # Обновить время проверки
        score.last_inactivity_check_at = now
        
        # 1. Проверить observation mode - если AI в обучении, штрафа НЕТ!
        stmt = select(AITradingSession).where(
            AITradingSession.portfolio_id == portfolio_id,
            AITradingSession.is_active == True
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session and session.observation_mode_until:
            if now < session.observation_mode_until:
                # В OBSERVATION MODE - штрафа нет!
                print(f"  ✅ Observation Mode: NO inactivity penalty (AI is learning)")
                await db.flush()
                return score
        
        # 2. Если никогда не торговал - не штрафуем
        if not score.last_trade_at:
            await db.flush()
            return score
        
        # 3. Проверить прошел ли час с последней сделки
        time_since_last_trade = now - score.last_trade_at
        
        # 4. Если больше 1 часа - штраф
        if time_since_last_trade > timedelta(hours=1):
            hours_idle = int(time_since_last_trade.total_seconds() / 3600)
            
            # Применить штраф
            penalty = 3
            new_score = max(0, score.score - penalty)
            score.score = new_score
            score.last_change_reason = f"Простой {hours_idle}ч без сделок: -{penalty} pts"
            
            await db.flush()
            print(f"  ⚠️ INACTIVITY PENALTY: -{penalty} pts (idle {hours_idle}h)")
        else:
            await db.flush()
        
        return score
    
    @staticmethod
    async def reset_score(db: AsyncSession, portfolio_id: uuid.UUID):
        """Сбросить Performance Score до начального значения (50 - нейтральный старт)"""
        score = await PerformanceScoreService.get_or_create(db, portfolio_id)
        
        score.score = 50
        score.total_trades = 0
        score.winning_trades = 0
        score.total_pnl = Decimal("0")
        score.rule_violations = 0
        score.last_trade_at = None
        score.last_inactivity_check_at = None
        score.last_change_reason = "Score reset"
        
        await db.flush()
        return score
    
    @staticmethod
    def get_confidence_modifier(score_value: int) -> float:
        """Модификатор уверенности на основе рейтинга"""
        # 0-30: очень плохо → снижаем confidence на 15%
        # 30-50: плохо → снижаем на 10%
        # 50-70: норма → без изменений
        # 70-85: хорошо → повышаем на 5%
        # 85-100: отлично → повышаем на 10%
        
        if score_value < 30:
            return -15.0
        elif score_value < 50:
            return -10.0
        elif score_value < 70:
            return 0.0
        elif score_value < 85:
            return 5.0
        else:
            return 10.0


# Singleton
performance_score_service = PerformanceScoreService()
