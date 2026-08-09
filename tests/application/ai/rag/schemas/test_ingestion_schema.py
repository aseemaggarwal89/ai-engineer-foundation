import pytest
from pydantic import ValidationError

from app.application.ai.rag.schemas.ingestion import (
    RAGDocumentContentType,
    RAGIngestionRequest,
)
from app.application.ai.rag.usecases.ingest_document_input import (
    IngestDocumentInput,
)


def make_payload(**overrides):
    payload = {
        "document_id": "doc-001",
        "title": "Architecture Notes",
        "source": "manual://architecture-notes",
        "content_type": "text/plain",
        "content": "FastAPI AI backend notes",
    }
    payload.update(overrides)
    return payload


def test_ingestion_request_accepts_valid_plain_text():
    request = RAGIngestionRequest.model_validate(make_payload())

    assert request.document_id == "doc-001"
    assert request.content_type == RAGDocumentContentType.TEXT_PLAIN


def test_ingestion_request_accepts_valid_markdown():
    request = RAGIngestionRequest.model_validate(
        make_payload(
            content_type="text/markdown",
            content="# Architecture\n\nSome Markdown content.",
        )
    )

    assert request.content_type == RAGDocumentContentType.TEXT_MARKDOWN


@pytest.mark.parametrize("field", ["title", "source"])
def test_ingestion_request_rejects_blank_required_text_fields(field):
    with pytest.raises(ValidationError, match=field):
        RAGIngestionRequest.model_validate(make_payload(**{field: "   "}))


@pytest.mark.parametrize("content", ["", "   ", "\n\t  "])
def test_ingestion_request_rejects_empty_or_whitespace_only_content(content):
    with pytest.raises(ValidationError, match="content"):
        RAGIngestionRequest.model_validate(make_payload(content=content))


def test_ingestion_request_rejects_unsupported_content_type():
    with pytest.raises(ValidationError, match="content_type"):
        RAGIngestionRequest.model_validate(make_payload(content_type="application/pdf"))


def test_ingestion_request_trims_metadata_but_preserves_content():
    request = RAGIngestionRequest.model_validate(
        make_payload(
            document_id="  doc-001  ",
            title="  Architecture Notes  ",
            source="  manual://architecture-notes  ",
            content="  keep markdown spacing\n",
        )
    )

    assert request.document_id == "doc-001"
    assert request.title == "Architecture Notes"
    assert request.source == "manual://architecture-notes"
    assert request.content == "  keep markdown spacing\n"


@pytest.mark.parametrize(
    "field",
    ["status", "checksum", "embedding_model", "index_version"],
)
def test_ingestion_request_rejects_internal_caller_controlled_fields(field):
    with pytest.raises(ValidationError, match=field):
        RAGIngestionRequest.model_validate(make_payload(**{field: "caller-value"}))


def test_ingestion_request_maps_to_application_input_without_http_types():
    request = RAGIngestionRequest.model_validate(make_payload())

    command = request.to_application_input()

    assert command == IngestDocumentInput(
        document_id="doc-001",
        title="Architecture Notes",
        source="manual://architecture-notes",
        content_type="text/plain",
        content="FastAPI AI backend notes",
    )
