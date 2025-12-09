"""add_entry_volume_ratio

Revision ID: entry_vol_001
Revises: futures_001
Create Date: 2025-10-27 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'entry_vol_001'
down_revision = 'performance_log_001'  # Depend on performance_log_001 instead of futures_001
branch_labels = None
depends_on = None


def upgrade():
    # Добавить entry_volume_ratio в positions
    op.add_column('positions', sa.Column('entry_volume_ratio', sa.DECIMAL(10, 2), nullable=True, comment='Volume ratio at entry (5m/avg_15m)'))
    
    # Добавить entry_volume_ratio в futures_positions
    op.add_column('futures_positions', sa.Column('entry_volume_ratio', sa.DECIMAL(10, 2), nullable=True, comment='Volume ratio at entry (5m/avg_15m)'))


def downgrade():
    # Удалить entry_volume_ratio из positions
    op.drop_column('positions', 'entry_volume_ratio')
    
    # Удалить entry_volume_ratio из futures_positions
    op.drop_column('futures_positions', 'entry_volume_ratio')

