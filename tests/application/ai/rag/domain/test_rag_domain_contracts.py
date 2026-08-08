from datetime import UTC, datetime

import pytest

from app.application.ai.rag.domain.chunk import DocumentChunk, EmbeddedChunk
from app.application.ai.rag.domain.citation import Citation
from app.application.ai.rag.domain.document import Document, DocumentStatus
from app.application.ai.rag.domain.rag_result import RAGResult, RAGResultStatus
from app.application.ai.rag.domain.retrieval import (
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
)


def test_document_status_allows_only_expected_lifecycle_transitions():
    assert DocumentStatus.RECEIVED.can_transition_to(DocumentStatus.PROCESSING)
    assert DocumentStatus.PROCESSING.can_transition_to(DocumentStatus.INDEXED)
    assert DocumentStatus.PROCESSING.can_transition_to(DocumentStatus.FAILED)
    assert DocumentStatus.INDEXED.can_transition_to(DocumentStatus.PROCESSING)
    assert DocumentStatus.INDEXED.can_transition_to(DocumentStatus.DELETED)
    assert DocumentStatus.FAILED.can_transition_to(DocumentStatus.PROCESSING)
    assert DocumentStatus.FAILED.can_transition_to(DocumentStatus.DELETED)

    assert not DocumentStatus.RECEIVED.can_transition_to(DocumentStatus.INDEXED)
    assert not DocumentStatus.DELETED.can_transition_to(DocumentStatus.PROCESSING)


def test_document_rejects_missing_identity():
    now = datetime.now(UTC)

    with pytest.raises(ValueError, match="document_id is required"):
        Document(
            document_id=" ",
            title="Architecture Notes",
            source="docs/architecture.md",
            content_type="text/markdown",
            version="v1",
            checksum="sha256:abc",
            status=DocumentStatus.RECEIVED,
            created_at=now,
            updated_at=now,
        )


def test_document_rejects_updated_at_before_created_at():
    with pytest.raises(ValueError, match="updated_at"):
        Document(
            document_id="doc-1",
            title="Architecture Notes",
            source="docs/architecture.md",
            content_type="text/markdown",
            version="v1",
            checksum="sha256:abc",
            status=DocumentStatus.RECEIVED,
            created_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
            updated_at=datetime(2026, 8, 8, 11, 0, tzinfo=UTC),
        )


def test_document_chunk_rejects_negative_index_and_invalid_page_number():
    with pytest.raises(ValueError, match="chunk_index"):
        DocumentChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_version="v1",
            chunk_index=-1,
            text="content",
            chunking_version="chunker-v1",
        )

    with pytest.raises(ValueError, match="page_number"):
        DocumentChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_version="v1",
            chunk_index=0,
            text="content",
            chunking_version="chunker-v1",
            page_number=0,
        )


def test_embedded_chunk_requires_vector_and_embedding_metadata():
    chunk = DocumentChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        document_version="v1",
        chunk_index=0,
        text="content",
        chunking_version="chunker-v1",
    )

    with pytest.raises(ValueError, match="embedding is required"):
        EmbeddedChunk(
            chunk=chunk,
            embedding=[],
            embedding_model="text-embedding-3-small",
            embedding_version="embedding-v1",
        )


def test_citation_rejects_invalid_page_number():
    with pytest.raises(ValueError, match="page_number"):
        Citation(
            document_id="doc-1",
            chunk_id="chunk-1",
            title="Architecture Notes",
            page_number=0,
        )


def test_retrieval_query_and_result_filter_relevant_chunks():
    query = RetrievalQuery(
        query="How does provider fallback work?",
        top_k=3,
        minimum_score=0.75,
    )

    citation = Citation(
        document_id="doc-1",
        chunk_id="chunk-1",
        title="Provider Architecture",
    )

    result = RetrievalResult(
        query=query,
        chunks=[
            RetrievedChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                text="High confidence evidence",
                score=0.91,
                citation=citation,
            ),
            RetrievedChunk(
                chunk_id="chunk-2",
                document_id="doc-1",
                text="Weak evidence",
                score=0.42,
                citation=Citation(
                    document_id="doc-1",
                    chunk_id="chunk-2",
                    title="Provider Architecture",
                ),
            ),
        ],
    )

    assert [chunk.chunk_id for chunk in result.relevant_chunks()] == ["chunk-1"]


def test_retrieval_models_reject_invalid_scores():
    with pytest.raises(ValueError, match="minimum_score"):
        RetrievalQuery(query="hello", minimum_score=1.5)

    with pytest.raises(ValueError, match="score"):
        RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            text="content",
            score=1.2,
            citation=Citation(
                document_id="doc-1",
                chunk_id="chunk-1",
                title="Architecture Notes",
            ),
        )


def test_no_context_result_is_normal_domain_result_without_citations():
    result = RAGResult.no_context(
        "The indexed knowledge base does not contain enough information to answer this question."
    )

    assert result.status == RAGResultStatus.NO_CONTEXT
    assert result.citations == []

    with pytest.raises(ValueError, match="no-context"):
        RAGResult(
            answer="No context",
            citations=[
                Citation(
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    title="Architecture Notes",
                )
            ],
            status=RAGResultStatus.NO_CONTEXT,
        )
