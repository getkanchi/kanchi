"""Add rerun review audit fields.

Revision ID: c8a4e7d9b123
Revises: b7f8c9d0e1a2
Create Date: 2026-05-20 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8a4e7d9b123"
down_revision: Union[str, None] = "b7f8c9d0e1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "task_action_items",
        sa.Column("attempted_task_id", sa.String(length=255), nullable=True),
    )
    op.add_column("task_action_items", sa.Column("submitted_args", sa.JSON(), nullable=True))
    op.add_column("task_action_items", sa.Column("submitted_kwargs", sa.JSON(), nullable=True))
    op.add_column("task_action_items", sa.Column("rerun_kind", sa.String(length=50), nullable=True))
    op.add_column(
        "task_action_items",
        sa.Column("skip_category", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "task_action_items",
        sa.Column("review_fingerprint", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "task_action_items",
        sa.Column("target_queue", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_task_action_items_attempted_task_id",
        "task_action_items",
        ["attempted_task_id"],
    )
    op.create_index("ix_task_action_items_rerun_kind", "task_action_items", ["rerun_kind"])
    op.create_index("ix_task_action_items_skip_category", "task_action_items", ["skip_category"])


def downgrade() -> None:
    op.drop_index("ix_task_action_items_skip_category", table_name="task_action_items")
    op.drop_index("ix_task_action_items_rerun_kind", table_name="task_action_items")
    op.drop_index("ix_task_action_items_attempted_task_id", table_name="task_action_items")
    op.drop_column("task_action_items", "target_queue")
    op.drop_column("task_action_items", "review_fingerprint")
    op.drop_column("task_action_items", "skip_category")
    op.drop_column("task_action_items", "rerun_kind")
    op.drop_column("task_action_items", "submitted_kwargs")
    op.drop_column("task_action_items", "submitted_args")
    op.drop_column("task_action_items", "attempted_task_id")
