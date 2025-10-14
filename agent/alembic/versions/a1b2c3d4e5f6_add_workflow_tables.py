"""Add workflow automation tables

Revision ID: a1b2c3d4e5f6
Revises: 9b011bf1de45
Create Date: 2025-10-13 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9b011bf1de45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('trigger_config', sa.JSON(), nullable=True),
        sa.Column('conditions', sa.JSON(), nullable=True),
        sa.Column('actions', sa.JSON(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('max_executions_per_hour', sa.Integer(), nullable=True),
        sa.Column('cooldown_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('execution_count', sa.Integer(), nullable=True),
        sa.Column('last_executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('success_count', sa.Integer(), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create workflow indexes
    op.create_index('idx_workflows_enabled', 'workflows', ['enabled'])
    op.create_index('idx_workflows_enabled_trigger', 'workflows', ['enabled', 'trigger_type'])
    op.create_index('idx_workflows_priority', 'workflows', ['priority'])
    op.create_index(op.f('ix_workflows_trigger_type'), 'workflows', ['trigger_type'], unique=False)

    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('workflow_id', sa.String(length=36), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('trigger_event', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('actions_executed', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('workflow_snapshot', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create workflow_executions indexes
    op.create_index('idx_workflow_exec_workflow_id', 'workflow_executions', ['workflow_id'])
    op.create_index('idx_workflow_exec_workflow_time', 'workflow_executions', ['workflow_id', 'triggered_at'])
    op.create_index('idx_workflow_exec_status', 'workflow_executions', ['status', 'triggered_at'])
    op.create_index(op.f('ix_workflow_executions_trigger_type'), 'workflow_executions', ['trigger_type'], unique=False)
    op.create_index(op.f('ix_workflow_executions_triggered_at'), 'workflow_executions', ['triggered_at'], unique=False)

    # Create action_configs table
    op.create_table(
        'action_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create action_configs indexes
    op.create_index('idx_action_configs_action_type', 'action_configs', ['action_type'])
    op.create_index('idx_action_configs_name', 'action_configs', ['name'])


def downgrade() -> None:
    # Drop action_configs
    op.drop_index('idx_action_configs_name', table_name='action_configs')
    op.drop_index('idx_action_configs_action_type', table_name='action_configs')
    op.drop_table('action_configs')

    # Drop workflow_executions
    op.drop_index(op.f('ix_workflow_executions_triggered_at'), table_name='workflow_executions')
    op.drop_index(op.f('ix_workflow_executions_trigger_type'), table_name='workflow_executions')
    op.drop_index('idx_workflow_exec_status', table_name='workflow_executions')
    op.drop_index('idx_workflow_exec_workflow_time', table_name='workflow_executions')
    op.drop_index('idx_workflow_exec_workflow_id', table_name='workflow_executions')
    op.drop_table('workflow_executions')

    # Drop workflows
    op.drop_index(op.f('ix_workflows_trigger_type'), table_name='workflows')
    op.drop_index('idx_workflows_priority', table_name='workflows')
    op.drop_index('idx_workflows_enabled_trigger', table_name='workflows')
    op.drop_index('idx_workflows_enabled', table_name='workflows')
    op.drop_table('workflows')
