"""Add task progress and steps tables.

Revision ID: 12c3d5e7a9b0
Revises: ff4d89c580cc
Create Date: 2025-02-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "12c3d5e7a9b0"
down_revision: Union[str, None] = "ff4d89c580cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "task_progress_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.String(length=255), nullable=False),
        sa.Column("task_name", sa.String(length=255), nullable=True),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("step_key", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_progress_task_ts",
        "task_progress_events",
        ["task_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        op.f("ix_task_progress_events_task_name"),
        "task_progress_events",
        ["task_name"],
        unique=False,
    )

    op.create_table(
        "task_progress_latest",
        sa.Column("task_id", sa.String(length=255), primary_key=True),
        sa.Column("task_name", sa.String(length=255), nullable=True),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("step_key", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_progress_latest_updated",
        "task_progress_latest",
        ["updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_task_progress_latest_task_name"),
        "task_progress_latest",
        ["task_name"],
        unique=False,
    )

    op.create_table(
        "task_steps",
        sa.Column("task_id", sa.String(length=255), primary_key=True),
        sa.Column("task_name", sa.String(length=255), nullable=True),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("defined_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_task_steps_defined",
        "task_steps",
        ["defined_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_task_steps_task_name"),
        "task_steps",
        ["task_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_task_steps_defined", table_name="task_steps")
    op.drop_index(op.f("ix_task_steps_task_name"), table_name="task_steps")
    op.drop_table("task_steps")

    op.drop_index("idx_progress_latest_updated", table_name="task_progress_latest")
    op.drop_index(op.f("ix_task_progress_latest_task_name"), table_name="task_progress_latest")
    op.drop_table("task_progress_latest")

    op.drop_index("idx_progress_task_ts", table_name="task_progress_events")
    op.drop_index(op.f("ix_task_progress_events_task_name"), table_name="task_progress_events")
    op.drop_table("task_progress_events")
