# RAG-05 — Ingestion Request Schema and Validation

## Purpose

This document explains the changes, concepts, and reasoning behind **RAG-05 — Ingestion Request Schema and Validation**. It is intended as a future learning reference for understanding how the RAG ingestion pipeline begins.

> **Accuracy note:** the final Codex completion report/diff for RAG-05 was not provided here. The details below document the agreed RAG-05 task contract and architecture. Before treating exact class names or paths as final, compare with the repository, tests, and `docs/architecture/rag-progress.md`.

---

# 1. Where RAG-05 Fits

```text
RAG-00  Architecture + domain contracts
   ↓
RAG-01  Configuration
   ↓
RAG-02  Persistence models
   ↓
RAG-03  Alembic migration
   ↓
RAG-04  Document repository
   ↓
RAG-05  Ingestion request + validation
   ↓
RAG-06  Document loader / extraction
   ↓
RAG-07  Normalization + chunking
   ↓
RAG-08/09 Embeddings
   ↓
RAG-10/11 Vector store + Qdrant
   ↓
RAG-12  IndexDocumentUseCase
```

RAG-05 answers:

> **What information is allowed to enter the RAG ingestion pipeline, and who owns each piece of state?**

---

# 2. What “Ingestion” Means

RAG ingestion means preparing external knowledge for future semantic retrieval.

Eventually:

```text
External Knowledge
      ↓
Validate Request
      ↓
Load / Extract
      ↓
Normalize
      ↓
Chunk
      ↓
Embed
      ↓
Store Vectors
      ↓
Knowledge Becomes Searchable
```

RAG-05 handles only:

```text
External Input
      ↓
Validation
      ↓
Safe Application Input
```

It does **not** yet perform loading, chunking, embedding, Qdrant indexing, retrieval, or generation.

---

# 3. Why an Ingestion Contract Is Necessary

Without a clear request contract, every downstream component would need to repeat questions such as:

```text
Is the title present?
Is content empty?
Is this content type supported?
Is the document too large?
Can the caller choose status?
Can the caller choose the embedding model?
Who owns versioning?
Who owns checksums?
```

That leads to duplicated validation, inconsistent behavior, security problems, and hard-to-test services.

RAG-05 creates one clear front-door boundary.

---

# 4. API Request DTO vs Application Input vs Domain Model

These should remain separate.

## API Request DTO

Represents what the client sends.

Conceptually:

```text
document_id
title
source
content_type
content
```

## Application Input

Represents what the future use case needs.

Possible name:

```text
IngestDocumentInput
```

## Domain `Document`

Represents application lifecycle state such as:

```text
status
version
checksum
processing metadata
```

## ORM Model

Represents how that state is persisted in PostgreSQL.

Flow:

```text
Client JSON
    ↓
Request DTO
    ↓
Application Input
    ↓
Domain
    ↓
Repository
    ↓
PostgreSQL
```

This separation keeps HTTP, application logic, domain state, and persistence concerns independent.

---

# 5. Why the Domain `Document` Should Not Be the Request Model

A caller should not control all domain state.

Bad example:

```json
{
  "title": "Employee Handbook",
  "status": "INDEXED"
}
```

The client cannot know whether extraction, chunking, embedding, and Qdrant indexing actually succeeded.

Therefore:

```text
Client supplies knowledge.
Application owns processing truth.
```

---

# 6. Expected Initial Request Fields

The task proposes a small request surface, likely concepts such as:

```text
document_id
title
source
content_type
content
```

The exact final set should match the repository.

The key rule is:

> Add only fields required at ingestion time. Do not add speculative fields merely for future flexibility.

---

# 7. `document_id`

A document needs a stable logical identity.

Example:

```text
employee-handbook
```

Possible versions:

```text
employee-handbook v1
employee-handbook v2
employee-handbook v3
```

RAG-05 must make one decision explicit:

```text
Who owns document_id?
```

Either:

```text
caller supplied
```

or:

```text
server generated
```

This matters for updates, reindexing, deletion, citations, and API lookups.

A logical `document_id` should not automatically be confused with an internal database primary key.

---

# 8. `title`

Example:

```text
Employee Handbook
```

Why needed:

```text
citations
document lists
admin tools
user-facing provenance
debugging
```

Typical validation:

```text
not blank
not whitespace-only
bounded length
trimmed
```

Title is descriptive metadata, not identity.

---

# 9. `source`

A generic source describes where knowledge originated.

Examples:

