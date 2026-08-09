# Generic Enterprise RAG Architecture

This is the living architecture document for RAG in `ai-engineer-foundation`.

The formal decision record is:

```text
docs/architecture/adr/ADR-RAG-001-generic-rag-architecture.md
```

The readiness assessment is:

```text
docs/architecture/rag-readiness-assessment.md
```

## Definition

RAG is an application workflow.

It is not:

- a model provider
- a vector database
- a provider-routing shortcut
- a single `AICapability.RAG` operation

Conceptually, RAG means:

```text
document ingestion
+ document processing
+ embedding
+ vector indexing
+ retrieval
+ context construction
+ text generation
+ citation/provenance handling
+ response validation
```

## Existing AI Infrastructure Reused by RAG

RAG reuses the current generation platform:

| Component | Path | RAG responsibility |
| --- | --- | --- |
| `AIInferencePort` | `app/application/ai/domain/ai_inference_port.py` | Text generation for final RAG answers |
| `InferenceRouter` | `app/application/ai/infrastructure/inference_router.py` | Primary/fallback provider execution |
| `ModelRegistry` | `app/core/model_registry.py` | Capability-to-provider route lookup |
| `OllamaAdapter` | `app/application/ai/infrastructure/ollama_adapter.py` | Local text generation |
| `OpenAIAdapter` | `app/application/ai/infrastructure/openai_adapter.py` | Cloud text generation |
| `EmbeddingPort` | `app/application/ai/domain/embedding_port.py` | Generic embedding boundary |
| `RedisAIResponseCache` | `app/application/ai/infrastructure/redis_ai_cache.py` | Cache pattern, not direct RAG cache yet |
| `PipelineRegistry` | `app/application/ai/core/pipeline_registry.py` | Response-pipeline pattern |
| Exception hierarchy | `app/domain/exceptions/exceptions.py` | Safe application and AI errors |
| Observability | `app/core/*` | Logging, metrics, tracing, request IDs |

The final RAG generation step will use:

```text
RAGQueryUseCase
-> RAGPromptBuilder
-> AIInferencePort.generate(...)
-> InferenceRouter
-> ModelRegistry
-> OllamaAdapter / OpenAIAdapter
```

## Configuration

RAG configuration is nested under the existing AI settings model because RAG is an AI application workflow.

Settings path:

```text
Settings
└── ai: AISettings
    └── rag: RAGSettings
        ├── embedding: EmbeddingSettings
        └── vector_store: VectorStoreSettings
```

Environment variables use the repository's existing nested delimiter:

```text
AI__RAG__ENABLED=false
AI__RAG__CHUNK_SIZE=800
AI__RAG__CHUNK_OVERLAP=120
AI__RAG__RETRIEVAL_TOP_K=5
AI__RAG__MINIMUM_SCORE=0.3
AI__RAG__MAX_DOCUMENT_BYTES=5242880
AI__RAG__EMBEDDING__MODEL=text-embedding-3-small
AI__RAG__VECTOR_STORE__PROVIDER=qdrant
AI__RAG__VECTOR_STORE__URL=http://qdrant:6333
AI__RAG__VECTOR_STORE__COLLECTION=documents
```

RAG is disabled by default. These settings do not create Qdrant clients, embedding clients, routes, repositories, or runtime RAG services.

`minimum_score` is a configured retrieval threshold, but the configuration layer does not define a normalized score range. Retrieval-score ranges are not globally normalized by RAG configuration. Score and distance semantics belong to the retrieval policy and vector-store adapter contract, and will be finalized when the retriever and vector-store adapter are implemented.

Detailed learning note:

```text
docs/learning/rag/retrieval-score-semantics.md
```

## Architectural Boundaries

### Generic AI Infrastructure

Reusable across AI features:

- `AIInferencePort`
- `InferenceRouter`
- `ModelRegistry`
- `OllamaAdapter`
- `OpenAIAdapter`
- `EmbeddingPort`
- provider resilience controls
- Redis infrastructure
- logging, metrics, tracing
- exception infrastructure

### RAG Application Workflow

New RAG-owned behavior:

- documents
- chunks
- ingestion
- retrieval
- RAG prompt construction
- citations
- RAG response validation
- no-context semantics

### Future RAG Infrastructure Adapters

Deferred infrastructure:

- SQLAlchemy document repository
- document parsers
- Qdrant or pgvector adapter
- embedding provider wiring
- durable ingestion workers

## Dependency Direction

RAG must follow the existing architecture:

```text
HTTP
 |
 v
Use Case
 |
 v
Application Service / Domain Port
 |
 v
Infrastructure Adapter
```

Use cases may depend on domain ports.

Infrastructure adapters may implement domain ports.

Domain contracts must not import FastAPI, SQLAlchemy, Redis, OpenAI, Qdrant, or HTTP clients.

## RAG Query Flow

Target workflow:

