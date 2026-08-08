from abc import ABC, abstractmethod

from app.application.ai.rag.domain.document import LoadedDocumentContent


class DocumentLoaderPort(ABC):
    """Extracts text from source-specific document inputs.

    Future adapters may support plain text, Markdown, PDF, or remote sources.
    Parser SDK objects must not leak through this boundary.
    """

    @abstractmethod
    async def extract(self, *, source: str, content_type: str) -> LoadedDocumentContent:
        pass
