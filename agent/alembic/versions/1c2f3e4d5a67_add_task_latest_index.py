"""Add composite index for latest task lookup

Revision ID: 1c2f3e4d5a67
Revises: f1e4ab37f2da
Create Date: 2025-02-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1c2f3e4d5a67'
down_revision: Union[str, None] = 'f1e4ab37f2da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'idx_task_latest_lookup',
        'task_events',
        ['task_id', 'timestamp', 'id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('idx_task_latest_lookup', table_name='task_events')

