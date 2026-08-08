from dataclasses import dataclass
from enum import Enum

from app.application.ai.rag.domain.citation import Citation


class RAGResultStatus(str, Enum):
    ANSWERED = "answered"
    NO_CONTEXT = "no_context"


@dataclass(frozen=True)
class RAGResult:
    answer: str
    citations: list[Citation]
    status: RAGResultStatus = RAGResultStatus.ANSWERED

    def __post_init__(self):
        if not self.answer or not self.answer.strip():
            raise ValueError("answer is required")

        if self.status == RAGResultStatus.NO_CONTEXT and self.citations:
            raise ValueError("no-context results must not include citations")

    @classmethod
    def no_context(cls, answer: str) -> "RAGResult":
        return cls(
            answer=answer,
            citations=[],
            status=RAGResultStatus.NO_CONTEXT,
        )
