import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.application.ai.rag.domain.document import DocumentStatus
from app.db.db import Base


def _document_status_values(enum_cls):
    return [status.value for status in enum_cls]


class RAGDocumentORM(Base):
    __tablename__ = "rag_documents"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "document_version",
            name="uq_rag_documents_document_version",
        ),
        Index("ix_rag_documents_document_id", "document_id"),
        Index("ix_rag_documents_document_version", "document_id", "document_version"),
        Index("ix_rag_documents_checksum", "checksum"),
        Index("ix_rag_documents_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    document_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    document_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    checksum: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(
            DocumentStatus,
            name="rag_document_status",
            values_callable=_document_status_values,
        ),
        default=DocumentStatus.RECEIVED,
        nullable=False,
    )

    chunking_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    embedding_provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    embedding_model: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    embedding_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    index_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    chunks: Mapped[list["RAGDocumentChunkORM"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class RAGDocumentChunkORM(Base):
    __tablename__ = "rag_document_chunks"

    __table_args__ = (
        UniqueConstraint(
            "chunk_id",
            name="uq_rag_document_chunks_chunk_id",
        ),
        UniqueConstraint(
            "document_id",
            "document_version",
            "chunking_version",
            "chunk_index",
            name="uq_rag_document_chunks_position",
        ),
        CheckConstraint("chunk_index >= 0", name="ck_rag_document_chunks_index_nonnegative"),
        CheckConstraint(
            "page_number IS NULL OR page_number >= 1",
            name="ck_rag_document_chunks_page_positive",
        ),
        Index("ix_rag_document_chunks_document_pk", "document_pk"),
        Index("ix_rag_document_chunks_document_version", "document_id", "document_version"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    chunk_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    document_pk: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    document_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    document_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    chunking_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    embedding_provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    embedding_model: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    embedding_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    index_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    section: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    page_number: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped[RAGDocumentORM] = relationship(
        back_populates="chunks",
    )
