"""add_user_addresses_table

Revision ID: 5f2c1d8f7a3e
Revises: c8f7a0d5b1f2
Create Date: 2026-03-15 20:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f2c1d8f7a3e'
down_revision = 'c8f7a0d5b1f2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_addresses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('label', sa.String(length=120), nullable=True),
        sa.Column('street', sa.String(length=255), nullable=True),
        sa.Column('street_number', sa.String(length=20), nullable=True),
        sa.Column('neighborhood', sa.String(length=120), nullable=True),
        sa.Column('zip_code', sa.String(length=20), nullable=True),
        sa.Column('apartment', sa.String(length=80), nullable=True),
        sa.Column('complement', sa.String(length=120), nullable=True),
        sa.Column('city', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('user_addresses')
