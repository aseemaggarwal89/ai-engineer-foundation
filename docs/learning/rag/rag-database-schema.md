# RAG Database Schema

This note explains the database migration added in `RAG-03`.

It is written for someone learning how SQLAlchemy, Alembic, and PostgreSQL fit together in a backend project.

## 1. Why a Migration Is Needed

A SQLAlchemy model describes persistence structure in Python.

It does not automatically mean the database table exists.

The flow is:

```text
Python ORM Model
      |
      v
Alembic Migration
      |
      v
PostgreSQL Schema
```

The ORM model answers:

```text
What should this table look like in Python?
```

The Alembic migration answers:

```text
How do we change the real database to match this schema?
```

The PostgreSQL table is the actual persisted database structure.

## 2. ORM vs Migration vs Database

| Layer | Meaning |
| --- | --- |
| SQLAlchemy model | Python representation of persistence structure |
| Alembic migration | Versioned instruction for changing the database |
| PostgreSQL table | Actual persisted database structure |

This separation matters because every environment must evolve through the same database history.

## 3. Why Database Changes Are Versioned

Database schema changes must be reproducible across:

- developer machines
- test environments
- CI
- staging
- production

Without migrations:

```text
Developer A has table version X
Developer B has table version Y
Production has unknown version
```

Alembic gives the project:

```text
ordered schema history
```

For `RAG-03`, the migration revision is:

```text
1d9b86e3e5c4_create_rag_document_and_chunk_metadata.py
```

## 4. RAG Tables

The migration creates:

```text
rag_documents
rag_document_chunks
```

Conceptually:

```text
RAG Document
    |
    | 1
    |
    +----------- *
                |
             RAG Chunk
```

One document version can have many chunks.

## 5. `rag_documents`

The document table stores lifecycle and indexing metadata.

Important columns:

- `id`
- `document_id`
- `title`
- `source`
- `content_type`
- `document_version`
- `checksum`
- `status`
- `chunking_version`
- `embedding_provider`
- `embedding_model`
- `embedding_version`
- `index_version`
- `failure_reason`
- `created_at`
- `updated_at`
- `indexed_at`
- `deleted_at`

The logical document-version identity is:

```text
document_id + document_version
```

This means the same logical document version cannot be inserted twice.

## 6. Document Status

The migration creates the RAG document status enum:

```text
received
processing
indexed
failed
deleted
```

These values match the domain enum:

```text
DocumentStatus
```

The database stores the lowercase domain values so persistence can map cleanly back to the application model.

## 7. `rag_document_chunks`

The chunk table stores chunk metadata and authoritative normalized chunk text.

Important columns:

- `id`
- `chunk_id`
- `document_pk`
- `document_id`
- `document_version`
- `chunk_index`
- `text`
- `chunking_version`
- `embedding_provider`
- `embedding_model`
- `embedding_version`
- `index_version`
- `section`
- `page_number`
- `source`
- `created_at`

The `text` column stores normalized chunk text.

It does not store embeddings or vectors.

## 8. Foreign Keys

A foreign key is a database rule ensuring a child row references a valid parent row.

For RAG:

```text
Chunk
cannot belong to
a nonexistent Document
```

The migration enforces:

```text
rag_document_chunks.document_pk
    -> rag_documents.id
```

with:

```text
ON DELETE CASCADE
```

That means deleting a document version row deletes its chunk rows.

## 9. Unique Constraints

Unique constraints protect logical identity.

The document table has:

```text
UNIQUE(document_id, document_version)
```

The chunk table has:

```text
UNIQUE(chunk_id)
```

and:

```text
UNIQUE(document_id, document_version, chunking_version, chunk_index)
```

These constraints help prevent duplicate logical state during retries, reindexing, or duplicate ingestion.

## 10. Check Constraints

The chunk table also includes simple integrity checks:

```text
chunk_index >= 0
```

and:

```text
page_number IS NULL OR page_number >= 1
```

These enforce domain-safe values at the database level.

## 11. PostgreSQL Indexes

PostgreSQL indexes optimize relational lookups.

RAG-03 adds indexes for:

- lookup by `document_id`
- lookup by `document_id + document_version`
- lookup by `checksum`
- lookup by `status`
- loading chunks by parent document primary key
- loading chunks by `document_id + document_version`

These support future repository operations such as:

- find a document
- check idempotency by checksum
- list documents by status
- load chunks for reindexing or citation provenance

## 12. PostgreSQL Index vs Qdrant Vector Index

These are different concepts.

| Concept | PostgreSQL Index | Qdrant Vector Index |
| --- | --- | --- |
| Purpose | Relational lookup | Semantic retrieval |
| Example | Lookup by `document_id` | Nearest embedding search |
| Data | Scalar/text columns | Vectors + payload |
| Source of truth | Supports authoritative DB | Rebuildable retrieval index |
| Added in | RAG-03 | Later Qdrant task |

PostgreSQL indexes do not perform semantic search.

Qdrant indexes do not own authoritative document lifecycle state.

## 13. Why Chunk Text Is in PostgreSQL

PostgreSQL stores authoritative normalized chunk text.

Qdrant remains rebuildable.

If Qdrant is lost:

```text
read chunks from PostgreSQL
    |
    v
regenerate embeddings
    |
    v
rebuild Qdrant
```

This is why the migration includes a `text` column in `rag_document_chunks`, but no vector column.

## 14. What RAG-03 Does Not Add

RAG-03 does not implement:

- document repository
- ingestion flow
- file upload
- PDF extraction
- chunking
- embedding calls
- Qdrant SDK
- Qdrant client
- vector search
- retriever
- RAG API

It only creates the physical schema for the RAG persistence metadata designed in `RAG-02`.
