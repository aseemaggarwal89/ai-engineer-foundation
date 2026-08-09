# Enterprise RAG Implementation Progress

## Status Legend

- ⬜ Not Started
- 🟡 In Progress
- ✅ Completed
- ⛔ Blocked
- 🔄 Revisit

## Foundation

| ID | Task | Status | Notes |
|---|---|---|---|
| RAG-PRE-01 | Architecture Readiness Assessment | ✅ | Completed in `docs/architecture/rag-readiness-assessment.md` |
| RAG-00 | Architecture ADR and Domain Contracts | ✅ | Completed |
| RAG-01 | RAG Settings Skeleton | ✅ | Completed |
| RAG-02 | Document and Chunk Metadata Models | ✅ | Completed |
| RAG-03 | Alembic Migration for RAG Document Metadata | ✅ | Completed |
| RAG-04 | Document Repository | ⬜ | Deferred |

## Ingestion

| ID | Task | Status |
|---|---|---|
| RAG-05 | Ingestion Request Schema and Validation | ✅ |
| RAG-06 | Document Loader / Extraction | ⬜ |
| RAG-07 | Normalization and Chunking | ⬜ |
| RAG-08 | EmbeddingPort Revision | ⬜ |
| RAG-09 | Embedding Adapter Wiring | ⬜ |
| RAG-10 | VectorStorePort Infrastructure Wiring | ⬜ |
| RAG-11 | Qdrant Adapter | ⬜ |
| RAG-12 | IndexDocumentUseCase | ⬜ |
| RAG-13 | Durable Ingestion Lifecycle | ⬜ |

## Retrieval and Generation

| ID | Task | Status |
|---|---|---|
| RAG-14 | Retriever | ⬜ |
| RAG-15 | Dense Retrieval Baseline | ⬜ |
| RAG-16 | RAGPromptBuilder | ⬜ |
| RAG-17 | RAGQueryUseCase | ⬜ |
| RAG-18 | Citation Contract | ⬜ |
| RAG-19 | RAG Response Pipeline | ⬜ |

## Enterprise Hardening

| ID | Task | Status |
|---|---|---|
| RAG-20 | Security Hardening | ⬜ |
| RAG-21 | RAG Observability | ⬜ |
| RAG-22 | RAG Metrics | ⬜ |
| RAG-23 | RAG Cache | ⬜ |
| RAG-24 | Index Recovery | ⬜ |
| RAG-25 | Embedding Migration | ⬜ |
| RAG-26 | Stable API + E2E | ⬜ |
| RAG-27 | Performance / Enterprise Readiness | ⬜ |

## Current Milestone

RAG-05 — Ingestion Request Schema and Validation

## Next Task

RAG-06 — Document Loader / Extraction

## Architecture Decisions

| ADR | Status | Summary |
|---|---|---|
| `docs/architecture/adr/ADR-RAG-001-generic-rag-architecture.md` | Accepted | RAG is an application workflow; generation reuses existing AI infrastructure; embeddings stay generic; PostgreSQL is authoritative; vector store is rebuildable |

## Known Risks / Technical Debt

| Area | Risk | Planned follow-up |
|---|---|---|
| Embeddings | Current `EmbeddingPort` supports one text and no metadata | RAG-08 |
| Persistence | Document ORM and migration exist; repository implementation is still missing | RAG-04 |
| Vector index | No vector-store adapter exists | RAG-10, RAG-11 |
| Retrieval | Retriever and retrieval policy are not implemented | RAG-14, RAG-15 |
| Security | Ingestion-specific validation and prompt-injection handling are not implemented | RAG-20 |
| Observability | RAG-specific logs, metrics, and traces are documented but not implemented | RAG-21, RAG-22 |
| Runtime wiring | RAG settings exist but do not start infrastructure or expose routes | RAG-05 and later |
| Retrieval score semantics | `minimum_score` is finite-only; final interpretation is deferred to vector-store/retriever policy | RAG-10, RAG-14 |
| RAG repository | RAG tables exist but no repository implementation has been added | RAG-04 |
| Ingestion lifecycle | Request validation exists, but no loader, checksum, repository write, chunking, embedding, or indexing workflow exists yet | RAG-06 and later |

