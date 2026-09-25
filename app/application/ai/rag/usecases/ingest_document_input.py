from dataclasses import dataclass

from app.application.ai.rag.domain.document_loader_port import DocumentLoadRequest


@dataclass(frozen=True)
class IngestDocumentInput:
    """
    Application-level input for future document indexing.

    This command is independent of FastAPI and Pydantic so the future use case
    can be called from HTTP routes, workers, CLI tasks, or tests.
    """

    document_id: str
    title: str
    source: str
    content_type: str
    content: str

    @property
    def content_size_bytes(self) -> int:
        return len(self.content.encode("utf-8"))

    def to_load_request(self) -> DocumentLoadRequest:
        return DocumentLoadRequest(
            title=self.title,
            source=self.source,
            content_type=self.content_type,
            content=self.content,
        )
