# RAG Document Loading

`RAG-06` adds the first document-loading layer for the ingestion pipeline.

The goal is small:

```text
validated ingestion input
-> document loader
-> LoadedDocumentContent
-> future normalizer and chunker
```

This task does not normalize text, split chunks, calculate checksums, create embeddings, write to Qdrant, or persist documents.

## What Is Document Loading?

Document loading turns an accepted source representation into a common application-owned content model.

For this project, the first accepted source representations are already textual:

```text
text/plain
text/markdown
```

That means extraction is intentionally simple. The loader preserves the submitted content and wraps it in:

```text
LoadedDocumentContent
```

## Why Use `DocumentLoaderPort`?

The existing port lives in:

```text
app/application/ai/rag/domain/document_loader_port.py
```

All source-specific loaders implement the same contract.

Without this boundary, the pipeline could become source-specific:

```text
PDF parser object
-> chunker

Markdown AST
-> embedding service
```

Preferred:

```text
source-specific loader
-> LoadedDocumentContent
-> generic downstream pipeline
```

## Initial Loaders

Plain text:

```text
Plain Text
    |
    v
PlainTextDocumentLoader
    |
    v
LoadedDocumentContent
```

Markdown:

```text
Markdown
    |
    v
MarkdownDocumentLoader
    |
    v
LoadedDocumentContent
```

Both loaders preserve the original textual structure. For Markdown, headings and syntax are not stripped because later chunking may use them for section-aware retrieval.

## Loader Resolution

Loader selection lives in:

```text
app/application/ai/rag/infrastructure/document_loaders.py
```

The resolver maps:

```text
text/plain -> PlainTextDocumentLoader
text/markdown -> MarkdownDocumentLoader
```

Unsupported content types fail with a safe application exception.

## Loaded Representation

`LoadedDocumentContent` preserves:

- `title`
- `source`
- `content_type`
- extracted `text`

It does not include parser-specific objects, fake page numbers, embeddings, chunks, vector-store identifiers, or checksums.

Checksum calculation is deferred. The future ingestion use case should own authoritative checksum/idempotency behavior because it coordinates repository state and document versions.

## Loader vs Normalizer vs Chunker

| Component | Responsibility |
| --- | --- |
| Loader | obtain or extract textual content |
| Normalizer | create a consistent textual representation |
| Chunker | divide normalized text into retrieval units |
| EmbeddingPort | convert chunks to vectors |
| VectorStorePort | store and search vectors |

The loader answers:

```text
What text did this source contain?
```

The normalizer answers:

```text
How should this text be cleaned or standardized?
```

The chunker answers:

```text
How should this text be divided for retrieval?
```

## Why Start With Text and Markdown?

Text and Markdown are enough to validate the architecture without immediately adding:

- PDF parsing
- OCR
- layout reconstruction
- table extraction
- image extraction
- scanned-document handling

Those can be added later as new loader adapters.

## Why No OCR Yet?

OCR introduces separate concerns:

- image preprocessing
- language detection
- layout reconstruction
- extraction accuracy
- cost
- latency

It is not needed to prove the first RAG ingestion architecture.

## Safety

Loaders must not log raw document content.

Safe future log fields include:

- document ID
- content type
- byte size
- loader name

Raw document text remains untrusted input.

## Tests

The RAG-06 tests verify:

- plain text loading
- Markdown loading
- Markdown structure preservation
- loader resolution by content type
- unsupported content type failure
- empty loaded content failure
- no unwanted normalization

## Next

The next task is:

```text
RAG-07 — Text Normalizer and Chunker
```
