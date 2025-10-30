"""empty message

Revision ID: d927bf6ca0c2
Revises: 9bf8c2bb4027, f1e4ab37f2da
Create Date: 2025-10-30 08:05:08.218674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd927bf6ca0c2'
down_revision: Union[str, None] = ('9bf8c2bb4027', 'f1e4ab37f2da')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
