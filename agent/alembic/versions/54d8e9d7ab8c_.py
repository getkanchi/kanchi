"""empty message

Revision ID: 54d8e9d7ab8c
Revises: 0b16d5b0d4a3, 0f5b6b5dc1ad
Create Date: 2025-12-06 16:42:03.809938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54d8e9d7ab8c'
down_revision: Union[str, None] = ('0b16d5b0d4a3', '0f5b6b5dc1ad')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
