from collections.abc import Mapping

from app.application.ai.rag.domain.document import LoadedDocumentContent
from app.application.ai.rag.domain.document_loader_port import (
    DocumentLoaderPort,
    DocumentLoadRequest,
)
from app.application.ai.rag.domain.content_type import RAGDocumentContentType
from app.domain.exceptions.exceptions import (
    EmptyLoadedDocumentError,
    UnsupportedDocumentTypeError,
)


class PlainTextDocumentLoader(DocumentLoaderPort):
    supported_content_type = RAGDocumentContentType.TEXT_PLAIN.value

    async def load(self, request: DocumentLoadRequest) -> LoadedDocumentContent:
        return _build_loaded_content(request)


class MarkdownDocumentLoader(DocumentLoaderPort):
    supported_content_type = RAGDocumentContentType.TEXT_MARKDOWN.value

    async def load(self, request: DocumentLoadRequest) -> LoadedDocumentContent:
        return _build_loaded_content(request)


class DocumentLoaderResolver:
    def __init__(self, loaders: Mapping[str, DocumentLoaderPort]):
        self._loaders = dict(loaders)

    def resolve(self, content_type: str) -> DocumentLoaderPort:
        loader = self._loaders.get(content_type)

        if not loader:
            raise UnsupportedDocumentTypeError()

        return loader

    async def load(self, request: DocumentLoadRequest) -> LoadedDocumentContent:
        return await self.resolve(request.content_type).load(request)


def create_default_document_loader_resolver() -> DocumentLoaderResolver:
    loaders: dict[str, DocumentLoaderPort] = {
        PlainTextDocumentLoader.supported_content_type: PlainTextDocumentLoader(),
        MarkdownDocumentLoader.supported_content_type: MarkdownDocumentLoader(),
    }
    return DocumentLoaderResolver(loaders)


def _build_loaded_content(request: DocumentLoadRequest) -> LoadedDocumentContent:
    if not request.content.strip():
        raise EmptyLoadedDocumentError()

    return LoadedDocumentContent(
        title=request.title,
        source=request.source,
        content_type=request.content_type,
        text=request.content,
    )
