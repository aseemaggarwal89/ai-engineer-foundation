import pytest

from app.application.ai.rag.infrastructure.document_loaders import (
    DocumentLoaderResolver,
    MarkdownDocumentLoader,
    PlainTextDocumentLoader,
    create_default_document_loader_resolver,
)
from app.application.ai.rag.usecases.ingest_document_input import (
    IngestDocumentInput,
)
from app.domain.exceptions.exceptions import (
    EmptyLoadedDocumentError,
    UnsupportedDocumentTypeError,
)


def make_input(**overrides) -> IngestDocumentInput:
    data = {
        "document_id": "doc-001",
        "title": "Knowledge Base Note",
        "source": "manual://knowledge-base-note",
        "content_type": "text/plain",
        "content": "Do not normalize this Text.\n\nKeep punctuation!",
    }
    data.update(overrides)
    return IngestDocumentInput(**data)


@pytest.mark.asyncio
async def test_plain_text_loader_returns_loaded_document_content_without_normalizing():
    command = make_input()
    loader = PlainTextDocumentLoader()

    loaded = await loader.load(command.to_load_request())

    assert loaded.title == "Knowledge Base Note"
    assert loaded.source == "manual://knowledge-base-note"
    assert loaded.content_type == "text/plain"
    assert loaded.text == "Do not normalize this Text.\n\nKeep punctuation!"


@pytest.mark.asyncio
async def test_markdown_loader_preserves_useful_markdown_structure():
    markdown = (
        "# Leave Policy\n\n"
        "Employees receive 20 annual leave days.\n\n"
        "## Carry Forward\n\n"
        "Unused leave can be carried forward."
    )
    command = make_input(content_type="text/markdown", content=markdown)

    loaded = await MarkdownDocumentLoader().load(command.to_load_request())

    assert loaded.content_type == "text/markdown"
    assert loaded.text == markdown
    assert "# Leave Policy" in loaded.text
    assert "## Carry Forward" in loaded.text


def test_default_loader_resolver_maps_supported_content_types():
    resolver = create_default_document_loader_resolver()

    assert isinstance(resolver.resolve("text/plain"), PlainTextDocumentLoader)
    assert isinstance(resolver.resolve("text/markdown"), MarkdownDocumentLoader)


def test_loader_resolver_rejects_unsupported_content_type_safely():
    resolver = DocumentLoaderResolver({})

    with pytest.raises(UnsupportedDocumentTypeError):
        resolver.resolve("application/pdf")


@pytest.mark.asyncio
@pytest.mark.parametrize("content", ["", "   ", "\n\t "])
async def test_loader_rejects_empty_or_whitespace_only_loaded_content(content):
    command = make_input(content=content)

    with pytest.raises(EmptyLoadedDocumentError):
        await PlainTextDocumentLoader().load(command.to_load_request())
