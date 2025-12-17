"""Add verification_expires_at column to UserAuth

Revision ID: add_verification_expires_at
Revises: f422668550d1
Create Date: 2025-12-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_verification_expires_at'
down_revision: Union[str, Sequence[str], None] = 'f422668550d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 verification_expires_at 欄位到 UserAuth 表
    op.add_column('UserAuth', sa.Column('verification_expires_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # 移除 verification_expires_at 欄位
    op.drop_column('UserAuth', 'verification_expires_at')
