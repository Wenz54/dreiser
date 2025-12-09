"""
Orderbook Recorder Service - записывает snapshots для backtracking
Получает данные из shared memory C-engine и сохраняет в БД
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.orderbook_snapshot import OrderbookSnapshot
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class OrderbookRecorder:
    """
    Записывает orderbook snapshots в БД для последующего backtracking
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.is_running = False
        self.record_interval_seconds = 1  # Записывать каждую секунду
        
    async def start_recording(self, symbols: List[str], exchanges: List[str]):
        """
        Начать запись orderbook snapshots
        """
        self.is_running = True
        logger.info(f"📊 Starting orderbook recording for {symbols} on {exchanges}")
        
        while self.is_running:
            try:
                # Get current prices from C-engine shared memory
                # TODO: Implement shared memory reading
                # For now, this is a placeholder
                
                # In real implementation, we would:
                # 1. Read from shared memory (price_cache)
                # 2. Save to DB
                # 3. Sleep for interval
                
                await asyncio.sleep(self.record_interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Error recording orderbook: {e}")
                await asyncio.sleep(5)
    
    def stop_recording(self):
        """
        Остановить запись
        """
        self.is_running = False
        logger.info("⏸️  Orderbook recording stopped")
    
    def save_snapshot(
        self,
        exchange: str,
        symbol: str,
        bid: float,
        ask: float,
        bid_qty: float = 0.0,
        ask_qty: float = 0.0,
        timestamp_ns: int = None
    ):
        """
        Сохранить один snapshot в БД
        """
        if timestamp_ns is None:
            timestamp_ns = int(time.time() * 1_000_000_000)
        
        snapshot = OrderbookSnapshot(
            exchange=exchange,
            symbol=symbol,
            bid=bid,
            ask=ask,
            bid_quantity=bid_qty,
            ask_quantity=ask_qty,
            timestamp=datetime.utcnow(),
            timestamp_ns=timestamp_ns
        )
        
        self.db.add(snapshot)
        self.db.commit()
        
        return snapshot
    
    def get_snapshots(
        self,
        start_time: datetime,
        end_time: datetime,
        symbols: List[str] = None,
        exchanges: List[str] = None
    ) -> List[OrderbookSnapshot]:
        """
        Получить snapshots для backtest
        """
        query = self.db.query(OrderbookSnapshot).filter(
            OrderbookSnapshot.timestamp >= start_time,
            OrderbookSnapshot.timestamp <= end_time
        )
        
        if symbols:
            query = query.filter(OrderbookSnapshot.symbol.in_(symbols))
        
        if exchanges:
            query = query.filter(OrderbookSnapshot.exchange.in_(exchanges))
        
        return query.order_by(OrderbookSnapshot.timestamp).all()





