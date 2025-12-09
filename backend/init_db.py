"""Initialize database - create all tables"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base import Base
from app.core.config import settings

# Import all models to register them with Base
from app.models.user import User  # noqa: F401
from app.models.portfolio import Portfolio  # noqa: F401
from app.models.position import Position  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.ai_decision import AIDecision  # noqa: F401
from app.models.market_data import MarketDataCache  # noqa: F401
from app.models.chat_message import ChatMessage  # noqa: F401
from app.models.news_summary import NewsSummary  # noqa: F401
from app.models.deepseek_context import DeepSeekContext  # noqa: F401
from app.models.security_audit import SecurityAuditLog, APIKeyRotation  # noqa: F401
from app.models.performance_log import PerformanceLog  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.security_event import SecurityEvent  # noqa: F401
from app.models.ai_session import AITradingSession  # noqa: F401


async def init_db():
    """Create all tables in the database"""
    print(f"🔗 Connecting to: {settings.DATABASE_URL}")
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        pool_pre_ping=True
    )
    
    print("📦 Creating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ All tables created successfully!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())

