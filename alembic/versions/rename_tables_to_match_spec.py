"""Rename tables to match specification: user_profiles -> UserProfile, user_defaults -> UserDefaults, user_settings -> UserSettings

Revision ID: rename_tables_spec
Revises: add_phone_avatar
Create Date: 2025-12-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_tables_spec'
down_revision = 'add_phone_avatar'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename user_profiles to UserProfile
    op.rename_table('user_profiles', 'UserProfile')
    
    # Rename user_defaults to UserDefaults
    op.rename_table('user_defaults', 'UserDefaults')
    
    # Rename user_settings to UserSettings
    op.rename_table('user_settings', 'UserSettings')


def downgrade() -> None:
    # Rename UserProfile back to user_profiles
    op.rename_table('UserProfile', 'user_profiles')
    
    # Rename UserDefaults back to user_defaults
    op.rename_table('UserDefaults', 'user_defaults')
    
    # Rename UserSettings back to user_settings
    op.rename_table('UserSettings', 'user_settings')
