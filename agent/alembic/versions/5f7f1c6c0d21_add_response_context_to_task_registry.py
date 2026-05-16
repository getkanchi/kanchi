"""add response context to task registry

Revision ID: 5f7f1c6c0d21
Revises: 930bf786783a
Create Date: 2026-04-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f7f1c6c0d21"
down_revision: Union[str, None] = "930bf786783a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("task_registry", sa.Column("runbook_url", sa.String(length=2048), nullable=True))
    op.add_column("task_registry", sa.Column("severity_default", sa.String(length=32), nullable=True))
    op.add_column("task_registry", sa.Column("response_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("task_registry", "response_notes")
    op.drop_column("task_registry", "severity_default")
    op.drop_column("task_registry", "runbook_url")
