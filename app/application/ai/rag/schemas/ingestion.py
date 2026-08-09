from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

from app.application.ai.rag.usecases.ingest_document_input import (
    IngestDocumentInput,
)


DocumentId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$",
    ),
]

DocumentTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]

DocumentSource = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]

DocumentContent = Annotated[
    str,
    StringConstraints(min_length=1),
]


class RAGDocumentContentType(str, Enum):
    TEXT_PLAIN = "text/plain"
    TEXT_MARKDOWN = "text/markdown"


class RAGIngestionRequest(BaseModel):
    """
    HTTP-facing request contract for submitting text knowledge to RAG.

    The request intentionally accepts only caller-owned document information.
    Lifecycle state, checksums, document versions, embedding models, and index
    versions are application-owned and are assigned later in the ingestion flow.
    """

    model_config = ConfigDict(extra="forbid")

    document_id: DocumentId = Field(
        ...,
        description="Stable caller-supplied logical document identifier.",
    )
    title: DocumentTitle = Field(
        ...,
        description="Human-readable document title.",
    )
    source: DocumentSource = Field(
        ...,
        description="Generic source label, path, or URI for provenance.",
    )
    content_type: RAGDocumentContentType = Field(
        ...,
        description="Supported text content type.",
    )
    content: DocumentContent = Field(
        ...,
        description="Plain text or Markdown content to ingest.",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content is required")

        return value

    def to_application_input(self) -> IngestDocumentInput:
        return IngestDocumentInput(
            document_id=self.document_id,
            title=self.title,
            source=self.source,
            content_type=self.content_type.value,
            content=self.content,
        )
