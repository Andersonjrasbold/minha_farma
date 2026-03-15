"""add_user_delivery_address_fields

Revision ID: c8f7a0d5b1f2
Revises: b6f2c1ad4e90
Create Date: 2026-03-15 12:35:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8f7a0d5b1f2'
down_revision = 'b6f2c1ad4e90'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('street', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('street_number', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('neighborhood', sa.String(length=120), nullable=True))
    op.add_column('users', sa.Column('zip_code', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('apartment', sa.String(length=80), nullable=True))
    op.add_column('users', sa.Column('complement', sa.String(length=120), nullable=True))


def downgrade():
    op.drop_column('users', 'complement')
    op.drop_column('users', 'apartment')
    op.drop_column('users', 'zip_code')
    op.drop_column('users', 'neighborhood')
    op.drop_column('users', 'street_number')
    op.drop_column('users', 'street')
