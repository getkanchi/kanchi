"""Add circuit breaker support for workflows

Revision ID: c0a2f2d2fe85
Revises: 9b011bf1de45
Create Date: 2025-10-25 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0a2f2d2fe85'
down_revision: Union[str, None] = '9b011bf1de45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'


def upgrade() -> None:
    # Add circuit breaker configuration column to workflows
    op.add_column('workflows', sa.Column('circuit_breaker_config', sa.JSON(), nullable=True))

    # Add circuit breaker key tracking to workflow executions
    op.add_column('workflow_executions', sa.Column('circuit_breaker_key', sa.String(length=255), nullable=True))
    op.create_index(
        'idx_workflow_exec_circuit_key',
        'workflow_executions',
        ['workflow_id', 'circuit_breaker_key', 'triggered_at'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_workflow_exec_circuit_key', table_name='workflow_executions')
    op.drop_column('workflow_executions', 'circuit_breaker_key')
    op.drop_column('workflows', 'circuit_breaker_config')
