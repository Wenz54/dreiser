"""
Orderbook Snapshot Model - для backtracking и анализа
Сохраняет bid/ask цены с обеих бирж для последующего replay
"""

from sqlalchemy import Column, String, Float, BigInteger, DateTime, Index
from app.db.base_class import Base
from datetime import datetime


class OrderbookSnapshot(Base):
    """
    Snapshot orderbook (best bid/ask) для backtracking
    Записывается каждые N секунд или при значительном изменении цены
    """
    __tablename__ = "orderbook_snapshots"
    
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Exchange & Symbol
    exchange = Column(String(20), nullable=False, index=True)  # binance, bybit
    symbol = Column(String(20), nullable=False, index=True)    # BTCUSDT, ETHUSDT
    
    # Best bid/ask
    bid = Column(Float, nullable=False)
    ask = Column(Float, nullable=False)
    bid_quantity = Column(Float, nullable=True)
    ask_quantity = Column(Float, nullable=True)
    
    # Timestamp (microsecond precision)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    timestamp_ns = Column(BigInteger, nullable=False)  # Nanoseconds since epoch
    
    # Indexes for fast backtest queries
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_exchange_symbol_timestamp', 'exchange', 'symbol', 'timestamp'),
    )





