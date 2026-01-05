"""update audits table

Revision ID: b7c55379b332
Revises: f28547774cfd
Create Date: 2026-01-03 01:37:01.462628

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c55379b332'
down_revision: Union[str, Sequence[str], None] = 'f28547774cfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("audits") as batch_op:
        batch_op.alter_column(
            "event_type",
            existing_type=sa.VARCHAR(length=100),
            type_=sa.String(length=100),  # SQLite-safe
            nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("audits") as batch_op:
        batch_op.alter_column(
            "event_type",
            existing_type=sa.String(length=100),
            type_=sa.String(length=100),
            nullable=False,
        )