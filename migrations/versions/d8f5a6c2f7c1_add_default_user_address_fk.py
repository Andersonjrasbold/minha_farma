"""add_default_user_address_fk

Revision ID: d8f5a6c2f7c1
Revises: 5f2c1d8f7a3e
Create Date: 2026-03-15 20:40:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8f5a6c2f7c1'
down_revision = '5f2c1d8f7a3e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('default_address_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_users_default_address_id_user_addresses',
        'users',
        'user_addresses',
        ['default_address_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_users_default_address_id_user_addresses', 'users', type_='foreignkey')
    op.drop_column('users', 'default_address_id')
