"""Add performance indexes

Revision ID: 29ae0acdc50e
Revises: 7fd9930ce8a0
Create Date: 2026-06-25 23:54:56.145490

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29ae0acdc50e'
down_revision: Union[str, Sequence[str], None] = '7fd9930ce8a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
