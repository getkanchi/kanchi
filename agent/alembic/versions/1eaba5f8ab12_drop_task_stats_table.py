"""drop_task_stats_table

Revision ID: 1eaba5f8ab12
Revises: 8ff8ccaebcba

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1eaba5f8ab12'
down_revision: Union[str, None] = '8ff8ccaebcba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the task_stats table (replaced by task_daily_stats)
    op.drop_table('task_stats')


def downgrade() -> None:
    # Recreate task_stats table if needed
    op.create_table(
        'task_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('total_tasks', sa.Integer(), nullable=True),
        sa.Column('succeeded', sa.Integer(), nullable=True),
        sa.Column('failed', sa.Integer(), nullable=True),
        sa.Column('pending', sa.Integer(), nullable=True),
        sa.Column('retried', sa.Integer(), nullable=True),
        sa.Column('active', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
