"""Add phone and avatar columns to user_profiles table

Revision ID: add_phone_avatar
Revises: update_timezone_to_utc8
Create Date: 2025-12-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_phone_avatar'
down_revision = 'update_timezone_to_utc8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add phone column to user_profiles
    op.add_column('user_profiles', sa.Column('phone', sa.String(), nullable=True))
    # Add avatar column to user_profiles
    op.add_column('user_profiles', sa.Column('avatar', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove avatar column from user_profiles
    op.drop_column('user_profiles', 'avatar')
    # Remove phone column from user_profiles
    op.drop_column('user_profiles', 'phone')