## Learning / Decision Notes

### RAG-01A — Retrieval Score Semantics

- Removed premature `0..1` `minimum_score` contract.
- `minimum_score` is now a finite configurable threshold.
- Vector metric and score interpretation are intentionally deferred.
- Final score semantics will be decided during VectorStore/Qdrant/Retriever work.
- Reference: `docs/learning/rag/retrieval-score-semantics.md`

### RAG-02 — Document and Chunk Persistence Metadata

- Added `RAGDocumentORM` and `RAGDocumentChunkORM`.
- `document_id + document_version` is the logical document-version identity.
- `chunk_id` is the stable chunk identity.
- `document_id + document_version + chunking_version + chunk_index` is the chunk-position identity.
- PostgreSQL owns authoritative normalized chunk text for rebuildability.
- Qdrant remains the future rebuildable vector retrieval index.
- Migration completed in `RAG-03 — Alembic Migration for RAG Document Metadata`.
- Reference: `docs/learning/rag/document-and-chunk-persistence.md`

### RAG-03 — Alembic Migration for RAG Document and Chunk Metadata

- Added migration revision `1d9b86e3e5c4`.
- Created `rag_documents` and `rag_document_chunks`.
- `rag_document_chunks.document_pk` references `rag_documents.id` with `ON DELETE CASCADE`.
- Enforced document-version identity with `UNIQUE(document_id, document_version)`.
- Enforced chunk identity with `UNIQUE(chunk_id)` and chunk-position uniqueness.
- Added lookup indexes for document ID, document version, checksum, status, and chunk loading.
- Validated upgrade and downgrade paths in a disposable database test.
- Next repository task: `RAG-04 — Document Repository`.
- Reference: `docs/learning/rag/rag-database-schema.md`

### RAG-05 — Ingestion Request Schema and Validation

- Added HTTP-facing `RAGIngestionRequest` in `app/application/ai/rag/schemas/ingestion.py`.
- Added application-level `IngestDocumentInput` in `app/application/ai/rag/usecases/ingest_document_input.py`.
- Initial supported content types are `text/plain` and `text/markdown`.
- `document_id` is caller-supplied stable logical identity; the application still owns database primary keys.
- `document_version`, lifecycle status, checksum, embedding model, index version, and processing versions remain application-owned.
- Pydantic validates request structure, enum values, required text fields, safe document IDs, and forbids extra fields.
- `RAGIngestionRequestValidator` enforces `RAGSettings.max_document_bytes` using UTF-8 byte length.
- No ingestion route, loader, chunker, embedding, Qdrant, repository, or indexing workflow was added.
- Reference: `docs/learning/rag/rag-ingestion-request-validation.md`

## Validation History

| Task | Tests | Lint | Integration | Notes |
|---|---|---|---|---|
| RAG-PRE-01 | `pytest` passed | `flake8` passed | `docker compose config` passed | Readiness assessment only |
| RAG-00 | `.venv/bin/pytest` passed, 95 tests | `.venv/bin/flake8` passed | `docker compose config` passed | ADR, docs, Codex context, and domain contracts |
| RAG-01 | `.venv/bin/pytest` passed, 111 tests | `.venv/bin/flake8` passed | Not required | RAG settings skeleton |
| RAG-01A | `.venv/bin/pytest` passed, 124 tests | `.venv/bin/flake8` passed | Not required | Removed premature normalized retrieval-score assumption from settings and domain contracts |
| RAG-02 | `.venv/bin/pytest` passed, 131 tests | `.venv/bin/flake8` passed | Not required | Document and chunk ORM metadata models |
| RAG-03 | `.venv/bin/pytest` passed, 133 tests | `.venv/bin/flake8` passed | Disposable migration upgrade/downgrade passed | Alembic migration for RAG document/chunk metadata |
| RAG-05 | `.venv/bin/pytest` passed, 149 tests | `.venv/bin/flake8` passed | Not required | Ingestion request DTO, application input, and policy validation |
