"""change audits id to uuid string

Revision ID: 9c54bce0c2e0
Revises: 51c802d33f74
Create Date: 2026-01-30 03:43:28.220718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c54bce0c2e0'
down_revision: Union[str, Sequence[str], None] = '51c802d33f74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
