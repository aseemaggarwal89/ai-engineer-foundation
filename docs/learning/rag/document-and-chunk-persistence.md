# Document and Chunk Persistence in RAG

This note explains the persistence metadata added in `RAG-02`.

The goal is to make RAG document ingestion recoverable and reindexable without coupling the domain model to SQLAlchemy or storing vectors in PostgreSQL.

## 1. Document vs Document ORM Model

There are two different concepts:

```text
Document
=
application/domain concept
```

and:

```text
RAGDocumentORM
=
database representation
```

The domain model lives in:

```text
app/application/ai/rag/domain/document.py
```

The persistence model lives in:

```text
app/db/models/rag_document_orm.py
```

The domain model stays infrastructure-independent.

The ORM model describes how PostgreSQL will store document lifecycle metadata.

## 2. Why PostgreSQL Is Needed

RAG is not only a model call.

It needs durable state for:

- document identity
- document version
- checksum
- ingestion status
- indexing status
- processing versions
- chunk metadata
- failure information
- timestamps

This durable state matters for:

- idempotent ingestion
- change detection
- retry after failure
- deletion
- reindexing
- vector index recovery
- citation provenance

Without PostgreSQL-owned metadata, the system would not know which documents were indexed, which version was indexed, or whether a document needs to be processed again.

## 3. Document Lifecycle Metadata

The RAG document table stores the existing domain lifecycle:

```text
RECEIVED
PROCESSING
INDEXED
FAILED
DELETED
```

The semantic source of truth remains:

```text
DocumentStatus
```

from:

```text
app/application/ai/rag/domain/document.py
```

The ORM model stores this status with values that map cleanly back to the domain enum.

## 4. Document Version and Checksum

A document can change over time.

Example:

```text
Employee Handbook
version 1
version 2
version 3
```

So the database model keeps:

```text
document_id
document_version
checksum
```

`document_id + document_version` identifies one logical document version.

`checksum` supports future idempotency and change detection.

Conceptually:

```text
same document
+ same checksum
+ same processing versions
= avoid duplicate processing
```

The repository logic for this is not implemented in `RAG-02`.

## 5. Processing and Index Metadata

The document model includes processing identity fields:

- `chunking_version`
- `embedding_provider`
- `embedding_model`
- `embedding_version`
- `index_version`

These fields answer a future reindexing question:

```text
Was this document indexed using the current processing configuration?
```

For example:

```text
document v3
chunking v1
embedding model A
index v1
```

is different from:

```text
document v3
chunking v2
embedding model B
index v2
```

These fields are nullable on the document record because a document may be `RECEIVED` before processing has started.

## 6. Why Store Chunks

RAG retrieval works from chunks, not usually from whole documents.

Conceptually:

```text
Document
      |
      v
Chunks
      |
      v
Embeddings
      |
      v
Qdrant
```

The chunk table stores:

- stable `chunk_id`
- logical document identity
- document version
- chunk index
- chunking version
- normalized chunk text
- processing/index versions
- optional provenance such as section and page number

## 7. Chunk Text Source-of-Truth Decision

`RAG-02` decides that PostgreSQL stores authoritative normalized chunk text.

This is important because Qdrant is a rebuildable vector index, not the source of truth.

If Qdrant is lost or needs to be rebuilt:

```text
Qdrant lost
    |
    v
read stored chunks from PostgreSQL
    |
    v
regenerate embeddings
    |
    v
rebuild Qdrant
```

This avoids depending on the original upload still being available.

PostgreSQL does not store original PDF or binary blobs in `RAG-02`.

It stores normalized chunk text only.

## 8. Chunk Text Safety

Chunk text is application data and may be sensitive.

Rules:

- do not log chunk text by default
- do not use chunk text as a metric label
- do not include chunk text in exception messages
- do not store raw provider responses in chunk rows

Operational details belong in structured logs and traces without leaking content.

## 9. PostgreSQL vs Qdrant

The ownership split is:

```text
PostgreSQL
=
authoritative document/chunk state
```

and:

```text
Qdrant
=
searchable vector index
```

PostgreSQL owns:

- document lifecycle
- document versions
- checksums
- chunk identity
- chunk text
- chunk provenance
- processing versions

Qdrant will eventually own:

- embedding vectors
- similarity-search payload
- retrieval-optimized index state

PostgreSQL does not store embedding vectors in this architecture.

## 10. Example

```text
Employee Handbook
document_id = employee-handbook
document_version = 3
status = INDEXED
checksum = sha256:abc

    |
    +--> chunk 0
    |    chunk_id = ...
    |    text = "Employees receive annual leave..."
    |    page_number = 4
    |
    +--> chunk 1
    |    chunk_id = ...
    |    text = "Carry-forward rules..."
    |    page_number = 5
    |
    +--> chunk 2
         chunk_id = ...
         text = "Approval workflow..."
         page_number = 6
```

Later, retrieval can return a chunk and the application can trace it back to:

```text
document_id
document_version
chunk_id
page_number
section
source
```

That supports citations and provenance.

## 11. Constraints and Indexes

The ORM metadata declares:

```text
document_id + document_version
```

as the logical document-version identity.

The chunk model declares:

```text
chunk_id
```

as a stable unique chunk identity.

It also declares:

```text
document_id + document_version + chunking_version + chunk_index
```

as a unique chunk-position identity for a specific chunking strategy.

Indexes are planned for common future operations:

- lookup by `document_id`
- lookup by `document_id + document_version`
- lookup by `checksum`
- lookup by `status`
- load chunks for a document/version

RAG-03 will create the actual Alembic migration.

## 12. What RAG-02 Does Not Implement

RAG-02 does not add:

- Alembic migration
- document repository
- document upload
- PDF extraction
- chunking algorithm
- embedding calls
- Qdrant adapter
- vector search
- retriever
- RAG API

It only adds the ORM metadata and documentation needed for the migration and repository tasks that follow.
