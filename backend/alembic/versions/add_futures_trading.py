"""add futures trading

Revision ID: futures_001
Revises: performance_score_001
Create Date: 2025-10-24 08:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'futures_001'
down_revision: Union[str, None] = 'performance_score_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Обновить комментарии для balance (теперь это единый баланс)
    op.alter_column('portfolios', 'balance_usd', 
                    comment='Total balance (spot + futures margin)')
    op.alter_column('portfolios', 'total_pnl',
                    comment='Total P&L (spot + futures)')
    
    # Создать таблицу futures_positions
    op.create_table('futures_positions',
    sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False, comment='e.g. BTCUSDT'),
    sa.Column('side', sa.String(length=10), nullable=False, comment='LONG or SHORT'),
    sa.Column('entry_price', sa.DECIMAL(precision=20, scale=8), nullable=False, comment='Entry price'),
    sa.Column('quantity', sa.DECIMAL(precision=20, scale=8), nullable=False, comment='Position size'),
    sa.Column('leverage', sa.Integer(), nullable=False, server_default='3', comment='Leverage (default 3x)'),
    sa.Column('current_price', sa.DECIMAL(precision=20, scale=8), nullable=True, comment='Last known price'),
    sa.Column('unrealized_pnl', sa.DECIMAL(precision=20, scale=8), nullable=True, server_default='0', comment='Current P&L'),
    sa.Column('liquidation_price', sa.DECIMAL(precision=20, scale=8), nullable=True, comment='Liquidation price'),
    sa.Column('is_closed', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('exit_price', sa.DECIMAL(precision=20, scale=8), nullable=True, comment='Exit price when closed'),
    sa.Column('realized_pnl', sa.DECIMAL(precision=20, scale=8), nullable=True, comment='Final P&L'),
    sa.Column('closed_at', sa.DateTime(), nullable=True),
    sa.Column('is_simulated', sa.Boolean(), nullable=False, server_default='true', comment='Virtual position'),
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_futures_positions_id'), 'futures_positions', ['id'], unique=False)
    
    # Обновить enum для ai_decisions (добавить LONG, SHORT, WAIT)
    # PostgreSQL требует пересоздания enum
    op.execute("ALTER TYPE decisiontype RENAME TO decisiontype_old")
    op.execute("CREATE TYPE decisiontype AS ENUM ('BUY', 'SELL', 'HOLD', 'LONG', 'SHORT', 'WAIT')")
    op.execute("ALTER TABLE ai_decisions ALTER COLUMN decision_type TYPE decisiontype USING decision_type::text::decisiontype")
    op.execute("DROP TYPE decisiontype_old")


def downgrade() -> None:
    # Удалить futures_positions
    op.drop_index(op.f('ix_futures_positions_id'), table_name='futures_positions')
    op.drop_table('futures_positions')
    
    # Вернуть старые комментарии
    op.alter_column('portfolios', 'balance_usd',
                    comment='Virtual USD balance')
    op.alter_column('portfolios', 'total_pnl',
                    comment='Total simulated P&L')
    
    # Вернуть старый enum
    op.execute("ALTER TYPE decisiontype RENAME TO decisiontype_old")
    op.execute("CREATE TYPE decisiontype AS ENUM ('BUY', 'SELL', 'HOLD')")
    op.execute("ALTER TABLE ai_decisions ALTER COLUMN decision_type TYPE decisiontype USING decision_type::text::decisiontype")
    op.execute("DROP TYPE decisiontype_old")

