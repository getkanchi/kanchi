"""Add task_latest snapshot table for fast aggregated queries

Revision ID: aa2f5bfc1d02
Revises: 1c2f3e4d5a67
Create Date: 2025-02-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "aa2f5bfc1d02"
down_revision: Union[str, None] = "1c2f3e4d5a67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LATEST_COLUMNS = [
    "task_id",
    "event_id",
    "task_name",
    "event_type",
    "timestamp",
    "hostname",
    "worker_name",
    "queue",
    "exchange",
    "routing_key",
    "root_id",
    "parent_id",
    "args",
    "kwargs",
    "retries",
    "eta",
    "expires",
    "result",
    "runtime",
    "exception",
    "traceback",
    "retry_of",
    "retried_by",
    "is_retry",
    "has_retries",
    "retry_count",
    "is_orphan",
    "orphaned_at",
]


def upgrade() -> None:
    op.create_table(
        "task_latest",
        sa.Column("task_id", sa.String(length=255), primary_key=True),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("task_name", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("worker_name", sa.String(length=255), nullable=True),
        sa.Column("queue", sa.String(length=255), nullable=True),
        sa.Column("exchange", sa.String(length=255), nullable=True),
        sa.Column("routing_key", sa.String(length=255), nullable=True),
        sa.Column("root_id", sa.String(length=255), nullable=True),
        sa.Column("parent_id", sa.String(length=255), nullable=True),
        sa.Column("args", sa.JSON(), nullable=True),
        sa.Column("kwargs", sa.JSON(), nullable=True),
        sa.Column("retries", sa.Integer(), nullable=True),
        sa.Column("eta", sa.String(length=50), nullable=True),
        sa.Column("expires", sa.String(length=50), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("runtime", sa.Float(), nullable=True),
        sa.Column("exception", sa.Text(), nullable=True),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column("retry_of", sa.String(length=255), nullable=True),
        sa.Column("retried_by", sa.Text(), nullable=True),
        sa.Column("is_retry", sa.Boolean(), nullable=True),
        sa.Column("has_retries", sa.Boolean(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=True),
        sa.Column("is_orphan", sa.Boolean(), nullable=True),
        sa.Column("orphaned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_task_latest_timestamp",
        "task_latest",
        ["timestamp", "task_id"],
        unique=False,
    )
    op.create_index(
        "idx_task_latest_hostname_ts",
        "task_latest",
        ["hostname", "timestamp"],
        unique=False,
    )
    op.create_index(
        "idx_task_latest_routing_ts",
        "task_latest",
        ["routing_key", "timestamp"],
        unique=False,
    )
    op.create_index(
        "idx_task_latest_event_type_ts",
        "task_latest",
        ["event_type", "timestamp"],
        unique=False,
    )

    bind = op.get_bind()
    dialect = bind.dialect.name

    column_list = ", ".join(LATEST_COLUMNS)

    if dialect == "postgresql":
        op.execute(
            sa.text(
                f"""
                INSERT INTO task_latest ({column_list})
                SELECT DISTINCT ON (te.task_id)
                    te.task_id,
                    te.id AS event_id,
                    te.task_name,
                    te.event_type,
                    te.timestamp,
                    te.hostname,
                    te.worker_name,
                    te.queue,
                    te.exchange,
                    te.routing_key,
                    te.root_id,
                    te.parent_id,
                    te.args,
                    te.kwargs,
                    te.retries,
                    te.eta,
                    te.expires,
                    te.result,
                    te.runtime,
                    te.exception,
                    te.traceback,
                    te.retry_of,
                    te.retried_by,
                    te.is_retry,
                    te.has_retries,
                    te.retry_count,
                    te.is_orphan,
                    te.orphaned_at
                FROM task_events te
                ORDER BY te.task_id, te.timestamp DESC, te.id DESC
                """
            )
        )
    else:
        # SQLite and other dialects fallback using a grouped subquery
        op.execute(
            sa.text(
                f"""
                INSERT INTO task_latest ({column_list})
                SELECT
                    te.task_id,
                    te.id AS event_id,
                    te.task_name,
                    te.event_type,
                    te.timestamp,
                    te.hostname,
                    te.worker_name,
                    te.queue,
                    te.exchange,
                    te.routing_key,
                    te.root_id,
                    te.parent_id,
                    te.args,
                    te.kwargs,
                    te.retries,
                    te.eta,
                    te.expires,
                    te.result,
                    te.runtime,
                    te.exception,
                    te.traceback,
                    te.retry_of,
                    te.retried_by,
                    te.is_retry,
                    te.has_retries,
                    te.retry_count,
                    te.is_orphan,
                    te.orphaned_at
                FROM task_events te
                JOIN (
                    SELECT task_id, MAX(timestamp) AS max_ts, MAX(id) AS max_id
                    FROM task_events
                    GROUP BY task_id
                ) latest
                ON te.task_id = latest.task_id
                AND te.timestamp = latest.max_ts
                AND te.id = latest.max_id
                """
            )
        )


def downgrade() -> None:
    op.drop_index("idx_task_latest_event_type_ts", table_name="task_latest")
    op.drop_index("idx_task_latest_routing_ts", table_name="task_latest")
    op.drop_index("idx_task_latest_hostname_ts", table_name="task_latest")
    op.drop_index("idx_task_latest_timestamp", table_name="task_latest")
    op.drop_table("task_latest")
