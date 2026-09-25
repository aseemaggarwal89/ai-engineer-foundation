from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.application.ai.rag.domain.document import LoadedDocumentContent


@dataclass(frozen=True)
class DocumentLoadRequest:
    title: str
    source: str
    content_type: str
    content: str

    @property
    def content_size_bytes(self) -> int:
        return len(self.content.encode("utf-8"))


class DocumentLoaderPort(ABC):
    """Extracts text from source-specific document inputs.

    Future adapters may support plain text, Markdown, PDF, or remote sources.
    Parser SDK objects must not leak through this boundary.
    """

    @abstractmethod
    async def load(self, request: DocumentLoadRequest) -> LoadedDocumentContent:
        pass
