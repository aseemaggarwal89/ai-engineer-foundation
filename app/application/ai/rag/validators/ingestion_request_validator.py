from app.application.ai.rag.usecases.ingest_document_input import (
    IngestDocumentInput,
)
from app.core.config import RAGSettings
from app.domain.exceptions.exceptions import PromptTooLargeError


class RAGIngestionRequestValidator:
    """
    Applies settings-driven ingestion policy that does not belong in the DTO.

    Pydantic validates request shape and basic field constraints. This validator
    enforces runtime policy such as byte-oriented document size limits.
    """

    def __init__(self, settings: RAGSettings):
        self.settings = settings

    def validate(self, request: IngestDocumentInput) -> IngestDocumentInput:
        if request.content_size_bytes > self.settings.max_document_bytes:
            raise PromptTooLargeError("Document exceeds allowed byte size")

        return request
