"""Add audit log table for operator and workflow actions.

Revision ID: 97a4e6d2c1ab
Revises: 930bf786783a
Create Date: 2026-04-30 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "97a4e6d2c1ab"
down_revision: Union[str, None] = "930bf786783a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("actor_name", sa.String(length=255), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=False),
        sa.Column("target_label", sa.String(length=255), nullable=True),
        sa.Column("task_id", sa.String(length=255), nullable=True),
        sa.Column("related_task_id", sa.String(length=255), nullable=True),
        sa.Column("workflow_id", sa.String(length=36), nullable=True),
        sa.Column("execution_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
    )

    op.create_index(op.f("ix_audit_logs_timestamp"), "audit_logs", ["timestamp"], unique=False)
    op.create_index(op.f("ix_audit_logs_source"), "audit_logs", ["source"], unique=False)
    op.create_index(op.f("ix_audit_logs_action_type"), "audit_logs", ["action_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_status"), "audit_logs", ["status"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_id"), "audit_logs", ["actor_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_name"), "audit_logs", ["actor_name"], unique=False)
    op.create_index(op.f("ix_audit_logs_target_type"), "audit_logs", ["target_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_target_id"), "audit_logs", ["target_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_target_label"), "audit_logs", ["target_label"], unique=False)
    op.create_index(op.f("ix_audit_logs_task_id"), "audit_logs", ["task_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_related_task_id"), "audit_logs", ["related_task_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_workflow_id"), "audit_logs", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_execution_id"), "audit_logs", ["execution_id"], unique=False)
    op.create_index("idx_audit_timestamp_id", "audit_logs", ["timestamp", "id"], unique=False)
    op.create_index(
        "idx_audit_target_lookup",
        "audit_logs",
        ["target_type", "target_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        "idx_audit_task_lookup",
        "audit_logs",
        ["task_id", "related_task_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        "idx_audit_workflow_lookup",
        "audit_logs",
        ["workflow_id", "timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_audit_workflow_lookup", table_name="audit_logs")
    op.drop_index("idx_audit_task_lookup", table_name="audit_logs")
    op.drop_index("idx_audit_target_lookup", table_name="audit_logs")
    op.drop_index("idx_audit_timestamp_id", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_execution_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_workflow_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_related_task_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_task_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_target_label"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_target_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_target_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_name"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_status"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_source"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_timestamp"), table_name="audit_logs")
    op.drop_table("audit_logs")
