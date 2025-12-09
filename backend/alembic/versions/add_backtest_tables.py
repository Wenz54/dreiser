"""add backtest tables

Revision ID: backtest_001
Revises: 
Create Date: 2025-10-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'backtest_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create orderbook_snapshots table
    op.create_table(
        'orderbook_snapshots',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('exchange', sa.String(length=20), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('bid', sa.Float(), nullable=False),
        sa.Column('ask', sa.Float(), nullable=False),
        sa.Column('bid_quantity', sa.Float(), nullable=True),
        sa.Column('ask_quantity', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('timestamp_ns', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_exchange', 'orderbook_snapshots', ['exchange'])
    op.create_index('idx_symbol', 'orderbook_snapshots', ['symbol'])
    op.create_index('idx_timestamp', 'orderbook_snapshots', ['timestamp'])
    op.create_index('idx_symbol_timestamp', 'orderbook_snapshots', ['symbol', 'timestamp'])
    op.create_index('idx_exchange_symbol_timestamp', 'orderbook_snapshots', ['exchange', 'symbol', 'timestamp'])
    
    # Create backtest_results table
    op.create_table(
        'backtest_results',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('symbols', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('exchanges', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('min_spread_bps', sa.Float(), nullable=False),
        sa.Column('fee_bps', sa.Float(), nullable=False),
        sa.Column('slippage_bps', sa.Float(), nullable=False),
        sa.Column('total_opportunities', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('opportunities_per_minute', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('avg_spread_bps', sa.Float(), nullable=True),
        sa.Column('min_spread_bps_found', sa.Float(), nullable=True),
        sa.Column('max_spread_bps_found', sa.Float(), nullable=True),
        sa.Column('median_spread_bps', sa.Float(), nullable=True),
        sa.Column('total_potential_profit_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('avg_profit_per_trade_usd', sa.Float(), nullable=True),
        sa.Column('best_trade_profit_usd', sa.Float(), nullable=True),
        sa.Column('avg_opportunity_lifetime_ms', sa.Float(), nullable=True),
        sa.Column('symbol_stats', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_start_time', 'backtest_results', ['start_time'])


def downgrade():
    op.drop_table('backtest_results')
    op.drop_table('orderbook_snapshots')





