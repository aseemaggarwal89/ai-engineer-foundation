# ADR-RAG-001: Generic Enterprise RAG Architecture

## Status

Accepted

## Date

2026-08-08

## Context

The project already has a reusable AI generation platform:

- `AIInferencePort`
- `InferenceRouter`
- `ModelRegistry`
- `OllamaAdapter`
- `OpenAIAdapter`
- provider retry, timeout, fallback, and circuit breaker controls
- Redis-backed AI response cache pattern
- structured logging, metrics, tracing, and safe exception handling

The RAG readiness assessment concluded that RAG should build on this platform instead of duplicating model-provider infrastructure.

RAG also needs new application concepts that do not currently exist:

- documents
- document chunks
- ingestion lifecycle
- embedding/indexing lifecycle
- vector-store boundary
- retrieval
- RAG prompt construction
- citations and provenance
- no-context response semantics
- RAG-specific validation, observability, and testing

## Decision

### Decision 1: RAG is an application workflow, not a provider

RAG is defined as:

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

RAG is not an AI provider, not a vector database, and not a simple provider-routing capability.

The project will not add `AICapability.RAG` merely to route generation calls.

### Decision 2: `AIInferencePort` remains responsible for text generation

The final generation step of RAG will reuse:

```text
AIInferencePort
-> InferenceRouter
-> ModelRegistry
-> OllamaAdapter / OpenAIAdapter
```

RAG code will not create duplicate OpenAI or Ollama text-generation clients.

### Decision 3: The generic `EmbeddingPort` will be evolved and reused

Embeddings are generic AI infrastructure, not RAG-only infrastructure.

The existing contract remains owned by:

```text
app/application/ai/domain/embedding_port.py
```

RAG ingestion and RAG retrieval will use that generic embedding boundary. A batch/result-oriented revision is deferred to `RAG-08`.

### Decision 4: RAG does not get duplicate generation adapters

RAG will not introduce separate `RAGOllamaAdapter` or `RAGOpenAIAdapter` classes for text generation.

Provider-specific generation behavior remains isolated in existing provider adapters.

### Decision 5: Vector storage is accessed through `VectorStorePort`

Application code will depend on:

```text
app/application/ai/rag/domain/vector_store_port.py
```

not on Qdrant, pgvector, or any vector-store SDK.

### Decision 6: PostgreSQL remains authoritative for document and index lifecycle metadata

PostgreSQL will own durable metadata such as:

- document identity
- document metadata
- document version
- checksum
- ingestion state
- indexing state
- processing versions
- timestamps

### Decision 7: Vector storage is a rebuildable retrieval index

The vector store owns:

- embedding vectors
- chunk retrieval representation
- similarity-search metadata

It must not be the sole authoritative document store.

### Decision 8: Document ingestion and RAG querying are separate workflows

Ingestion changes the knowledge base.

Querying reads the knowledge base and produces grounded answers.

They will have separate use cases, validation, observability, and failure handling.

### Decision 9: Retrieved context is untrusted evidence

Retrieved documents are evidence, not instructions.

Retrieved context must never override system-level RAG instructions.

### Decision 10: Grounded answers preserve citation provenance

The provenance chain must be preserved:

```text
Document
-> DocumentChunk
-> EmbeddedChunk
-> RetrievedChunk
-> RAG context
-> Citation
```

Citations must be derived from retrieval metadata, not guessed after generation.

### Decision 11: No-context behavior does not fall back to unrestricted model knowledge

When retrieval finds no sufficiently relevant evidence, RAG returns a deterministic no-context result.

The absence of evidence is normal application behavior, not permission to answer from unrestricted model memory.

### Decision 12: Processing behavior that affects indexing or retrieval is versioned

Future RAG implementation must track version identities for:

- `document_version`
- `chunking_version`
- `embedding_provider`
- `embedding_model`
- `embedding_version`
- `index_version`
- `retrieval_policy_version`
- `rag_prompt_version`

## Dependency Direction

The architecture preserves the existing direction:

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

Infrastructure SDK types must not escape into application or use-case code.

## Alternatives Considered

### LangChain-first architecture

Rejected for the initial implementation.

The project is explicitly learning and demonstrating backend architecture through ports, adapters, and explicit workflows. LangChain may be evaluated later as an infrastructure/tooling choice.

### LlamaIndex-first architecture

Rejected for the initial implementation for the same reason as LangChain.

### Direct Qdrant usage in use cases

Rejected.

This would couple application workflows to vector database infrastructure and make future vector-store changes harder.

### `AICapability.RAG`

Rejected/deferred.

RAG is a composed workflow, not a single provider operation.

### Vector database as the sole document store

Rejected.

This makes recovery, reindexing, migration, auditing, and lifecycle tracking unnecessarily fragile.

### Embeddings through `AIInferencePort.generate()`

Rejected.

Embedding and generation have different input/output contracts and lifecycle semantics.

## Consequences

Positive:

- RAG stays understandable as an application workflow.
- Existing generation infrastructure remains reusable.
- The architecture avoids vendor lock-in and SDK leakage.
- PostgreSQL and vector storage have clear ownership boundaries.
- No-context and citation behavior are explicit from the start.
- Future enterprise concerns such as tenancy, authorization filters, and reindexing have extension points.

Tradeoffs:

- More explicit contracts must be built before a quick RAG demo exists.
- Later tasks must wire infrastructure carefully instead of directly importing SDK clients into use cases.
- Embedding support needs a future contract revision before production ingestion.

## Follow-Up Tasks

- `RAG-01` — RAG Settings Skeleton
- `RAG-02` — Document and Chunk Metadata Models
- `RAG-03` — Alembic Document Migration
- `RAG-08` — EmbeddingPort Revision
- `RAG-10` — VectorStorePort infrastructure wiring
- `RAG-11` — Qdrant Adapter
