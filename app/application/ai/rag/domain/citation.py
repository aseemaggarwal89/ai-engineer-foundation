from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    document_id: str
    chunk_id: str
    title: str
    page_number: int | None = None
    section: str | None = None
    source: str | None = None

    def __post_init__(self):
        _require_text("document_id", self.document_id)
        _require_text("chunk_id", self.chunk_id)
        _require_text("title", self.title)

        if self.page_number is not None and self.page_number < 1:
            raise ValueError("page_number must be greater than zero")


def _require_text(name: str, value: str):
    if not value or not value.strip():
        raise ValueError(f"{name} is required")
