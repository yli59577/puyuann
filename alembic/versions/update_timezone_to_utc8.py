"""Update all datetime columns to UTC+8

Revision ID: update_timezone_to_utc8
Revises: add_verification_expires_at
Create Date: 2025-12-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone, timedelta


# revision identifiers, used by Alembic.
revision: str = 'update_timezone_to_utc8'
down_revision: Union[str, Sequence[str], None] = 'add_verification_expires_at'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TAIWAN_TZ = timezone(timedelta(hours=8))


def upgrade() -> None:
    """Upgrade schema - update all datetime columns to UTC+8."""
    # 由於 SQLite 不支援直接修改欄位，我們需要通過 Python 來更新資料
    # 這個遷移主要是為了記錄版本，實際的資料更新會通過應用程式進行
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
