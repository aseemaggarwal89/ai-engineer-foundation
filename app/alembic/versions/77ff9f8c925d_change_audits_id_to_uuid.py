"""change audits id to uuid

Revision ID: 77ff9f8c925d
Revises: 9c54bce0c2e0
Create Date: 2026-01-30 03:46:27.327689

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77ff9f8c925d'
down_revision: Union[str, Sequence[str], None] = '9c54bce0c2e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
