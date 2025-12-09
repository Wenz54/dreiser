"""
Backtest Service - replay исторических orderbook данных
Анализирует opportunities, spreads, потенциальную прибыль
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from collections import defaultdict
import statistics

from app.models.orderbook_snapshot import OrderbookSnapshot
from app.models.backtest_result import BacktestResult
from app.services.orderbook_recorder import OrderbookRecorder
import logging

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Engine для backtest - replay исторических данных и анализ
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.recorder = OrderbookRecorder(db)
        
        # Strategy parameters (from HFT Risk Manager)
        self.min_spread_bps = 3.0  # Minimum profitable spread
        self.fee_bps = 10.0        # 0.1% per side
        self.slippage_bps = 2.0    # 0.02% estimated slippage
    
    def run_backtest(
        self,
        start_time: datetime,
        end_time: datetime,
        symbols: List[str],
        exchanges: List[str] = ["binance", "bybit"]
    ) -> BacktestResult:
        """
        Запустить backtest на исторических данных
        """
        logger.info(f"🔄 Starting backtest from {start_time} to {end_time}")
        logger.info(f"   Symbols: {symbols}, Exchanges: {exchanges}")
        
        # Create result object
        result = BacktestResult(
            start_time=start_time,
            end_time=end_time,
            duration_seconds=int((end_time - start_time).total_seconds()),
            symbols=symbols,
            exchanges=exchanges,
            min_spread_bps=self.min_spread_bps,
            fee_bps=self.fee_bps,
            slippage_bps=self.slippage_bps,
            completed=False
        )
        self.db.add(result)
        self.db.commit()
        
        try:
            # Get all snapshots for the time period
            snapshots = self.recorder.get_snapshots(
                start_time=start_time,
                end_time=end_time,
                symbols=symbols,
                exchanges=exchanges
            )
            
            logger.info(f"📊 Loaded {len(snapshots)} snapshots")
            
            if len(snapshots) == 0:
                result.error_message = "No historical data found for this period"
                result.completed = True
                self.db.commit()
                return result
            
            # Group snapshots by timestamp for cross-exchange comparison
            opportunities = self._detect_opportunities(snapshots, symbols, exchanges)
            
            # Calculate statistics
            self._calculate_statistics(result, opportunities)
            
            result.completed = True
            result.recommendation = self._generate_recommendation(result)
            self.db.commit()
            
            logger.info(f"✅ Backtest completed: {result.total_opportunities} opportunities found")
            return result
            
        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
            result.error_message = str(e)
            result.completed = True
            self.db.commit()
            raise
    
    def _detect_opportunities(
        self,
        snapshots: List[OrderbookSnapshot],
        symbols: List[str],
        exchanges: List[str]
    ) -> List[Dict]:
        """
        Detect arbitrage opportunities from snapshots
        """
        opportunities = []
        
        # Group snapshots by timestamp and symbol
        time_buckets = defaultdict(lambda: defaultdict(dict))
        
        for snap in snapshots:
            # Round timestamp to nearest 100ms for grouping
            time_key = snap.timestamp.replace(microsecond=(snap.timestamp.microsecond // 100000) * 100000)
            time_buckets[time_key][snap.symbol][snap.exchange] = {
                'bid': snap.bid,
                'ask': snap.ask,
                'bid_qty': snap.bid_quantity or 0,
                'ask_qty': snap.ask_quantity or 0
            }
        
        # Check each time bucket for arbitrage opportunities
        for time_key, symbols_data in time_buckets.items():
            for symbol, exchange_data in symbols_data.items():
                # Need at least 2 exchanges to arbitrage
                if len(exchange_data) < 2:
                    continue
                
                # Find best bid and best ask across exchanges
                best_bid = None
                best_bid_exchange = None
                best_ask = None
                best_ask_exchange = None
                
                for exchange, prices in exchange_data.items():
                    if best_bid is None or prices['bid'] > best_bid:
                        best_bid = prices['bid']
                        best_bid_exchange = exchange
                    
                    if best_ask is None or prices['ask'] < best_ask:
                        best_ask = prices['ask']
                        best_ask_exchange = exchange
                
                # Check if arbitrage exists (bid > ask across exchanges)
                if best_bid > best_ask and best_bid_exchange != best_ask_exchange:
                    # Calculate spread
                    gross_spread_bps = ((best_bid - best_ask) / best_ask) * 10000.0
                    net_spread_bps = gross_spread_bps - (self.fee_bps * 2) - self.slippage_bps
                    
                    # Check if profitable
                    if net_spread_bps >= self.min_spread_bps:
                        opportunities.append({
                            'timestamp': time_key,
                            'symbol': symbol,
                            'buy_exchange': best_ask_exchange,
                            'sell_exchange': best_bid_exchange,
                            'buy_price': best_ask,
                            'sell_price': best_bid,
                            'gross_spread_bps': gross_spread_bps,
                            'net_spread_bps': net_spread_bps,
                            'potential_profit_usd': (net_spread_bps / 10000.0) * 100.0  # Assuming $100 position
                        })
        
        return opportunities
    
    def _calculate_statistics(self, result: BacktestResult, opportunities: List[Dict]):
        """
        Calculate statistics from opportunities
        """
        if not opportunities:
            result.total_opportunities = 0
            result.opportunities_per_minute = 0.0
            return
        
        result.total_opportunities = len(opportunities)
        
        # Opportunities per minute
        duration_minutes = result.duration_seconds / 60.0
        result.opportunities_per_minute = result.total_opportunities / duration_minutes if duration_minutes > 0 else 0
        
        # Spread statistics
        spreads = [opp['net_spread_bps'] for opp in opportunities]
        result.avg_spread_bps = statistics.mean(spreads)
        result.min_spread_bps_found = min(spreads)
        result.max_spread_bps_found = max(spreads)
        result.median_spread_bps = statistics.median(spreads)
        
        # Profitability
        profits = [opp['potential_profit_usd'] for opp in opportunities]
        result.total_potential_profit_usd = sum(profits)
        result.avg_profit_per_trade_usd = statistics.mean(profits)
        result.best_trade_profit_usd = max(profits)
        
        # Per-symbol breakdown
        symbol_stats = defaultdict(lambda: {'opportunities': 0, 'spreads': [], 'profits': []})
        for opp in opportunities:
            symbol_stats[opp['symbol']]['opportunities'] += 1
            symbol_stats[opp['symbol']]['spreads'].append(opp['net_spread_bps'])
            symbol_stats[opp['symbol']]['profits'].append(opp['potential_profit_usd'])
        
        # Calculate averages per symbol
        result.symbol_stats = {}
        for symbol, stats in symbol_stats.items():
            result.symbol_stats[symbol] = {
                'opportunities': stats['opportunities'],
                'avg_spread_bps': statistics.mean(stats['spreads']),
                'total_profit_usd': sum(stats['profits'])
            }
    
    def _generate_recommendation(self, result: BacktestResult) -> str:
        """
        Generate recommendation based on backtest results
        """
        if result.total_opportunities == 0:
            return "❌ NOT PROFITABLE: No arbitrage opportunities found in this period. Market is too efficient."
        
        if result.opportunities_per_minute < 0.1:
            return f"⚠️  LOW FREQUENCY: Only {result.opportunities_per_minute:.2f} opportunities/minute. " \
                   f"Potential profit: ${result.total_potential_profit_usd:.2f} over {result.duration_seconds/3600:.1f} hours."
        
        if result.opportunities_per_minute >= 1.0:
            return f"✅ PROFITABLE: {result.opportunities_per_minute:.2f} opportunities/minute. " \
                   f"Avg spread: {result.avg_spread_bps:.2f} bps. " \
                   f"Potential profit: ${result.total_potential_profit_usd:.2f} over {result.duration_seconds/3600:.1f} hours."
        
        return f"⚡ MODERATE: {result.opportunities_per_minute:.2f} opportunities/minute. " \
               f"Potential profit: ${result.total_potential_profit_usd:.2f}. Consider testing longer period."
