from abc import ABC, abstractmethod

from app.application.ai.rag.domain.chunk import DocumentChunk
from app.application.ai.rag.domain.document import Document, DocumentStatus


class DocumentRepositoryPort(ABC):
    """Authoritative document metadata and ingestion lifecycle boundary."""

    @abstractmethod
    async def create(self, document: Document) -> Document:
        pass

    @abstractmethod
    async def get(self, document_id: str) -> Document | None:
        pass

    @abstractmethod
    async def get_by_checksum(self, checksum: str) -> Document | None:
        pass

    @abstractmethod
    async def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
    ) -> Document:
        pass

    @abstractmethod
    async def save_chunks_metadata(
        self,
        document_id: str,
        chunks: list[DocumentChunk],
    ) -> None:
        pass

    @abstractmethod
    async def delete(self, document_id: str) -> None:
        pass
