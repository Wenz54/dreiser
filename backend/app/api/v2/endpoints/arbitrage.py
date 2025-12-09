"""
DRAIZER V2 API - Arbitrage Statistics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional
import time

from app.api.deps import get_current_user
from app.services.c_engine_bridge import CEngineBridge
from app.models.user import User

router = APIRouter()

# Global bridge instance
_bridge = None

def get_bridge() -> CEngineBridge:
    """Get or create C engine bridge"""
    global _bridge
    if _bridge is None:
        _bridge = CEngineBridge()
        _bridge.connect()
    return _bridge


@router.get("/stats")
async def get_arbitrage_stats(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get arbitrage statistics for dashboard
    
    Returns:
        Stats matching frontend DashboardStats interface
    """
    bridge = get_bridge()
    
    stats = bridge.get_stats()
    if not stats:
        # Return default stats if engine not running
        return {
            'engine_status': 'STOPPED',
            'uptime_seconds': 0,
            'connected_exchanges': 0,
            'total_exchanges': 4,
            'balance_usd': 1000.0,
            'total_operations': 0,
            'total_profit': 0.0,
            'avg_spread_bps': 0.0,
            'avg_execution_time_us': 0,
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'win_rate_percent': 0.0,
            'best_pair': None,
            'worst_pair': None
        }
    
    # Map C-engine stats to frontend format
    return {
        'engine_status': 'RUNNING' if stats['engine_running'] else 'STOPPED',
        'uptime_seconds': 0,  # TODO: calculate from last_update_ns
        'connected_exchanges': 4,  # TODO: read from engine
        'total_exchanges': 4,
        'balance_usd': stats['balance_usd'],
        'total_operations': stats['opportunities_executed'],
        'total_profit': stats['total_profit_usd'],
        'avg_spread_bps': 0.0,  # TODO: calculate from operations
        'avg_execution_time_us': stats['avg_latency_us'],
        'opportunities_found': stats['opportunities_detected'],
        'opportunities_executed': stats['opportunities_executed'],
        'win_rate_percent': stats['win_rate'] * 100,
        'best_pair': None,  # TODO: calculate from operations
        'worst_pair': None   # TODO: calculate from operations
    }


@router.get("/profit-history")
async def get_profit_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000)
) -> List[Dict]:
    """
    Get profit history for chart
    
    Returns:
        List of profit points with timestamp and cumulative
    """
    bridge = get_bridge()
    
    # Get operations from C-engine shared memory
    operations = bridge.get_operations(limit=limit)
    
    if not operations:
        return []
    
    # Calculate cumulative profit
    cumulative = 0.0
    profit_history = []
    
    for op in operations:
        cumulative += op.get('pnl', 0.0)
        profit_history.append({
            'timestamp': op['timestamp'],
            'profit': op.get('pnl', 0.0),
            'cumulative': cumulative
        })
    
    return profit_history


@router.get("/history")
async def get_arbitrage_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500),
    symbol: Optional[str] = None,
    exchange: Optional[str] = None
) -> Dict:
    """
    Get arbitrage operation history
    
    Returns:
        Paginated list of operations
    """
    bridge = get_bridge()
    
    operations = bridge.get_operations(limit=limit)
    
    # Filter by symbol/exchange if specified
    if symbol:
        operations = [op for op in operations if op.get('symbol') == symbol]
    
    if exchange:
        operations = [op for op in operations 
                     if op.get('exchange_buy') == exchange or op.get('exchange_sell') == exchange]
    
    return {
        'operations': operations,
        'total': len(operations),
        'page': 1,
        'per_page': limit
    }


@router.get("/history/export")
async def export_arbitrage_history(
    current_user: User = Depends(get_current_user)
):
    """
    Export arbitrage history as CSV
    
    Returns:
        CSV file download
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    bridge = get_bridge()
    operations = bridge.get_operations(limit=1000)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'timestamp', 'type', 'strategy', 'symbol', 
        'exchange_buy', 'exchange_sell', 'quantity',
        'entry_price', 'exit_price', 'pnl', 'pnl_percent',
        'spread_bps', 'fees_paid', 'is_open'
    ])
    
    writer.writeheader()
    writer.writerows(operations)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=arbitrage_history_{int(time.time())}.csv"
        }
    )
