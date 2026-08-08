from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    DELETED = "deleted"

    def can_transition_to(self, next_status: "DocumentStatus") -> bool:
        allowed = {
            DocumentStatus.RECEIVED: {DocumentStatus.PROCESSING},
            DocumentStatus.PROCESSING: {
                DocumentStatus.INDEXED,
                DocumentStatus.FAILED,
            },
            DocumentStatus.INDEXED: {
                DocumentStatus.PROCESSING,
                DocumentStatus.DELETED,
            },
            DocumentStatus.FAILED: {
                DocumentStatus.PROCESSING,
                DocumentStatus.DELETED,
            },
            DocumentStatus.DELETED: set(),
        }
        return next_status in allowed[self]


@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    source: str
    content_type: str
    version: str
    checksum: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self):
        _require_text("document_id", self.document_id)
        _require_text("title", self.title)
        _require_text("source", self.source)
        _require_text("content_type", self.content_type)
        _require_text("version", self.version)
        _require_text("checksum", self.checksum)

        if self.updated_at < self.created_at:
            raise ValueError("updated_at must be greater than or equal to created_at")


@dataclass(frozen=True)
class LoadedDocumentContent:
    title: str
    source: str
    content_type: str
    text: str
    checksum: str

    def __post_init__(self):
        _require_text("title", self.title)
        _require_text("source", self.source)
        _require_text("content_type", self.content_type)
        _require_text("text", self.text)
        _require_text("checksum", self.checksum)


def _require_text(name: str, value: str):
    if not value or not value.strip():
        raise ValueError(f"{name} is required")
