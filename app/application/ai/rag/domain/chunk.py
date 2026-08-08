from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    document_version: str
    chunk_index: int
    text: str
    chunking_version: str
    section: str | None = None
    page_number: int | None = None
    source: str | None = None

    def __post_init__(self):
        _require_text("chunk_id", self.chunk_id)
        _require_text("document_id", self.document_id)
        _require_text("document_version", self.document_version)
        _require_text("text", self.text)
        _require_text("chunking_version", self.chunking_version)

        if self.chunk_index < 0:
            raise ValueError("chunk_index must be greater than or equal to zero")

        if self.page_number is not None and self.page_number < 1:
            raise ValueError("page_number must be greater than zero")


@dataclass(frozen=True)
class EmbeddedChunk:
    chunk: DocumentChunk
    embedding: Sequence[float]
    embedding_model: str
    embedding_version: str

    def __post_init__(self):
        if not self.embedding:
            raise ValueError("embedding is required")

        _require_text("embedding_model", self.embedding_model)
        _require_text("embedding_version", self.embedding_version)


def _require_text(name: str, value: str):
    if not value or not value.strip():
        raise ValueError(f"{name} is required")
