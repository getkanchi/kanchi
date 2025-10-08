"""Add timezone support to DateTime columns

Revision ID: 2aad51a773a9
Revises: e41432b7c746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2aad51a773a9'
down_revision: Union[str, None] = 'e41432b7c746'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # For SQLite: Update existing timestamps to include UTC timezone suffix
    # This converts naive timestamps like "2025-10-07 07:38:20.476623"
    # to timezone-aware format "2025-10-07 07:38:20.476623+00:00"
    if conn.dialect.name == 'sqlite':
        conn.execute(sa.text("""
            UPDATE task_events
            SET timestamp = timestamp || '+00:00'
            WHERE timestamp NOT LIKE '%+%' AND timestamp NOT LIKE '%-__:__'
        """))

        conn.execute(sa.text("""
            UPDATE task_events
            SET orphaned_at = orphaned_at || '+00:00'
            WHERE orphaned_at IS NOT NULL
              AND orphaned_at NOT LIKE '%+%'
              AND orphaned_at NOT LIKE '%-__:__'
        """))

        conn.execute(sa.text("""
            UPDATE worker_events
            SET timestamp = timestamp || '+00:00'
            WHERE timestamp NOT LIKE '%+%' AND timestamp NOT LIKE '%-__:__'
        """))

        conn.execute(sa.text("""
            UPDATE task_stats
            SET last_updated = last_updated || '+00:00'
            WHERE last_updated IS NOT NULL
              AND last_updated NOT LIKE '%+%'
              AND last_updated NOT LIKE '%-__:__'
        """))

        conn.execute(sa.text("""
            UPDATE retry_relationships
            SET created_at = created_at || '+00:00',
                updated_at = updated_at || '+00:00'
            WHERE created_at NOT LIKE '%+%' AND created_at NOT LIKE '%-__:__'
        """))


def downgrade() -> None:
    conn = op.get_bind()

    # For SQLite: Remove UTC timezone suffix from timestamps
    if conn.dialect.name == 'sqlite':
        conn.execute(sa.text("""
            UPDATE task_events
            SET timestamp = REPLACE(timestamp, '+00:00', '')
        """))

        conn.execute(sa.text("""
            UPDATE task_events
            SET orphaned_at = REPLACE(orphaned_at, '+00:00', '')
            WHERE orphaned_at IS NOT NULL
        """))

        conn.execute(sa.text("""
            UPDATE worker_events
            SET timestamp = REPLACE(timestamp, '+00:00', '')
        """))

        conn.execute(sa.text("""
            UPDATE task_stats
            SET last_updated = REPLACE(last_updated, '+00:00', '')
            WHERE last_updated IS NOT NULL
        """))

        conn.execute(sa.text("""
            UPDATE retry_relationships
            SET created_at = REPLACE(created_at, '+00:00', ''),
                updated_at = REPLACE(updated_at, '+00:00', '')
        """))
