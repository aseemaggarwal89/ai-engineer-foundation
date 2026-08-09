# RAG Ingestion Request Validation

`RAG-05` defines the first safe input boundary for document ingestion.

The goal is intentionally small:

```text
client request
-> request validation
-> application input
-> future IndexDocumentUseCase
```

This task does not parse documents, chunk text, calculate checksums, create embeddings, write to Qdrant, or persist ingestion state.

## Why This Boundary Exists

RAG ingestion starts with untrusted user content.

The backend needs a clear contract before later processing can happen. Without that contract, future loader, chunking, embedding, and indexing code would each need to guess what the input shape means.

The request schema answers:

```text
What can a client submit?
```

The application input answers:

```text
What does the future use case receive?
```

Keeping those two separate prevents HTTP models from becoming domain or persistence models.

## Request Schema

The HTTP-facing schema lives in:

```text
app/application/ai/rag/schemas/ingestion.py
```

The request model is:

```text
RAGIngestionRequest
```

It accepts:

| Field | Required | Owner | Purpose |
| --- | --- | --- | --- |
| `document_id` | Yes | Client | Stable logical document identity |
| `title` | Yes | Client | Human-readable title |
| `source` | Yes | Client | Generic source label, path, or URI |
| `content_type` | Yes | Client | Supported content representation |
| `content` | Yes | Client | Plain text or Markdown content |

Supported initial content types are:

```text
text/plain
text/markdown
```

PDF, OCR, file uploads, URLs, and object-storage sources are intentionally deferred.

## Application Input

The application-level command lives in:

```text
app/application/ai/rag/usecases/ingest_document_input.py
```

The command is:

```text
IngestDocumentInput
```

It is a frozen dataclass and does not depend on FastAPI or Pydantic.

That matters because the future ingestion use case may be called from:

- an HTTP route
- a background worker
- a CLI command
- a test
- a scheduled reindex job

The DTO maps to this command through:

```python
request.to_application_input()
```

## Ownership Decisions

`document_id` is caller supplied.

It is a stable logical identifier, such as:

```text
handbook-intro
policy:security:2026
docs.architecture.rag
```

It is not the database primary key. PostgreSQL still owns internal row identity.

`document_version` is not caller controlled in the ingestion request.

The application will own version assignment later because versioning must stay consistent with persistence, checksum, reindexing, and chunking behavior.

Clients also cannot set:

- lifecycle status
- checksum
- embedding model
- index version
- chunking version
- prompt version
- processing state

A client can submit content. The application decides what happened to that content.

For example, this is rejected:

```json
{
  "document_id": "handbook",
  "title": "Handbook",
  "source": "manual://handbook",
  "content_type": "text/plain",
  "content": "Welcome",
  "status": "indexed"
}
```

The client cannot truthfully declare the document indexed. Only the application knows whether validation, extraction, chunking, embedding, and indexing completed.

## Structural Validation

Pydantic validates:

- required fields
- non-empty `document_id`
- safe `document_id` characters
- bounded `document_id`, `title`, and `source`
- non-blank `title`
- non-blank `source`
- non-empty and non-whitespace `content`
- allowed `content_type`
- forbidden extra fields

Extra fields are forbidden so clients cannot smuggle internal state into the request.

## Runtime Policy Validation

Settings-driven validation lives in:

```text
app/application/ai/rag/validators/ingestion_request_validator.py
```

The validator is:

```text
RAGIngestionRequestValidator
```

It enforces:

```text
RAGSettings.max_document_bytes
```

The byte size is calculated with UTF-8 encoding:

```python
len(content.encode("utf-8"))
```

This is important because character count and byte count are not always the same.

For example:

```text
éé
```

has 2 characters but 4 UTF-8 bytes.

The boundary behavior is:

- exactly `max_document_bytes` is accepted
- `max_document_bytes + 1` is rejected

## Why Size Limits Matter

Unbounded document ingestion can affect:

- memory
- CPU
- chunk count
- embedding cost
- indexing latency
- storage
- provider limits

`max_document_bytes` is both a reliability control and an abuse-protection control.

## Structural vs Runtime Validation

This project keeps two kinds of validation separate:

```text
Request schema
-> field shape
-> basic text constraints
-> enum validation
```

```text
Application policy
-> configured byte limit
-> future feature enabled checks
-> future authorization checks
-> future source policy
```

That keeps the DTO simple and prevents application settings from leaking into the schema class.

## Logging Safety

Document content is untrusted.

The ingestion boundary must not log:

- raw document content
- raw request bodies
- secrets
- embeddings
- large metadata payloads

Safe future log fields include:

- request ID
- document ID
- content type
- byte size
- validation result

## What Was Deferred

This task intentionally does not implement:

- PDF extraction
- OCR
- Markdown parsing
- document loader
- text normalization
- chunking
- checksum calculation
- repository writes
- embeddings
- Qdrant indexing
- background workers
- retrieval
- RAG prompting

Those belong to later RAG tasks.

## Tests

The test coverage verifies:

- valid plain text requests
- valid Markdown requests
- blank title rejection
- blank and whitespace-only content rejection
- unsupported content type rejection
- metadata trimming
- content preservation
- forbidden internal fields
- DTO to application input mapping
- UTF-8 byte-size boundary behavior

## Next

The next task is:

```text
RAG-06 — Document Loader / Extraction
```

That task will decide how submitted content becomes loaded document text for the indexing workflow.
