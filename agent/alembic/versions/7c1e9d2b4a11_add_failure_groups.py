"""add failure grouping metadata

Revision ID: 7c1e9d2b4a11
Revises: d927bf6ca0c2, ff4d89c580cc
Create Date: 2026-04-29 19:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '7c1e9d2b4a11'
down_revision: Union[str, Sequence[str], None] = ('d927bf6ca0c2', 'ff4d89c580cc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('task_events', sa.Column('failure_fingerprint', sa.String(length=64), nullable=True))
    op.add_column('task_events', sa.Column('failure_group_id', sa.String(length=64), nullable=True))
    op.add_column('task_events', sa.Column('environment', sa.String(length=255), nullable=True))
    op.create_index('ix_task_events_failure_fingerprint', 'task_events', ['failure_fingerprint'])
    op.create_index('ix_task_events_failure_group_id', 'task_events', ['failure_group_id'])
    op.create_index('ix_task_events_environment', 'task_events', ['environment'])

    op.add_column('task_latest', sa.Column('failure_fingerprint', sa.String(length=64), nullable=True))
    op.add_column('task_latest', sa.Column('failure_group_id', sa.String(length=64), nullable=True))
    op.add_column('task_latest', sa.Column('environment', sa.String(length=255), nullable=True))
    op.create_index('ix_task_latest_failure_fingerprint', 'task_latest', ['failure_fingerprint'])
    op.create_index('ix_task_latest_failure_group_id', 'task_latest', ['failure_group_id'])
    op.create_index('ix_task_latest_environment', 'task_latest', ['environment'])
    op.create_index('idx_task_latest_failure_group_ts', 'task_latest', ['failure_group_id', 'timestamp'])

    op.create_table(
        'failure_groups',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('fingerprint', sa.String(length=64), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('exception_fingerprint', sa.Text(), nullable=True),
        sa.Column('queue', sa.String(length=255), nullable=True),
        sa.Column('hostname', sa.String(length=255), nullable=True),
        sa.Column('environment', sa.String(length=255), nullable=True),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_task_id', sa.String(length=255), nullable=False),
    )
    op.create_index('ix_failure_groups_fingerprint', 'failure_groups', ['fingerprint'])
    op.create_index('ix_failure_groups_task_name', 'failure_groups', ['task_name'])
    op.create_index('ix_failure_groups_queue', 'failure_groups', ['queue'])
    op.create_index('ix_failure_groups_hostname', 'failure_groups', ['hostname'])
    op.create_index('ix_failure_groups_environment', 'failure_groups', ['environment'])
    op.create_index('ix_failure_groups_last_task_id', 'failure_groups', ['last_task_id'])
    op.create_index('idx_failure_groups_last_seen', 'failure_groups', ['last_seen'])
    op.create_index('idx_failure_groups_task_name', 'failure_groups', ['task_name', 'last_seen'])


def downgrade() -> None:
    op.drop_index('idx_failure_groups_task_name', table_name='failure_groups')
    op.drop_index('idx_failure_groups_last_seen', table_name='failure_groups')
    op.drop_index('ix_failure_groups_last_task_id', table_name='failure_groups')
    op.drop_index('ix_failure_groups_environment', table_name='failure_groups')
    op.drop_index('ix_failure_groups_hostname', table_name='failure_groups')
    op.drop_index('ix_failure_groups_queue', table_name='failure_groups')
    op.drop_index('ix_failure_groups_task_name', table_name='failure_groups')
    op.drop_index('ix_failure_groups_fingerprint', table_name='failure_groups')
    op.drop_table('failure_groups')

    op.drop_index('idx_task_latest_failure_group_ts', table_name='task_latest')
    op.drop_index('ix_task_latest_environment', table_name='task_latest')
    op.drop_index('ix_task_latest_failure_group_id', table_name='task_latest')
    op.drop_index('ix_task_latest_failure_fingerprint', table_name='task_latest')
    op.drop_column('task_latest', 'environment')
    op.drop_column('task_latest', 'failure_group_id')
    op.drop_column('task_latest', 'failure_fingerprint')

    op.drop_index('ix_task_events_environment', table_name='task_events')
    op.drop_index('ix_task_events_failure_group_id', table_name='task_events')
    op.drop_index('ix_task_events_failure_fingerprint', table_name='task_events')
    op.drop_column('task_events', 'environment')
    op.drop_column('task_events', 'failure_group_id')
    op.drop_column('task_events', 'failure_fingerprint')
