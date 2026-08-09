from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint

from app.application.ai.rag.domain.document import DocumentStatus
from app.db.models.rag_document_orm import RAGDocumentChunkORM, RAGDocumentORM


def constraint_names(model, constraint_type):
    return {
        constraint.name
        for constraint in model.__table__.constraints
        if isinstance(constraint, constraint_type)
    }


def index_names(model) -> set[str]:
    return {index.name for index in model.__table__.indexes if isinstance(index, Index)}


def test_rag_document_status_uses_domain_status_values():
    status_column = RAGDocumentORM.__table__.c.status

    assert status_column.type.enums == [status.value for status in DocumentStatus]
    assert status_column.default.arg == DocumentStatus.RECEIVED


def test_rag_document_model_defines_logical_version_identity_and_lookup_indexes():
    assert "uq_rag_documents_document_version" in constraint_names(
        RAGDocumentORM,
        UniqueConstraint,
    )

    indexes = index_names(RAGDocumentORM)

    assert "ix_rag_documents_document_id" in indexes
    assert "ix_rag_documents_document_version" in indexes
    assert "ix_rag_documents_checksum" in indexes
    assert "ix_rag_documents_status" in indexes


def test_rag_document_model_keeps_processing_versions_nullable_until_indexed():
    table = RAGDocumentORM.__table__

    assert table.c.document_id.nullable is False
    assert table.c.document_version.nullable is False
    assert table.c.checksum.nullable is False
    assert table.c.status.nullable is False
    assert table.c.chunking_version.nullable is True
    assert table.c.embedding_provider.nullable is True
    assert table.c.embedding_model.nullable is True
    assert table.c.embedding_version.nullable is True
    assert table.c.index_version.nullable is True
    assert table.c.failure_reason.nullable is True


def test_rag_chunk_model_stores_authoritative_text_but_not_vectors():
    table = RAGDocumentChunkORM.__table__

    assert table.c.text.nullable is False
    assert "embedding" not in table.c
    assert "vector" not in table.c


def test_rag_chunk_model_defines_identity_integrity_and_lookup_metadata():
    unique_constraints = constraint_names(RAGDocumentChunkORM, UniqueConstraint)
    check_constraints = constraint_names(RAGDocumentChunkORM, CheckConstraint)
    indexes = index_names(RAGDocumentChunkORM)

    assert "uq_rag_document_chunks_chunk_id" in unique_constraints
    assert "uq_rag_document_chunks_position" in unique_constraints
    assert "ck_rag_document_chunks_index_nonnegative" in check_constraints
    assert "ck_rag_document_chunks_page_positive" in check_constraints
    assert "ix_rag_document_chunks_document_pk" in indexes
    assert "ix_rag_document_chunks_document_version" in indexes


def test_rag_chunk_model_links_to_parent_document_with_cascade_relationship():
    document_pk_column = RAGDocumentChunkORM.__table__.c.document_pk
    foreign_keys = list(document_pk_column.foreign_keys)

    assert len(foreign_keys) == 1
    assert isinstance(foreign_keys[0], ForeignKey)
    assert foreign_keys[0].target_fullname == "rag_documents.id"
    assert foreign_keys[0].ondelete == "CASCADE"
    assert "delete-orphan" in RAGDocumentORM.chunks.property.cascade


def test_rag_document_and_chunk_models_can_be_connected_in_memory():
    document = RAGDocumentORM(
        document_id="employee-handbook",
        title="Employee Handbook",
        source="upload://employee-handbook.pdf",
        content_type="application/pdf",
        document_version="3",
        checksum="sha256:abc",
        status=DocumentStatus.INDEXED,
        chunking_version="chunker-v1",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_version="embedding-v1",
        index_version="index-v1",
    )
    chunk = RAGDocumentChunkORM(
        chunk_id="chunk-1",
        document_id="employee-handbook",
        document_version="3",
        chunk_index=0,
        text="Employees receive annual leave according to the handbook.",
        chunking_version="chunker-v1",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_version="embedding-v1",
        index_version="index-v1",
        page_number=4,
        section="Leave Policy",
    )

    document.chunks.append(chunk)

    assert chunk.document is document
    assert document.chunks == [chunk]
