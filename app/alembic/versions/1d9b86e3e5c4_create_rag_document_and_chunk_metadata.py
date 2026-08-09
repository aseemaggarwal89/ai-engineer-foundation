"""create rag document and chunk metadata

Revision ID: 1d9b86e3e5c4
Revises: 06dea7f83838
Create Date: 2026-08-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1d9b86e3e5c4"
down_revision: Union[str, Sequence[str], None] = "06dea7f83838"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


rag_document_status = sa.Enum(
    "received",
    "processing",
    "indexed",
    "failed",
    "deleted",
    name="rag_document_status",
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    rag_document_status.create(bind, checkfirst=True)

    op.create_table(
        "rag_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source", sa.String(length=1000), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("document_version", sa.String(length=100), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            rag_document_status,
            nullable=False,
        ),
        sa.Column("chunking_version", sa.String(length=100), nullable=True),
        sa.Column("embedding_provider", sa.String(length=100), nullable=True),
        sa.Column("embedding_model", sa.String(length=200), nullable=True),
        sa.Column("embedding_version", sa.String(length=100), nullable=True),
        sa.Column("index_version", sa.String(length=100), nullable=True),
        sa.Column("failure_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "document_version",
            name="uq_rag_documents_document_version",
        ),
    )
    op.create_index(
        "ix_rag_documents_document_id",
        "rag_documents",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_rag_documents_document_version",
        "rag_documents",
        ["document_id", "document_version"],
        unique=False,
    )
    op.create_index(
        "ix_rag_documents_checksum",
        "rag_documents",
        ["checksum"],
        unique=False,
    )
    op.create_index(
        "ix_rag_documents_status",
        "rag_documents",
        ["status"],
        unique=False,
    )

    op.create_table(
        "rag_document_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("chunk_id", sa.String(length=128), nullable=False),
        sa.Column("document_pk", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=100), nullable=False),
        sa.Column("document_version", sa.String(length=100), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("chunking_version", sa.String(length=100), nullable=False),
        sa.Column("embedding_provider", sa.String(length=100), nullable=False),
        sa.Column("embedding_model", sa.String(length=200), nullable=False),
        sa.Column("embedding_version", sa.String(length=100), nullable=False),
        sa.Column("index_version", sa.String(length=100), nullable=False),
        sa.Column("section", sa.String(length=500), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "chunk_index >= 0",
            name="ck_rag_document_chunks_index_nonnegative",
        ),
        sa.CheckConstraint(
            "page_number IS NULL OR page_number >= 1",
            name="ck_rag_document_chunks_page_positive",
        ),
        sa.ForeignKeyConstraint(
            ["document_pk"],
            ["rag_documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chunk_id",
            name="uq_rag_document_chunks_chunk_id",
        ),
        sa.UniqueConstraint(
            "document_id",
            "document_version",
            "chunking_version",
            "chunk_index",
            name="uq_rag_document_chunks_position",
        ),
    )
    op.create_index(
        "ix_rag_document_chunks_document_pk",
        "rag_document_chunks",
        ["document_pk"],
        unique=False,
    )
    op.create_index(
        "ix_rag_document_chunks_document_version",
        "rag_document_chunks",
        ["document_id", "document_version"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    op.drop_index(
        "ix_rag_document_chunks_document_version",
        table_name="rag_document_chunks",
    )
    op.drop_index(
        "ix_rag_document_chunks_document_pk",
        table_name="rag_document_chunks",
    )
    op.drop_table("rag_document_chunks")

    op.drop_index("ix_rag_documents_status", table_name="rag_documents")
    op.drop_index("ix_rag_documents_checksum", table_name="rag_documents")
    op.drop_index("ix_rag_documents_document_version", table_name="rag_documents")
    op.drop_index("ix_rag_documents_document_id", table_name="rag_documents")
    op.drop_table("rag_documents")

    rag_document_status.drop(bind, checkfirst=True)
