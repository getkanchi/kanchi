"""add task annotations

Revision ID: b4f2c8d9e103
Revises: 930bf786783a
Create Date: 2026-05-01 09:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4f2c8d9e103'
down_revision: Union[str, None] = '930bf786783a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'task_annotations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('operator', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_annotations_task_id'), 'task_annotations', ['task_id'], unique=False)
    op.create_index('idx_task_annotations_task_created', 'task_annotations', ['task_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_task_annotations_task_created', table_name='task_annotations')
    op.drop_index(op.f('ix_task_annotations_task_id'), table_name='task_annotations')
    op.drop_table('task_annotations')
