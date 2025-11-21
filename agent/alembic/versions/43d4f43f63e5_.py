"""empty message

Revision ID: 43d4f43f63e5
Revises: 1c2f3e4d5a67, d927bf6ca0c2
Create Date: 2025-11-21 21:55:52.000697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43d4f43f63e5'
down_revision: Union[str, None] = ('1c2f3e4d5a67', 'd927bf6ca0c2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
