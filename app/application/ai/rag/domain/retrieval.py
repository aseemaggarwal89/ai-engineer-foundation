from dataclasses import dataclass
import math
from typing import Mapping

from app.application.ai.rag.domain.citation import Citation

FilterValue = str | int | float | bool


@dataclass(frozen=True)
class RetrievalQuery:
    query: str
    top_k: int = 5
    minimum_score: float | None = None
    namespace: str | None = None
    filters: Mapping[str, FilterValue] | None = None

    def __post_init__(self):
        if not self.query or not self.query.strip():
            raise ValueError("query is required")

        if self.top_k < 1:
            raise ValueError("top_k must be greater than zero")

        if self.minimum_score is not None and not math.isfinite(self.minimum_score):
            raise ValueError("minimum_score must be finite")


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    score: float
    citation: Citation
    metadata: Mapping[str, FilterValue] | None = None

    def __post_init__(self):
        _require_text("chunk_id", self.chunk_id)
        _require_text("document_id", self.document_id)
        _require_text("text", self.text)

        if not math.isfinite(self.score):
            raise ValueError("score must be finite")


@dataclass(frozen=True)
class RetrievalResult:
    query: RetrievalQuery
    chunks: list[RetrievedChunk]

    def relevant_chunks(self) -> list[RetrievedChunk]:
        if self.query.minimum_score is None:
            return self.chunks

        return [
            chunk
            for chunk in self.chunks
            if chunk.score >= self.query.minimum_score
        ]


def _require_text(name: str, value: str):
    if not value or not value.strip():
        raise ValueError(f"{name} is required")
