"""change audits id to string

Revision ID: 06dea7f83838
Revises: 77ff9f8c925d
Create Date: 2026-01-30 03:47:35.338343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06dea7f83838'
down_revision: Union[str, Sequence[str], None] = '77ff9f8c925d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'audits',
        'id',
        existing_type=sa.Integer(),
        type_=sa.String(length=36),
        existing_nullable=False,
        postgresql_using='id::text',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'audits',
        'id',
        existing_type=sa.String(length=36),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using='id::integer',
    )