```text
manual-upload
internal-document
user-provided-text
URI/reference
```

Keep this generic.

Do not introduce OdinSync/CRM-specific source fields yet.

---

# 10. `content_type`

The request should identify the content format.

Recommended first support may include:

```text
text/plain
text/markdown
```

Later:

```text
application/pdf
```

when the loader actually supports it.

A controlled enum/literal provides validation, predictable loader routing, and clear documentation.

Do not advertise content types the pipeline cannot process.

---

# 11. `content`

For the first text-based ingestion flow, content can conceptually be:

```text
content: str
```

Validation should ensure:

```text
not empty
not whitespace-only
within max_document_bytes
```

RAG-05 does not parse or split the content.

---

# 12. Why Empty and Whitespace-Only Content Is Rejected

This request:

```json
{
  "title": "Policy",
  "content": ""
}
```

contains no knowledge to load, chunk, embed, or retrieve.

Likewise:

```text
"   \n\n\t"
```

has characters but no meaningful content.

Rejecting these inputs early prevents meaningless lifecycle records and unnecessary downstream work.

---

# 13. `max_document_bytes`

RAG-01 introduced:

```text
RAGSettings.max_document_bytes
```

RAG-05 is where this policy becomes useful.

```text
content size
   ↓
<= configured limit?
   ├── yes → accept
   └── no  → reject
```

This is a reliability, security, and capacity limit.

Large documents can increase:

```text
memory usage
processing time
chunk count
embedding calls
Qdrant writes
latency
storage
```

---

# 14. Characters Are Not Bytes

This is important.

```python
len(content)
```

measures characters, not UTF-8 byte size.

Many Unicode characters use multiple bytes.

If the setting is called:

```text
max_document_bytes
```

validation should conceptually use:

```python
len(content.encode("utf-8"))
```

or an equivalent project-consistent helper.

Boundary behavior should be explicit:

```text
exactly limit → accepted
limit + 1 byte → rejected
```

---

# 15. Structural Validation vs Runtime Policy Validation

These are different.

## Structural validation

Naturally belongs in a Pydantic/request model:

```text
required fields
non-empty title
valid content type
basic string bounds
```

## Runtime policy validation

May depend on settings/environment:

```text
max_document_bytes
RAG enabled/disabled
future authorization
allowed source policy
```

This distinction prevents request DTOs from becoming tightly coupled to global settings.

---

# 16. Why Avoid Direct Global Settings Reads Inside DTOs

A DTO that reaches into global runtime configuration can create:

```text
hidden dependencies
harder tests
environment-sensitive construction
global coupling
```

A cleaner conceptual flow is:

```text
Request DTO
   ↓
Structural Validation
   ↓
Application Validation
   ├── uses RAGSettings
   └── applies runtime policy
```

The actual implementation should follow existing project conventions.

---

# 17. `document_version` Ownership

RAG-05 must make clear whether versioning is client-controlled or application-managed.

In most designs, application-managed versioning is safer because the platform can reason about:

```text
latest version
checksum
existing processing state
reindexing
```

A caller should not arbitrarily create conflicting lifecycle history.

If explicit client versions are supported, their semantics must be documented precisely.

---

# 18. Checksum Ownership

The client generally should not supply the authoritative checksum.

Preferred future flow:

```text
validated content
   ↓
application computes checksum
   ↓
DocumentRepository lookup
```

Why?

Checksum is used for:

```text
idempotency
change detection
duplicate processing prevention
```

If the caller supplies a wrong checksum for the submitted content, those decisions become unsafe.

---

# 19. Status Ownership

Clients should not set:

```text
RECEIVED
PROCESSING
INDEXED
FAILED
DELETED
```

These are application lifecycle states.

Future flow:

```text
request accepted
   ↓
RECEIVED
   ↓
PROCESSING
   ├── INDEXED
   └── FAILED
```

Only the application knows whether each state is true.

---

# 20. Processing Configuration Ownership

Clients should normally not control:

```text
chunking_version
embedding_provider
embedding_model
index_version
prompt_version
```

These should come from application policy such as `RAGSettings`.

Why?

Allowing every client to choose arbitrary models/processing versions can create an inconsistent index and make evaluation/migration/recovery much harder.

---

# 21. Optional Metadata

Generic metadata should only be added if there is an immediate consumer.

Possible examples:

```text
category
language
source_reference
```

If supported, metadata should be bounded, JSON-compatible, generic, and validated.

