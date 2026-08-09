from dataclasses import dataclass


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
