"""empty message

Revision ID: 930bf786783a
Revises: 12c3d5e7a9b0, 54d8e9d7ab8c
Create Date: 2025-12-13 20:28:27.662199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '930bf786783a'
down_revision: Union[str, None] = ('12c3d5e7a9b0', '54d8e9d7ab8c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