```text
RAG Route
    |
    v
RAGQueryUseCase
    |
    +--> QueryGuardrails
    |
    +--> Retriever
    |       |
    |       +--> EmbeddingPort
    |       |
    |       +--> VectorStorePort
    |
    +--> RAGPromptBuilder
    |
    +--> existing AIInferencePort
    |
    +--> RAGResponsePipeline
    |
    v
RAGResult(answer, citations, status)
```

No RAG route or use case is implemented in `RAG-00`.

## Document Ingestion Flow

Target workflow:

```text
Document Route
      |
      v
Ingestion Request DTO
      |
      v
Application Input
      |
      v
IndexDocumentUseCase
      |
      +--> DocumentLoaderPort
      |
      +--> TextNormalizer
      |
      +--> TextChunker
      |
      +--> EmbeddingPort
      |
      +--> VectorStorePort
      |
      +--> DocumentRepositoryPort
```

No ingestion route, parser, chunker, embedding batch implementation, repository, or vector store is implemented yet.

`RAG-05` defines only the ingestion request boundary:

- callers provide `document_id`, `title`, `source`, `content_type`, and `content`
- supported initial content types are `text/plain` and `text/markdown`
- `document_id` is caller-supplied logical identity, not the database primary key
- `document_version`, lifecycle status, checksum, embedding model, index version, and processing versions are application-owned
- request DTOs map into application inputs before a future use case executes
- document size is validated against `RAGSettings.max_document_bytes` using UTF-8 byte length

## Package Structure

Initial RAG package:

```text
app/application/ai/rag/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── chunk.py
│   ├── citation.py
│   ├── document.py
│   ├── document_loader_port.py
│   ├── document_repository_port.py
│   ├── rag_result.py
│   ├── retrieval.py
│   └── vector_store_port.py
├── infrastructure/
│   └── __init__.py
├── prompts/
│   └── __init__.py
├── services/
│   └── __init__.py
├── schemas/
│   ├── __init__.py
│   └── ingestion.py
├── usecases/
│   ├── __init__.py
│   └── ingest_document_input.py
└── validators/
    ├── __init__.py
    └── ingestion_request_validator.py
```

Some subpackages still reserve architectural locations. `RAG-05` adds the first ingestion boundary without adding the final ingestion route or processing workflow.

## Domain Contracts

### `Document`

Path:

```text
app/application/ai/rag/domain/document.py
```

Represents framework-independent document metadata.

Required v1 fields:

- `document_id`
- `title`
- `source`
- `content_type`
- `version`
- `checksum`
- `status`
- `created_at`
- `updated_at`

Future extension fields may include:

- `namespace`
- `tenant_id`
- `organization_id`
- `visibility`

These are intentionally not required for generic RAG v1.

### `DocumentStatus`

Initial lifecycle:

```text
RECEIVED
   |
   v
PROCESSING
   |
   +------> INDEXED
   |
   +------> FAILED

INDEXED
   |
   +------> PROCESSING
   |
   +------> DELETED

FAILED
   |
   +------> PROCESSING
   |
   +------> DELETED
```

`PENDING` and `REINDEXING` are deferred until the implementation proves they are needed.

### `DocumentChunk`

Path:

```text
app/application/ai/rag/domain/chunk.py
```

Represents a chunk derived from a specific document version and chunking version.

Chunk IDs should eventually be deterministic:

```text
hash(document_id + document_version + chunking_version + chunk_index + normalized chunk content)
```

The final hash algorithm is deferred.

### `EmbeddedChunk`

Wraps a `DocumentChunk` with:

- embedding vector
- embedding model
- embedding version

This lets the vector store receive a complete application-owned indexing input without knowing about parser or embedding SDK types.

### `Citation`

Path:

```text
app/application/ai/rag/domain/citation.py
```

Provider-independent citation representation.

It intentionally does not expose:

- Qdrant point ID
- Qdrant collection name
- embedding vector
- internal database primary key

### Retrieval Models

Path:

```text
app/application/ai/rag/domain/retrieval.py
```

Application-owned retrieval types:

- `RetrievalQuery`
- `RetrievedChunk`
- `RetrievalResult`

Vector-store-specific result objects must be mapped into these types by infrastructure adapters.

### `RAGResult`

Path:

```text
app/application/ai/rag/domain/rag_result.py
```

Framework-independent result contract:

```text
answer
citations
status
```

Current statuses:

- `ANSWERED`
- `NO_CONTEXT`

No-context is a normal result, not an exception.

## Ports

### `DocumentLoaderPort`

Path:

```text
app/application/ai/rag/domain/document_loader_port.py
```

Extraction boundary for plain text, Markdown, PDF, or future source types.

Parser SDK types must not leak through this boundary.

### `DocumentRepositoryPort`

Path:

```text
app/application/ai/rag/domain/document_repository_port.py
```

Authoritative document metadata and ingestion lifecycle boundary.

The future implementation should support:

- idempotent ingestion
- status updates
- checksum lookup
- chunk metadata persistence
- deletion
- recovery and reindexing

### `VectorStorePort`

Path:

