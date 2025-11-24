"""empty message

Revision ID: ff4d89c580cc
Revises: 43d4f43f63e5, aa2f5bfc1d02
Create Date: 2025-11-23 13:32:21.343501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff4d89c580cc'
down_revision: Union[str, None] = ('43d4f43f63e5', 'aa2f5bfc1d02')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
