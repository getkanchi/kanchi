"""Add user_sessions table for anonymous session management

Revision ID: 9b011bf1de45
Revises: 6de4dae5ae09
Create Date: 2025-10-13 15:18:59.046237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b011bf1de45'
down_revision: Union[str, None] = '6de4dae5ae09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('active_environment_id', sa.String(length=36), nullable=True),
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_active', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('session_id')
    )

    # Create indexes
    op.create_index('idx_session_last_active', 'user_sessions', ['last_active'])
    op.create_index(op.f('ix_user_sessions_active_environment_id'), 'user_sessions', ['active_environment_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_user_sessions_active_environment_id'), table_name='user_sessions')
    op.drop_index('idx_session_last_active', table_name='user_sessions')

    # Drop table
    op.drop_table('user_sessions')