```text
app/application/ai/rag/domain/vector_store_port.py
```

Provider-independent vector index boundary.

Operations:

- `upsert_chunks`
- `search`
- `delete_document`
- `health`

The port accepts `EmbeddedChunk` and returns `RetrievalResult`.

## Retriever Abstraction Decision

`RAG-00` does not create a `RetrieverPort`.

The preferred starting design is:

```text
Retriever
    |
    +--> EmbeddingPort
    +--> VectorStorePort
```

If `Retriever` is an application service with no external implementation variants, an extra port adds symmetry but not value.

This can be revisited if multiple retrieval strategies need swappable implementations.

## No-Context Semantics

When retrieval returns no sufficiently relevant evidence:

```text
RAG should not answer from unrestricted model memory.
```

The result should be deterministic application behavior:

```text
status = NO_CONTEXT
citations = []
answer = controlled no-context message
```

The exact user-facing message will be decided with the HTTP API.

## Data Ownership

### PostgreSQL

Future source of truth for:

- document identity
- document metadata
- document version
- checksum
- ingestion state
- index state
- normalized chunk text
- chunk identity and provenance
- processing versions
- timestamps

PostgreSQL stores authoritative normalized chunk text so the vector index can be rebuilt without requiring the original uploaded file to still be available.

RAG document versions use `(document_id, document_version)` as their logical database identity. Chunk rows reference the internal document row primary key with `ON DELETE CASCADE`, so deleting a document-version row also removes its stored chunks.

### Vector Store

Future owner of:

- embedding vectors
- chunk retrieval representation
- similarity-search metadata

It is a rebuildable retrieval index.

The vector store does not own authoritative document text.

### Redis

Future optional use:

- RAG answer cache
- short-lived coordination/cache data

Redis is not document persistence.

## Versioning Model

Enterprise RAG needs reproducibility.

Future implementation must track:

- `document_version`
- `chunking_version`
- `embedding_provider`
- `embedding_model`
- `embedding_version`
- `index_version`
- `retrieval_policy_version`
- `rag_prompt_version`

Why this matters:

| Change | Impact |
| --- | --- |
| Document changed | Vectors may be stale |
| Chunker changed | Vectors may be stale |
| Embedding model changed | Vectors may be incompatible or semantically different |
| Retrieval policy changed | Answer-cache semantics change |
| Prompt changed | Generation behavior changes |

## Idempotency Model

Future ingestion should identify logical work using:

```text
document identity
+ content checksum
+ document version
+ chunking version
+ embedding version
+ index version
```

The goal:

```text
same input + same processing configuration = no duplicate logical index
```

## Security Boundaries

### Query Validation

RAG queries can reuse existing AI guardrail concepts where appropriate:

- `AISafetyFilter`
- `AIGuardrails`
- request size limits
- safe exception handling

### Ingestion Security

Future ingestion requires:

- file type validation
- size limits
- extraction limits
- source validation
- PII/secret policy
- malicious document handling

### Retrieved Context Safety

Retrieved context is untrusted evidence.

Retrieved documents must never override system instructions.

Prompt-injection detection is deferred.

## Observability Contract

Future ingestion events:

- `rag_document_received`
- `rag_ingestion_started`
- `rag_document_indexed`
- `rag_ingestion_failed`
- `rag_document_deleted`

Future query events:

- `rag_query_started`
- `rag_retrieval_completed`
- `rag_no_context`
- `rag_generation_completed`
- `rag_query_completed`
- `rag_query_failed`

Future trace shape:

```text
rag.query
    |
    +-- rag.embed_query
    +-- rag.retrieve
    +-- rag.build_context
    +-- ai.generate
    +-- rag.validate_response
```

Ingestion trace:

```text
rag.ingest
    |
    +-- rag.extract
    +-- rag.normalize
    +-- rag.chunk
    +-- rag.embed_chunks
    +-- rag.vector_upsert
```

Prometheus labels must stay low-cardinality.

Do not use raw queries, document content, retrieved text, document IDs, or request IDs as metric label values.

## Testing Strategy

### Unit Tests

No infrastructure required:

- text chunker
- RAG prompt builder
- retriever
- index document use case
- RAG query use case
- RAG response pipeline

Use fakes:

- `FakeEmbeddingPort`
- `FakeVectorStore`
- `FakeDocumentRepository`
- `FakeDocumentLoader`
- `FakeAIInferencePort`

### Integration Tests

Use real local infrastructure only when the task introduces infrastructure:

- PostgreSQL
- Qdrant or pgvector
- Redis

### RAG Evaluation Tests

Future first-class category:

- retrieval Recall@K
- MRR
- citation correctness
- groundedness
- no-context correctness
- regression dataset

## Future Enterprise Extension Points

The generic v1 architecture does not include OdinSync or tenant-specific fields.

It leaves extension points for:

- namespace
- authorization filters
- document ownership
- tenant-aware retrieval
- service-to-service authentication
- visibility policies

These should be added only when the generic architecture needs them.
