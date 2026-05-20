"""add task action history tables

Revision ID: b7f8c9d0e1a2
Revises: 930bf786783a
Create Date: 2026-05-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7f8c9d0e1a2'
down_revision: Union[str, None] = '930bf786783a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'task_actions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('initiated_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('initiated_by', sa.String(length=255), nullable=True),
        sa.Column('initiated_session_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('original_task_ids', sa.JSON(), nullable=False),
        sa.Column('selection_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('item_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('item_changed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('item_noop', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('item_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('item_skipped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('item_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('summary', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_task_actions_action_type', 'task_actions', ['action_type'])
    op.create_index('ix_task_actions_status', 'task_actions', ['status'])
    op.create_index('ix_task_actions_initiated_by_user_id', 'task_actions', ['initiated_by_user_id'])
    op.create_index('ix_task_actions_initiated_session_id', 'task_actions', ['initiated_session_id'])
    op.create_index('ix_task_actions_created_at', 'task_actions', ['created_at'])
    op.create_index('ix_task_actions_completed_at', 'task_actions', ['completed_at'])
    op.create_index('idx_task_actions_type_created', 'task_actions', ['action_type', 'created_at'])
    op.create_index('idx_task_actions_session_created', 'task_actions', ['initiated_session_id', 'created_at'])
    op.create_index('idx_task_actions_status_created', 'task_actions', ['status', 'created_at'])

    op.create_table(
        'task_action_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('action_id', sa.String(length=36), nullable=False),
        sa.Column('original_task_id', sa.String(length=255), nullable=False),
        sa.Column('original_task_name', sa.String(length=255), nullable=True),
        sa.Column('outcome', sa.String(length=50), nullable=False),
        sa.Column('reason_code', sa.String(length=100), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('rerun_task_id', sa.String(length=255), nullable=True),
        sa.Column('rerun_task_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['action_id'], ['task_actions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_task_action_items_action_id', 'task_action_items', ['action_id'])
    op.create_index('ix_task_action_items_original_task_id', 'task_action_items', ['original_task_id'])
    op.create_index('ix_task_action_items_outcome', 'task_action_items', ['outcome'])
    op.create_index('ix_task_action_items_rerun_task_id', 'task_action_items', ['rerun_task_id'])
    op.create_index('idx_task_action_items_action_outcome', 'task_action_items', ['action_id', 'outcome'])

    op.create_table(
        'task_rerun_relationships',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('original_task_id', sa.String(length=255), nullable=False),
        sa.Column('rerun_task_id', sa.String(length=255), nullable=False),
        sa.Column('action_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['action_id'], ['task_actions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rerun_task_id'),
    )
    op.create_index('ix_task_rerun_relationships_original_task_id', 'task_rerun_relationships', ['original_task_id'])
    op.create_index('ix_task_rerun_relationships_rerun_task_id', 'task_rerun_relationships', ['rerun_task_id'])
    op.create_index('ix_task_rerun_relationships_action_id', 'task_rerun_relationships', ['action_id'])
    op.create_index('ix_task_rerun_relationships_created_at', 'task_rerun_relationships', ['created_at'])
    op.create_index('idx_task_rerun_original_created', 'task_rerun_relationships', ['original_task_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_task_rerun_original_created', table_name='task_rerun_relationships')
    op.drop_index('ix_task_rerun_relationships_created_at', table_name='task_rerun_relationships')
    op.drop_index('ix_task_rerun_relationships_action_id', table_name='task_rerun_relationships')
    op.drop_index('ix_task_rerun_relationships_rerun_task_id', table_name='task_rerun_relationships')
    op.drop_index('ix_task_rerun_relationships_original_task_id', table_name='task_rerun_relationships')
    op.drop_table('task_rerun_relationships')

    op.drop_index('idx_task_action_items_action_outcome', table_name='task_action_items')
    op.drop_index('ix_task_action_items_rerun_task_id', table_name='task_action_items')
    op.drop_index('ix_task_action_items_outcome', table_name='task_action_items')
    op.drop_index('ix_task_action_items_original_task_id', table_name='task_action_items')
    op.drop_index('ix_task_action_items_action_id', table_name='task_action_items')
    op.drop_table('task_action_items')

    op.drop_index('idx_task_actions_status_created', table_name='task_actions')
    op.drop_index('idx_task_actions_session_created', table_name='task_actions')
    op.drop_index('idx_task_actions_type_created', table_name='task_actions')
    op.drop_index('ix_task_actions_completed_at', table_name='task_actions')
    op.drop_index('ix_task_actions_created_at', table_name='task_actions')
    op.drop_index('ix_task_actions_initiated_session_id', table_name='task_actions')
    op.drop_index('ix_task_actions_initiated_by_user_id', table_name='task_actions')
    op.drop_index('ix_task_actions_status', table_name='task_actions')
    op.drop_index('ix_task_actions_action_type', table_name='task_actions')
    op.drop_table('task_actions')
