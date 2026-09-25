from enum import Enum


class RAGDocumentContentType(str, Enum):
    TEXT_PLAIN = "text/plain"
    TEXT_MARKDOWN = "text/markdown"