Arbitrary unbounded metadata can become a hidden schema and security/storage risk.

If it is not needed yet, defer it.

---

# 22. Security: Treat Document Content as Untrusted

Submitted knowledge can contain:

```text
malicious text
prompt injection
HTML/scripts
strange Unicode
oversized strings
sensitive information
```

RAG-05 treats it as data.

It should not execute or interpret instructions embedded in the document.

Later RAG prompt construction must preserve the rule:

```text
retrieved content = evidence
not system instruction
```

---

# 23. Logging Safety

Do not log:

```text
full document content
raw request body
sensitive metadata
```

Safer operational fields can include:

```text
document_id
content_type
byte_size
request_id
```

where consistent with project logging policy.

---

# 24. Error Semantics

Input errors should remain distinct from infrastructure failures.

Examples:

```text
blank title
empty content
unsupported content type
document too large
invalid document ID
RAG disabled
```

Do not expose:

```text
stack traces
database errors
provider secrets
internal paths
```

through public validation errors.

---

# 25. `RAGSettings.enabled`

RAG-01 added:

```text
enabled = False
```

A structurally valid ingestion request may still be rejected because RAG is disabled.

Important distinction:

```text
Request schema validity
!=
Feature activation
```

Feature activation is application/runtime policy.

---

# 26. Application Input Model

A useful application-level command may be:

```text
IngestDocumentInput
```

Conceptually:

```text
IngestDocumentInput
├── document_id
├── title
├── source
├── content_type
└── content
```

The exact final structure should match the code.

This makes future ingestion usable from:

```text
FastAPI
CLI
worker
tests
another service
```

without depending on HTTP-specific schemas.

---

# 27. Why This Helps Durable Ingestion Later

Future:

```text
HTTP Request
   ↓
IngestDocumentInput
   ↓
Queue / Worker
   ↓
IndexDocumentUseCase
```

Because the application input is independent of FastAPI, the same workflow can move to durable processing without redesigning the core contract.

---

# 28. What RAG-05 Intentionally Does Not Implement

Do not confuse request validation with the rest of RAG.

RAG-05 should not implement:

```text
PDF parsing
Markdown parsing
OCR
normalization
chunking
checksum/idempotency orchestration
embedding calls
Qdrant writes
background jobs
retrieval
generation
```

It answers only:

> Is this knowledge-submission request acceptable?

---

# 29. Why Loading Is RAG-06

RAG-05:

```text
Is the request valid?
```

RAG-06:

```text
How do I convert the accepted source into LoadedDocumentContent?
```

Example:

```text
text/markdown
   ↓
Markdown loader
   ↓
LoadedDocumentContent
```

Keeping validation separate from extraction makes each layer easier to test and replace.

---

# 30. Why Chunking Is Later

RAG-01 already defines:

```text
chunk_size
chunk_overlap
```

But RAG-05 should not split content.

Chunking belongs later:

```text
LoadedDocumentContent
   ↓
Normalizer
   ↓
TextChunker
   ↓
DocumentChunk[]
```

---

# 31. Recommended Test Coverage

Tests should cover:

```text
valid plain text
valid Markdown
blank title rejected
blank content rejected
whitespace-only content rejected
unsupported content type rejected
document byte limit
Unicode byte-size behavior
exact max boundary
one byte above max
DTO → application input mapping
internal lifecycle fields not caller-controlled
```

---

# 32. Why Unicode Tests Matter

These may have different byte counts:

```text
"hello"
"नमस्ते"
```

Testing Unicode proves that:

```text
max_document_bytes
```

actually means bytes rather than characters.

---

# 33. Why Mapping Tests Matter

If:

```text
RAGIngestionRequest
```

maps to:

```text
IngestDocumentInput
```

tests should confirm that required business data is preserved and HTTP-only or unvalidated state does not leak into the application layer.

---

# 34. Example Valid Request

Conceptually:

```json
{
  "document_id": "employee-handbook",
  "title": "Employee Handbook",
  "source": "manual-upload",
  "content_type": "text/plain",
  "content": "Employees receive 20 annual leave days each year."
}
```

RAG-05 validates it.

It does not yet chunk, embed, or index it.

---

# 35. Example Invalid Request — Empty Content

```json
{
  "document_id": "employee-handbook",
  "title": "Employee Handbook",
  "content_type": "text/plain",
  "content": "   "
}
```

Expected:

```text
reject
```

---

# 36. Example Invalid Request — Unsupported Type

