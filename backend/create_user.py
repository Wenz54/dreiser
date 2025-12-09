"""Create first user with portfolio"""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.portfolio import Portfolio
from decimal import Decimal


async def create_first_user():
    """Create admin user with portfolio"""
    
    async with AsyncSessionLocal() as db:
        # Check if user exists
        from sqlalchemy import select
        stmt = select(User).where(User.username == "admin")
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"✅ User already exists: {existing_user.username} ({existing_user.email})")
            print(f"   User ID: {existing_user.id}")
            
            # Check portfolio
            stmt_portfolio = select(Portfolio).where(Portfolio.user_id == existing_user.id)
            result_portfolio = await db.execute(stmt_portfolio)
            existing_portfolio = result_portfolio.scalar_one_or_none()
            
            if existing_portfolio:
                print(f"✅ Portfolio exists: ${existing_portfolio.balance_usd} USD")
            else:
                # Create portfolio
                portfolio = Portfolio(
                    id=uuid.uuid4(),
                    user_id=existing_user.id,
                    balance_usd=Decimal("1000.00"),
                    initial_balance=Decimal("1000.00"),
                    total_pnl=Decimal("0.00"),
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0
                )
                db.add(portfolio)
                await db.commit()
                print(f"✅ Portfolio created: $1000 USD")
            
            return
        
        # Create user
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="admin@draizer.app",
            username="admin",
            password_hash=get_password_hash("Admin123!Secret"),
            is_active=True,
            is_verified=True,
            mfa_enabled=False
        )
        
        db.add(user)
        await db.flush()
        
        # Create portfolio
        portfolio = Portfolio(
            id=uuid.uuid4(),
            user_id=user_id,
            balance_usd=Decimal("1000.00"),
            initial_balance=Decimal("1000.00"),
            total_pnl=Decimal("0.00"),
            total_trades=0,
            winning_trades=0,
            losing_trades=0
        )
        
        db.add(portfolio)
        await db.commit()
        
        print("✅ User created:")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Password: Admin123!Secret")
        print(f"✅ Portfolio created:")
        print(f"   ID: {portfolio.id}")
        print(f"   Balance: $1000 USD")


if __name__ == "__main__":
    asyncio.run(create_first_user())

