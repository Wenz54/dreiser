"""
DRAIZER V2 API - Operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

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


@router.get("/latest")
async def get_latest_operations(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500)
) -> List[Dict]:
    """
    Get latest operations from C-engine
    
    Args:
        limit: Max number of operations to return
    
    Returns:
        List of recent operations
    """
    bridge = get_bridge()
    
    operations = bridge.get_operations(limit=limit)
    
    return operations


@router.get("/stats")
async def get_operations_stats(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get aggregated operations statistics
    
    Returns:
        Stats summary
    """
    bridge = get_bridge()
    
    stats = bridge.get_stats()
    if not stats:
        return {
            'total_operations': 0,
            'total_profit': 0.0,
            'avg_profit_per_operation': 0.0,
            'win_rate': 0.0,
            'best_symbol': None,
            'worst_symbol': None
        }
    
    # Get recent operations for detailed stats
    operations = bridge.get_operations(limit=100)
    
    if not operations:
        return {
            'total_operations': 0,
            'total_profit': 0.0,
            'avg_profit_per_operation': 0.0,
            'win_rate': 0.0,
            'best_symbol': None,
            'worst_symbol': None
        }
    
    # Calculate stats
    total_profit = sum(op['pnl'] for op in operations)
    wins = sum(1 for op in operations if op['pnl'] > 0)
    
    # Find best/worst symbols
    symbol_profits = {}
    for op in operations:
        symbol = op['symbol']
        if symbol not in symbol_profits:
            symbol_profits[symbol] = 0.0
        symbol_profits[symbol] += op['pnl']
    
    best_symbol = max(symbol_profits.items(), key=lambda x: x[1])[0] if symbol_profits else None
    worst_symbol = min(symbol_profits.items(), key=lambda x: x[1])[0] if symbol_profits else None
    
    return {
        'total_operations': len(operations),
        'total_profit': total_profit,
        'avg_profit_per_operation': total_profit / len(operations) if operations else 0.0,
        'win_rate': (wins / len(operations) * 100) if operations else 0.0,
        'best_symbol': best_symbol,
        'worst_symbol': worst_symbol
    }
