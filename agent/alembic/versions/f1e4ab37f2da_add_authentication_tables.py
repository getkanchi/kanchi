"""Add user authentication tables and columns

Revision ID: f1e4ab37f2da
Revises: c0a2f2d2fe85
Create Date: 2025-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1e4ab37f2da'
down_revision: Union[str, None] = 'c0a2f2d2fe85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_account_id', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_account_id', name='uq_users_provider_account'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_provider_email', 'users', ['provider', 'email'], unique=False)

    op.add_column('user_sessions', sa.Column('user_id', sa.String(length=36), nullable=True))
    op.add_column('user_sessions', sa.Column('auth_provider', sa.String(length=50), nullable=True))
    op.add_column('user_sessions', sa.Column('access_token_hash', sa.String(length=128), nullable=True))
    op.add_column('user_sessions', sa.Column('refresh_token_hash', sa.String(length=128), nullable=True))
    op.add_column('user_sessions', sa.Column('access_token_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_sessions', sa.Column('refresh_token_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_sessions', sa.Column('token_scopes', sa.JSON(), nullable=True))

    with op.batch_alter_table('user_sessions', recreate='always') as batch_op:
        batch_op.create_foreign_key(
            'fk_user_sessions_user_id_users',
            referent_table='users',
            local_cols=['user_id'],
            remote_cols=['id'],
            ondelete='SET NULL',
        )

    op.create_index('idx_session_user', 'user_sessions', ['user_id'], unique=False)
    op.create_index('ix_user_sessions_access_token_hash', 'user_sessions', ['access_token_hash'], unique=False)
    op.create_index('ix_user_sessions_refresh_token_hash', 'user_sessions', ['refresh_token_hash'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_user_sessions_refresh_token_hash', table_name='user_sessions')
    op.drop_index('ix_user_sessions_access_token_hash', table_name='user_sessions')
    op.drop_index('idx_session_user', table_name='user_sessions')

    with op.batch_alter_table('user_sessions', recreate='always') as batch_op:
        batch_op.drop_constraint('fk_user_sessions_user_id_users', type_='foreignkey')
        batch_op.drop_column('token_scopes')
        batch_op.drop_column('refresh_token_expires_at')
        batch_op.drop_column('access_token_expires_at')
        batch_op.drop_column('refresh_token_hash')
        batch_op.drop_column('access_token_hash')
        batch_op.drop_column('auth_provider')
        batch_op.drop_column('user_id')

    op.drop_index('idx_users_provider_email', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
