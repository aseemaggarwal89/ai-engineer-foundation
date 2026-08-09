# RAG Codex Context

## Project

AI Engineer Foundation

## Objective

Build a generic, production-oriented RAG capability that can later be consumed by enterprise applications without coupling the RAG architecture to any specific application.

## Existing Architecture

Reuse:

- `AIInferencePort`
- `InferenceRouter`
- `ModelRegistry`
- `OllamaAdapter`
- `OpenAIAdapter`
- generic `EmbeddingPort`
- `ServiceContainer` pattern
- Redis infrastructure and cache patterns
- guardrails
- exception handling
- logging
- metrics
- tracing
- retry, timeout, and circuit breakers

## Core Architecture Rules

1. RAG is an application workflow.
2. Do not create `AICapability.RAG` solely for provider routing.
3. Use existing `AIInferencePort` for RAG generation.
4. Do not duplicate OpenAI/Ollama generation clients.
5. Embeddings use generic `EmbeddingPort`.
6. Do not create a RAG-specific duplicate embedding abstraction without architectural justification.
7. Application code must depend on `VectorStorePort`, not Qdrant.
8. PostgreSQL owns authoritative document/index lifecycle metadata.
9. Vector DB is a rebuildable retrieval index.
10. Redis is cache/temporary infrastructure, not document storage.
11. Document ingestion and RAG querying are separate workflows.
12. Retrieved context is untrusted evidence.
13. No relevant context must not silently become unrestricted model answering.
14. Preserve provenance for citations.
15. Version document processing, chunking, embeddings, indexes, retrieval policy, and RAG prompts.
16. Keep infrastructure SDK objects out of use cases.
17. Do not log raw documents, raw queries, retrieved context, secrets, or embeddings by default.
18. Avoid high-cardinality Prometheus labels.
19. Keep RAG generic; do not introduce OdinSync-specific concepts yet.
20. Do not add LangChain/LlamaIndex merely for convenience.
21. RAG settings live under `AISettings` and use `AI__RAG__...` environment variables.
22. Do not assume retrieval scores are normalized to `0..1`; score semantics must be defined by the retrieval/vector-store contract.
23. PostgreSQL persists authoritative normalized chunk text and lifecycle metadata; Qdrant stores the rebuildable vector retrieval index.
24. RAG document versions use `(document_id, document_version)` as the database logical identity.
25. RAG ingestion clients may supply stable document identity and text content, but they cannot set lifecycle status, checksum, embedding model, index version, or processing versions.
26. RAG HTTP ingestion DTOs must stay separate from domain models and application inputs.

## Expected RAG Query Flow

```text
RAGQueryUseCase
-> query guardrails
-> Retriever
-> EmbeddingPort
-> VectorStorePort
-> RAGPromptBuilder
-> existing AIInferencePort
-> RAGResponsePipeline
-> RAGResult with citations
```

## Expected Ingestion Flow

```text
IndexDocumentUseCase
-> validation
-> DocumentLoaderPort
-> normalization
-> TextChunker
-> EmbeddingPort
-> VectorStorePort
-> DocumentRepositoryPort
```

## Working Method

For every RAG task:

1. inspect existing implementation first;
2. avoid duplicate abstractions;
3. implement only the current task scope;
4. add tests;
5. run configured quality checks;
6. update `docs/architecture/rag-progress.md`;
7. update architecture docs if decisions change;
8. report files changed and remaining risks.

## Current Task Bootstrap

Read:

- `docs/architecture/rag-readiness-assessment.md`
- `docs/architecture/adr/ADR-RAG-001-generic-rag-architecture.md`
- `docs/architecture/rag-architecture.md`
- `docs/architecture/rag-progress.md`
- `docs/prompts/rag-codex-context.md`

Implement only the next planned RAG task unless explicitly instructed otherwise.

# RAG Task Prompt Template

Task:

```text
RAG-XX — <Task Name>
```

Before implementation:

1. Read:
   - RAG readiness assessment
   - RAG architecture ADR
   - RAG architecture overview
   - RAG progress tracker
   - RAG Codex context
2. Inspect the current implementation relevant to this task.
3. Treat the repository as the source of truth.

Implementation rules:

- implement only `RAG-XX`;
- preserve existing architecture;
- do not duplicate working infrastructure;
- add unit tests;
- add integration tests where infrastructure is involved;
- update architecture documentation if behavior changes;
- update `rag-progress.md` before finishing.

Final report:

1. What was implemented
2. Architecture decisions
3. Files changed
4. Tests added
5. Validation results
6. Remaining risks
7. Recommended next RAG task
