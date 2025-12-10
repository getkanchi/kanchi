"""add app settings table for configurable options

Revision ID: 0b16d5b0d4a3
Revises: ff4d89c580cc
Create Date: 2025-02-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b16d5b0d4a3'
down_revision: Union[str, None] = 'ff4d89c580cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'app_settings',
        sa.Column('key', sa.String(length=255), primary_key=True),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('value_type', sa.String(length=50), nullable=False, server_default='string'),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('idx_app_settings_category', 'app_settings', ['category'])
    op.create_index('idx_app_settings_updated_at', 'app_settings', ['updated_at'])


def downgrade() -> None:
    op.drop_index('idx_app_settings_updated_at', table_name='app_settings')
    op.drop_index('idx_app_settings_category', table_name='app_settings')
    op.drop_table('app_settings')
