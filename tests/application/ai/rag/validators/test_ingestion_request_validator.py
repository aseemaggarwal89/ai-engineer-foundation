import pytest

from app.application.ai.rag.usecases.ingest_document_input import (
    IngestDocumentInput,
)
from app.application.ai.rag.validators.ingestion_request_validator import (
    RAGIngestionRequestValidator,
)
from app.core.config import RAGSettings
from app.domain.exceptions.exceptions import PromptTooLargeError


def make_input(content: str) -> IngestDocumentInput:
    return IngestDocumentInput(
        document_id="doc-001",
        title="Architecture Notes",
        source="manual://architecture-notes",
        content_type="text/plain",
        content=content,
    )


def test_ingestion_validator_accepts_content_at_byte_limit():
    validator = RAGIngestionRequestValidator(
        RAGSettings(max_document_bytes=4)
    )
    command = make_input("éé")

    assert command.content_size_bytes == 4
    assert validator.validate(command) is command


def test_ingestion_validator_rejects_content_above_byte_limit():
    validator = RAGIngestionRequestValidator(
        RAGSettings(max_document_bytes=4)
    )

    with pytest.raises(PromptTooLargeError, match="byte size"):
        validator.validate(make_input("ééx"))
