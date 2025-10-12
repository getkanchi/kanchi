"""merge heads

Revision ID: 6de4dae5ae09
Revises: 1eaba5f8ab12, d9f3a1e5c2b8
Create Date: 2025-10-12 09:19:22.764979

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6de4dae5ae09'
down_revision: Union[str, None] = ('1eaba5f8ab12', 'd9f3a1e5c2b8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
