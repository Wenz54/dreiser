"""
Backtest Result Model - результаты backtracking анализа
Хранит статистику opportunities, spreads, потенциальную прибыль
"""

from sqlalchemy import Column, String, Float, Integer, BigInteger, DateTime, Text, Boolean, JSON
from app.db.base_class import Base
from datetime import datetime


class BacktestResult(Base):
    """
    Результаты backtest - анализ исторических данных
    """
    __tablename__ = "backtest_results"
    
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Backtest parameters
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    
    # Symbols tested
    symbols = Column(JSON, nullable=False)  # ["BTCUSDT", "ETHUSDT", ...]
    exchanges = Column(JSON, nullable=False)  # ["binance", "bybit"]
    
    # Strategy parameters
    min_spread_bps = Column(Float, nullable=False)
    fee_bps = Column(Float, nullable=False)
    slippage_bps = Column(Float, nullable=False)
    
    # Results - Opportunities
    total_opportunities = Column(Integer, nullable=False, default=0)
    opportunities_per_minute = Column(Float, nullable=False, default=0.0)
    
    # Results - Spreads
    avg_spread_bps = Column(Float, nullable=True)
    min_spread_bps_found = Column(Float, nullable=True)
    max_spread_bps_found = Column(Float, nullable=True)
    median_spread_bps = Column(Float, nullable=True)
    
    # Results - Profitability
    total_potential_profit_usd = Column(Float, nullable=False, default=0.0)
    avg_profit_per_trade_usd = Column(Float, nullable=True)
    best_trade_profit_usd = Column(Float, nullable=True)
    
    # Results - Timing
    avg_opportunity_lifetime_ms = Column(Float, nullable=True)  # How long opportunity lasted
    
    # Results - Per Symbol breakdown
    symbol_stats = Column(JSON, nullable=True)  # {"BTCUSDT": {"opps": 10, "avg_spread": 5.5}, ...}
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    
    # Conclusion
    recommendation = Column(Text, nullable=True)  # "Profitable", "Not profitable", etc.