```json
{
  "title": "Executable",
  "content_type": "application/x-executable",
  "content": "..."
}
```

Expected:

```text
reject
```

because the loader pipeline does not support it.

---

# 37. Example Invalid Request — Client-Controlled Status

```json
{
  "title": "Handbook",
  "content_type": "text/plain",
  "content": "...",
  "status": "INDEXED"
}
```

The caller must not be able to control processing lifecycle state.

---

# 38. Example Invalid Request — Oversized Content

```text
encoded document bytes
>
RAGSettings.max_document_bytes
```

Expected:

```text
reject before expensive processing
```

---

# 39. How RAG-05 Connects to RAG-01

RAG-01 defines policy.

RAG-05 begins applying it.

Example:

```text
RAGSettings.max_document_bytes
   ↓
Ingestion validation
```

This is the first practical connection between RAG configuration and incoming knowledge.

---

# 40. How RAG-05 Connects to RAG-02/03/04

RAG-02/03/04 create and expose persistent lifecycle state.

RAG-05 creates the safe input that will eventually become a `Document`.

```text
Client Request
   ↓
RAG-05 Validation
   ↓
Application Input
   ↓
Future IndexDocumentUseCase
   ↓
Document(status=RECEIVED)
   ↓
DocumentRepositoryPort
   ↓
PostgreSQL
```

---

# 41. Ownership Summary

| Concern | Typical Owner |
|---|---|
| title | caller |
| content | caller |
| content type | caller, from supported set |
| source | caller/application depending final contract |
| document ID | explicit RAG-05 decision |
| document version | application |
| checksum | application |
| status | application |
| chunking strategy | application / RAGSettings |
| embedding provider/model | application / RAGSettings |
| index version | application / RAGSettings |
| timestamps | application/database |
| vector index | application/Qdrant adapter |

---

# 42. Engineering Lessons

## External input is not domain state

The client supplies knowledge, not lifecycle truth.

## Validate before expensive work

Reject invalid requests before extraction, embedding, and vector writes.

## Limits are architectural controls

`max_document_bytes` protects cost, memory, latency, capacity, and security.

## Configuration should drive runtime policy

Do not duplicate size limits as magic constants.

## DTOs and application commands have different purposes

Separating them makes the ingestion workflow reusable.

## The application owns processing policy

Clients should not decide status, checksums, embedding models, or index versions.

---

# 43. Beginner Mental Model

Think of ingestion like receiving a parcel.

Before opening it, you check:

```text
Is the label valid?
Is this parcel type supported?
Is it too large?
Is there anything inside?
```

That is RAG-05.

Later:

```text
open parcel                → RAG-06 loader
organize contents          → RAG-07 chunker
create searchable vectors  → RAG-08/09 embeddings
store semantic index       → RAG-10/11 Qdrant
```

---

# 44. Before vs After RAG-05

| Before | After |
|---|---|
| no clear ingestion request contract | typed ingestion boundary |
| unclear supported input | explicit supported content types |
| unclear lifecycle ownership | caller vs application ownership |
| size configuration not enforced at ingestion | byte-size policy can be applied |
| API/domain boundary ambiguous | DTO/application input separation |
| internal fields could be conceptually ambiguous | processing state protected |
| no ingestion validation suite | focused request/policy tests |

Only retain rows that match the final repository implementation when synchronizing this guide.

---

# 45. What Comes Next — RAG-06

RAG-06 answers:

> Once input is valid, how do we turn it into `LoadedDocumentContent`?

Future:

```text
Validated Input
   ↓
DocumentLoaderPort
   ↓
PlainText / Markdown / later PDF Loader
   ↓
LoadedDocumentContent
```

RAG-05 makes RAG-06 simpler because loaders can assume the input already passed front-door validation.

---

# 46. Final Takeaway

RAG-05 creates the **trusted application boundary around untrusted external knowledge**.

The client says:

```text
Here is the knowledge I want to ingest.
```

The application decides:

```text
Is it valid?
Is it small enough?
Is its type supported?
What version is it?
What checksum does it have?
What status is it in?
How should it be chunked?
Which embedding model should process it?
Which index version should receive it?
```

The simplified flow is:

```text
UNTRUSTED INPUT
      ↓
RAG-05 VALIDATION
      ↓
SAFE APPLICATION INPUT
      ↓
RAG-06+ PROCESSING PIPELINE
```

That front-door contract is necessary before the system begins expensive and stateful RAG processing.
