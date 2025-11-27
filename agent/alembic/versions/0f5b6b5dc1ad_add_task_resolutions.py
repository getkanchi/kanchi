"""add task resolutions and resolution fields to task_latest

Revision ID: 0f5b6b5dc1ad
Revises: ff4d89c580cc
Create Date: 2026-03-11 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f5b6b5dc1ad'
down_revision: Union[str, None] = 'ff4d89c580cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'task_resolutions',
        sa.Column('task_id', sa.String(length=255), primary_key=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(length=255), nullable=True),
    )
    op.create_index('idx_task_resolved_flag', 'task_resolutions', ['resolved'])

    op.add_column('task_latest', sa.Column('resolved', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('task_latest', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('task_latest', sa.Column('resolved_by', sa.String(length=255), nullable=True))

    # Drop server default after data backfill to avoid future inserts pinning to True/False unexpectedly.
    with op.batch_alter_table('task_resolutions') as batch_op:
        batch_op.alter_column('resolved', server_default=None)
    with op.batch_alter_table('task_latest') as batch_op:
        batch_op.alter_column('resolved', server_default=None)


def downgrade() -> None:
    op.drop_column('task_latest', 'resolved_by')
    op.drop_column('task_latest', 'resolved_at')
    op.drop_column('task_latest', 'resolved')

    op.drop_index('idx_task_resolved_flag', table_name='task_resolutions')
    op.drop_table('task_resolutions')

