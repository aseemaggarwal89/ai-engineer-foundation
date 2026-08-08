import pytest
from pydantic import ValidationError

from app.core.config import (
    AISettings,
    EmbeddingProvider,
    RAGSettings,
    Settings,
    VectorStoreProvider,
)


def test_rag_settings_defaults_keep_rag_disabled():
    settings = AISettings()

    assert settings.rag.enabled is False
    assert settings.rag.chunk_size == 800
    assert settings.rag.chunk_overlap == 120
    assert settings.rag.retrieval_top_k == 5
    assert settings.rag.minimum_score == 0.3
    assert settings.rag.max_document_bytes == 5 * 1024 * 1024
    assert settings.rag.max_chunks_per_document == 1000
    assert settings.rag.prompt_version == "v1"
    assert settings.rag.index_version == "v1"
    assert settings.rag.embedding.provider == EmbeddingProvider.OPENAI
    assert settings.rag.embedding.model == "text-embedding-3-small"
    assert settings.rag.embedding.batch_size == 64
    assert settings.rag.embedding.timeout_seconds == 30
    assert settings.rag.vector_store.provider == VectorStoreProvider.QDRANT
    assert settings.rag.vector_store.url == "http://qdrant:6333"
    assert settings.rag.vector_store.collection == "documents"
    assert settings.rag.vector_store.timeout_seconds == 10


def test_nested_environment_overrides_rag_settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("AI__PROVIDER", "ollama")
    monkeypatch.setenv("AI__RAG__ENABLED", "true")
    monkeypatch.setenv("AI__RAG__CHUNK_SIZE", "1200")
    monkeypatch.setenv("AI__RAG__CHUNK_OVERLAP", "150")
    monkeypatch.setenv("AI__RAG__RETRIEVAL_TOP_K", "8")
    monkeypatch.setenv("AI__RAG__EMBEDDING__MODEL", "text-embedding-3-large")
    monkeypatch.setenv("AI__RAG__VECTOR_STORE__URL", "http://localhost:6333")

    settings = Settings(_env_file=None)

    assert settings.ai.rag.enabled is True
    assert settings.ai.rag.chunk_size == 1200
    assert settings.ai.rag.chunk_overlap == 150
    assert settings.ai.rag.retrieval_top_k == 8
    assert settings.ai.rag.embedding.model == "text-embedding-3-large"
    assert settings.ai.rag.vector_store.url == "http://localhost:6333"


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("chunk_size", 0, "chunk_size"),
        ("chunk_overlap", -1, "chunk_overlap"),
        ("retrieval_top_k", 0, "retrieval_top_k"),
        ("minimum_score", -0.1, "minimum_score"),
        ("minimum_score", 1.1, "minimum_score"),
        ("max_document_bytes", 0, "max_document_bytes"),
        ("max_chunks_per_document", 0, "max_chunks_per_document"),
    ],
)
def test_rag_settings_reject_invalid_core_values(field, value, match):
    with pytest.raises(ValidationError, match=match):
        RAGSettings(**{field: value})


def test_rag_settings_reject_chunk_overlap_equal_to_chunk_size():
    with pytest.raises(ValidationError, match="chunk_overlap"):
        RAGSettings(chunk_size=100, chunk_overlap=100)


@pytest.mark.parametrize(
    "embedding_overrides,match",
    [
        ({"batch_size": 0}, "batch_size"),
        ({"timeout_seconds": 0}, "timeout_seconds"),
        ({"model": " "}, "embedding model"),
    ],
)
def test_rag_settings_reject_invalid_embedding_values(embedding_overrides, match):
    with pytest.raises(ValidationError, match=match):
        RAGSettings(embedding=embedding_overrides)


@pytest.mark.parametrize(
    "vector_store_overrides,match",
    [
        ({"timeout_seconds": 0}, "timeout_seconds"),
        ({"collection": " "}, "vector-store"),
        ({"url": " "}, "vector-store"),
    ],
)
def test_rag_settings_reject_invalid_vector_store_values(vector_store_overrides, match):
    with pytest.raises(ValidationError, match=match):
        RAGSettings(vector_store=vector_store_overrides)
