from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from app.application.ai.rag.domain.chunk import EmbeddedChunk
from app.application.ai.rag.domain.retrieval import RetrievalQuery, RetrievalResult


@dataclass(frozen=True)
class VectorStoreHealth:
    healthy: bool
    detail: str | None = None


class VectorStorePort(ABC):
    """Provider-independent vector index boundary.

    Future adapters may use Qdrant, pgvector, or another vector store. Use cases
    depend on this port, not on vector database SDK types.
    """

    @abstractmethod
    async def upsert_chunks(self, chunks: Sequence[EmbeddedChunk]) -> None:
        pass

    @abstractmethod
    async def search(
        self,
        *,
        query: RetrievalQuery,
        query_embedding: Sequence[float],
    ) -> RetrievalResult:
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> None:
        pass

    @abstractmethod
    async def health(self) -> VectorStoreHealth:
        pass
