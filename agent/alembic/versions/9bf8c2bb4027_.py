"""empty message

Revision ID: 9bf8c2bb4027
Revises: a1b2c3d4e5f6, c0a2f2d2fe85
Create Date: 2025-10-25 13:47:15.082277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9bf8c2bb4027'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'c0a2f2d2fe85')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
