# RAG-01 and RAG-02 — Implementation Learning Guide

## Purpose

This document explains the implementation changes and reasoning behind:

- **RAG-01 — RAG Settings Skeleton**
- **RAG-01A — retrieval score semantics correction**
- **RAG-02 — Document and Chunk Persistence Metadata Models**

It is intended as a future learning reference for understanding how the RAG platform is being built step by step.

> **Accuracy note:** RAG-01 is documented from the concrete settings code shared during development. The final RAG-02 Codex completion report/diff was not present in the conversation used to create this guide, so RAG-02 is documented from the agreed implementation contract and architecture. Exact ORM class names, columns, indexes, and constraints should be synchronized with the final repository implementation if they differ.

---

# 1. Where These Tasks Fit

RAG is not one API call. It is a pipeline:

```text
Document
   ↓
Load / Extract
   ↓
Normalize
   ↓
Chunk
   ↓
Embed
   ↓
Vector Store
   ↓
Retrieve
   ↓
Build Context
   ↓
LLM Generation
   ↓
Answer + Citations
```

The project is building this incrementally:

```text
RAG-00
Architecture + Domain Contracts
        ↓
RAG-01
Configuration Foundation
        ↓
RAG-02
Persistence Metadata Models
        ↓
RAG-03
Database Migration
        ↓
RAG-04
Repository
        ↓
Later ingestion / embeddings / Qdrant / retrieval
```

RAG-00 answered:

> What concepts and boundaries should exist?

RAG-01 answers:

> How should future RAG components be configured?

RAG-02 answers:

> What document/chunk state must be persisted so indexing can be reliable and rebuildable?

---

# Part I — RAG-01: RAG Settings Skeleton

# 2. What RAG-01 Added

The implementation introduced configuration concepts equivalent to:

```python
class EmbeddingProvider(str, Enum):
    OPENAI = "openai"

class VectorStoreProvider(str, Enum):
    QDRANT = "qdrant"

class EmbeddingSettings(BaseModel):
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI
    model: str = "text-embedding-3-small"
    batch_size: int = 64
    timeout_seconds: int = 30

class VectorStoreSettings(BaseModel):
    provider: VectorStoreProvider = VectorStoreProvider.QDRANT
    url: str = "http://qdrant:6333"
    collection: str = "documents"
    timeout_seconds: int = 10

class RAGSettings(BaseModel):
    enabled: bool = False
    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_top_k: int = 5
    minimum_score: float = 0.3
    max_document_bytes: int = 5 * 1024 * 1024
    max_chunks_per_document: int = 1000
    prompt_version: str = "v1"
    index_version: str = "v1"
    embedding: EmbeddingSettings
    vector_store: VectorStoreSettings
```

The important change is not the specific defaults. It is that RAG now has a **central, typed, validated configuration contract**.

---

# 3. Why RAG Needs Central Configuration

A RAG pipeline needs operational decisions such as:

```text
How large should chunks be?
How much should chunks overlap?
How many chunks should retrieval return?
Which embedding model should be used?
How many texts should be embedded in one batch?
Which vector database should be used?
Where is the vector store running?
How large can an uploaded document be?
Which prompt/index version is active?
```

Without a settings model, future code could contain duplicated magic values:

```python
chunk_size = 800
top_k = 5
timeout = 30
```

in several services.

That leads to:

```text
duplication
inconsistent behavior
harder testing
harder tuning
environment-specific hacks
```

RAG-01 creates:

```text
RAGSettings
   ├── chunking policy
   ├── retrieval policy
   ├── ingestion limits
   ├── embedding settings
   ├── vector-store settings
   └── version identifiers
```

Future components consume these settings instead of defining their own constants.

---

# 4. `EmbeddingProvider`

```python
class EmbeddingProvider(str, Enum):
    OPENAI = "openai"
```

This identifies which provider will generate embeddings.

Future dependency flow:

```text
DocumentChunk
      ↓
EmbeddingPort
      ↓
Configured Embedding Provider
      ↓
Embedding Vector
```

Why an enum?

```text
typed values
invalid strings rejected
clear extension point
better configuration discoverability
```

It also prevents provider-specific strings from being scattered through the codebase.

---

# 5. What Is an Embedding?

An embedding converts text into a numerical vector.

Example:

```text
"annual leave policy"
        ↓
Embedding Model
        ↓
[0.12, -0.48, 0.73, 0.19, ...]
```

RAG uses embeddings twice:

## During ingestion

```text
DocumentChunk
      ↓
Embedding
      ↓
Stored Vector
```

## During query

```text
Question
      ↓
Embedding
      ↓
Query Vector
```

The vector store compares the question vector with stored chunk vectors to find semantically related content.

---

# 6. `EmbeddingSettings`

Fields:

```text
provider
model
batch_size
timeout_seconds
```

## `provider`

Selects the future adapter that will satisfy `EmbeddingPort`.

Correct architecture:

```text
RAG application
      ↓
EmbeddingPort
      ↓
OpenAIEmbeddingAdapter
```

Not:

```text
RAGQueryUseCase
      ↓
OpenAI SDK directly
```

## `model`

Default:

```text
text-embedding-3-small
```

Why configure it?

The embedding model affects:

```text
semantic representation
vector dimensions
retrieval quality
index compatibility
cost/performance
```

Changing the embedding model later can require re-indexing because previously stored vectors should not automatically be assumed compatible with vectors generated by a different model.

## `batch_size`

Default:

```text
64
```

If a document produces 1,000 chunks, a naive implementation could make 1,000 individual embedding calls.

Batching allows:

```text
Chunks 1-64   → embedding request
Chunks 65-128 → embedding request
...
```

This supports:

```text
better throughput
fewer network calls
provider efficiency
bounded resource usage
```

RAG-01 only defines the policy. Actual batching belongs to later embedding tasks.

## `timeout_seconds`

Default:

```text
30
```

Embedding is an infrastructure call and needs a bounded execution time.

Important:

```text
embedding timeout
!=
LLM generation timeout
!=
vector search timeout
```

Separate settings allow each operation to have its own reliability policy.

---

# 7. Embedding Validation

The implementation validates concepts such as:

```text
model must not be blank
batch_size > 0
timeout_seconds > 0
```

This follows a useful backend principle:

> Invalid configuration should fail early.

Better:

```text
application settings load
      ↓
invalid batch_size detected immediately
```

than:

```text
application starts
      ↓
hours later ingestion runs
      ↓
embedding fails because batch_size = 0
```

---

# 8. `VectorStoreProvider`

```python
class VectorStoreProvider(str, Enum):
    QDRANT = "qdrant"
```

This identifies the planned first vector-store technology.

Architecture:

```text
VectorStorePort
      ↓
QdrantVectorStore
      ↓
Qdrant
```

Important distinction:

```text
VectorStoreProvider = configuration choice
VectorStorePort     = application interface
QdrantVectorStore   = future adapter
Qdrant              = infrastructure product
```

---

# 9. What Qdrant Means

Qdrant is the planned vector database for the first RAG implementation.

Its future job is to store/search vector representations of document chunks.

Example:

```text
Document chunk:
"Employees receive 20 annual leave days."
        ↓
Embedding
        ↓
[0.12, -0.48, 0.73, ...]
        ↓
Qdrant
```

Query:

```text
"How much vacation time do employees get?"
        ↓
Question Embedding
        ↓
Qdrant similarity search
        ↓
Relevant leave-policy chunk
```

The application should still depend on:

```text
VectorStorePort
```

rather than directly on Qdrant SDK objects.

---

# 10. `VectorStoreSettings`

Fields:

```text
provider
url
collection
timeout_seconds
```

## `url`

Default:

```text
http://qdrant:6333
```

This is where the future Qdrant adapter will connect.

Important:

```text
configured URL
!=
active Qdrant connection
```

RAG-01 only defines configuration.

## `collection`

Default:

```text
documents
```

Conceptually, a vector collection will contain entries such as:

```text
documents
├── vector A
│   ├── document_id
│   ├── chunk_id
│   ├── provenance
│   └── retrieval metadata
├── vector B
└── vector C
```

The exact payload schema belongs to later Qdrant work.

## `timeout_seconds`

Default:

```text
10
```

Future vector operations include:

```text
upsert
search
delete
health
```

They also require bounded execution time.

---

# 11. `RAGSettings.enabled`

```python
enabled: bool = False
```

RAG is disabled by default.

Why?

Because configuration exists before the runtime subsystem is complete.

Expected idea:

```text
Application starts
      ↓
RAGSettings loads
      ↓
enabled = False
```

This should not automatically create:

```text
Qdrant client
RAG routes
embedding wiring
retrieval
```

The setting creates a safe future feature-activation boundary.

---

# 12. `chunk_size`

Default:

```text
800
```

A large document should not usually be retrieved as one enormous block.

Instead:

```text
Large Document
      ↓
TextChunker
      ├── Chunk 0
      ├── Chunk 1
      ├── Chunk 2
      └── ...
```

`chunk_size` controls the target/maximum size according to the future chunking algorithm.

Important:

RAG-01 does not yet establish whether `800` means:

```text
characters
tokens
another unit
```

That belongs to the actual chunker task.

---

# 13. `chunk_overlap`

Default:

```text
120
```

Overlap preserves context around chunk boundaries.

Without overlap:

```text
Chunk 1 [----------------X]
Chunk 2                  [Y----------------]
```

A useful sentence or paragraph can be split.

With overlap:

```text
Chunk 1 [----------------------]
                   [======]
Chunk 2            [======----------------------]
```

Validation:

```text
chunk_overlap >= 0
chunk_overlap < chunk_size
```

---

# 14. `retrieval_top_k`

Default:

```text
5
```

It controls how many candidate chunks retrieval considers/returns.

```text
Question
   ↓
Vector Search
   ├── Result 1
   ├── Result 2
   ├── Result 3
   ├── Result 4
   └── Result 5
```

Too many results can cause:

```text
more irrelevant context
larger prompts
higher latency
higher cost
more noise
```

Too few can miss useful evidence.

The final value should later be tuned using RAG evaluation rather than intuition alone.

---

# 15. `minimum_score` and the RAG-01A Correction

The original validator assumed:

```python
0 <= minimum_score <= 1
```

That accidentally created the contract:

```text
all retrieval scores are normalized to 0..1
```

But the architecture had not yet defined:

```text
distance metric
similarity metric
Qdrant score semantics
normalization strategy
higher-vs-lower interpretation
```

Therefore the validation was too specific.

The corrected concept is:

```text
minimum_score
=
finite configured retrieval threshold
```

while:

```text
score interpretation
=
future Retriever / VectorStore policy
```

This is an important architecture lesson:

> Do not validate more narrowly than the domain contract actually guarantees.

Finite numeric values can be accepted without forcing an artificial `0..1` contract.

Special values such as:

```python
float("nan")
float("inf")
float("-inf")
```

should still be rejected because they are not useful operational thresholds.

---

# 16. `max_document_bytes`

Default:

```python
5 * 1024 * 1024
```

approximately 5 MiB.

This protects future ingestion from uncontrolled input size.

```text
Document upload
   ├── within limit → process
   └── too large    → reject
```

Large inputs can increase:

```text
memory use
extraction time
chunk count
embedding calls
vector writes
latency
```

---

# 17. `max_chunks_per_document`

Default:

```text
1000
```

Byte-size limits alone do not bound every kind of processing explosion.

A pathological document/chunking combination could produce too many chunks.

This setting bounds downstream work:

```text
document
   ↓
chunker
   ↓
maximum allowed chunk count
```

It protects:

```text
embedding capacity
memory
Qdrant writes
processing time
future queue capacity
```

---

# 18. `prompt_version`

Default:

```text
v1
```

A RAG prompt can evolve.

Example:

```text
v1:
Answer using retrieved context.
```

Later:

```text
v2:
Use retrieved evidence only.
Return structured citations.
Use stricter no-context behavior.
```

Versioning helps:

```text
debugging
evaluation
reproducibility
cache identity
regression analysis
```

---

# 19. `index_version`

Default:

```text
v1
```

RAG retrieval state is derived:

```text
Document
   ↓
Chunks
   ↓
Embeddings
   ↓
Vector Index
```

The index may depend on:

```text
chunking behavior
embedding model
vector dimensions
payload schema
indexing rules
```

If those change significantly, an index version helps identify whether a rebuild/migration is needed.

---

# 20. What RAG-01 Did Not Implement

RAG-01 intentionally did not add runtime RAG behavior:

```text
Qdrant SDK/client
document ingestion
document loaders
chunking implementation
embedding execution
embedding batching
VectorStore adapter
Retriever
RAGPromptBuilder
RAGQueryUseCase
RAG APIs
```

RAG-01 added **policy/configuration**, not execution.

---

# 21. RAG-01 Future Consumer Map

| Setting | Future Consumer | Purpose |
|---|---|---|
| `enabled` | composition/startup | feature activation |
| `chunk_size` | `TextChunker` | chunk size policy |
| `chunk_overlap` | `TextChunker` | preserve boundary context |
| `retrieval_top_k` | `Retriever` | retrieval breadth |
| `minimum_score` | retrieval policy | relevance threshold |
| `max_document_bytes` | ingestion validation | input limit |
| `max_chunks_per_document` | ingestion/chunking | work limit |
| `prompt_version` | `RAGPromptBuilder`/cache/eval | prompt identity |
| `index_version` | index lifecycle | derived-index identity |
| embedding provider/model | embedding adapter | vector generation |
| embedding batch size | ingestion | throughput |
| embedding timeout | embedding reliability | bounded calls |
| vector-store provider | DI/composition | adapter selection |
| vector-store URL | Qdrant adapter | endpoint |
| vector-store collection | Qdrant adapter | index/collection |
| vector-store timeout | vector adapter | bounded calls |

---

# Part II — RAG-02: Document and Chunk Persistence Metadata Models

# 22. What Problem RAG-02 Solves

RAG-00 created domain concepts:

```text
Document
DocumentChunk
```

But the platform also needs durable answers to:

```text
Which documents exist?
Which version was processed?
Did indexing succeed?
What checksum was used?
Which chunks belong to which document?
What processing configuration produced them?
Can the vector index be rebuilt if Qdrant is lost?
```

RAG-02 introduces the persistence representation needed to support those questions.

Conceptual architecture:

```text
Domain Model
      ↓
Document / DocumentChunk

Persistence Model
      ↓
SQLAlchemy document/chunk models

Database
      ↓
PostgreSQL
```

---

# 23. Domain Model vs Persistence Model

## Domain model

Represents application meaning.

Example:

```text
Document
```

It should not know about:

```text
SQLAlchemy
table names
foreign keys
database sessions
database indexes
```

## Persistence model

Represents storage details.

It may contain:

```text
SQLAlchemy columns
ForeignKey
Index
UniqueConstraint
relationship()
```

Correct dependency idea:

```text
Domain Document
      ↓
Repository mapping
      ↓
SQLAlchemy persistence model
      ↓
PostgreSQL
```

Why?

Because:

```text
application concept
!=
database implementation
```

This keeps the domain testable and infrastructure-independent.

---

# 24. Why PostgreSQL Is Needed When We Also Plan Qdrant

PostgreSQL and Qdrant have different responsibilities.

## PostgreSQL

Future authoritative state:

```text
document identity
document version
checksum
status
processing versions
chunk identity
chunk provenance
authoritative chunk text, if finalized
timestamps
safe failure metadata
```

## Qdrant

Future semantic retrieval index:

```text
vectors
retrieval payload
similarity-search representation
```

Mental model:

```text
PostgreSQL
=
What knowledge exists and what state is it in?

Qdrant
=
Which indexed chunks are semantically closest to this question?
```

---

# 25. Why Qdrant Should Be Rebuildable

Bad architecture:

```text
Qdrant lost
   ↓
knowledge permanently lost
```

Better:

```text
Qdrant lost
   ↓
read authoritative document/chunk state
   ↓
generate embeddings again
   ↓
rebuild Qdrant index
```

Therefore:

```text
Qdrant = derived searchable index
```

not:

```text
Qdrant = only source of truth
```

This is one of the central reasons RAG-02 exists.

---

# 26. Expected Document Persistence Metadata

The RAG-02 contract calls for concepts such as:

```text
document_id
title
source
content_type
document_version
checksum
status
processing/index metadata
timestamps
safe failure information
```

Each has a lifecycle purpose.

---

# 27. `document_id`

Stable logical identity.

Example:

```text
employee-handbook
```

The document can evolve:

```text
employee-handbook v1
employee-handbook v2
employee-handbook v3
```

while retaining one logical identity.

Useful for:

```text
updates
reindexing
deletion
citations
API operations
```

A DB internal primary key may still exist, but it is not necessarily the same as the domain-facing document ID.

---

# 28. `title`

Example:

```text
Employee Handbook
```

Useful for:

```text
display
citations
administration
document listing
```

A title is descriptive metadata, not stable identity.

---

# 29. `source`

Represents the generic origin of the document.

Possible concepts:

```text
uploaded file
URI
internal source identifier
```

RAG-02 should remain generic and avoid OdinSync-specific source fields.

---

# 30. `content_type`

Examples:

```text
text/plain
text/markdown
application/pdf
```

Why persist it?

Future reprocessing may need to know how the content was extracted.

RAG-02 stores metadata; it does not parse the document yet.

---

# 31. `document_version`

Imagine:

```text
Handbook v1:
15 leave days

Handbook v2:
20 leave days
```

Without version awareness, it becomes hard to answer:

```text
Which document version produced these chunks?
Which vectors are current?
Which version should a citation refer to?
Does this document need reindexing?
```

Document version is therefore part of reliable retrieval provenance.

---

# 32. `checksum`

A checksum is a content fingerprint.

```text
normalized content
      ↓
hash
      ↓
ABC123...
```

Later ingestion can compare:

```text
stored checksum
vs
new checksum
```

This supports change detection and idempotency.

---

# 33. Idempotency

In this context:

```text
same logical document
+
same content/checksum
+
same processing configuration
=
avoid duplicate logical processing/indexing
```

RAG-02 does not perform that workflow yet.

It stores the metadata future use cases need to make the decision.

---

# 34. `status`

Document ingestion is multi-stage:

```text
RECEIVED
   ↓
PROCESSING
   ├──→ INDEXED
   └──→ FAILED
```

Later:

```text
INDEXED
   ├──→ PROCESSING  # reindex
   └──→ DELETED
```

Why persist it?

Because:

```text
document exists
```

does not mean:

```text
document is searchable
```

The status tells the application whether the knowledge is ready.

---

# 35. Processing Version Metadata

The model needs enough information to answer:

> Was this document indexed with the current RAG processing configuration?

Useful concepts may include:

```text
chunking_version
embedding_provider
embedding_model
embedding_version
index_version
```

Example:

```text
Document v3
chunking v1
embedding model A
index v1
```

is not equivalent to:

```text
Document v3
chunking v2
embedding model B
index v2
```

even if the original document text did not change.

---

# 36. Why Reindexing Can Be Required Without a Document Change

Suppose:

```text
document checksum unchanged
```

but:

```text
embedding model changed
```

Then:

```text
old vectors
!=
new desired vector representation
```

The system may need:

```text
same document
   ↓
new embeddings
   ↓
new index
```

The same is true if the chunking algorithm changes.

That is why processing versions are persisted separately from source-document version.

---

# 37. Failure Metadata

A future ingestion can fail during:

```text
extraction
normalization
chunking
embedding
vector upsert
```

Persistence may keep a bounded safe value such as:

```text
failure_reason
```

Useful for answering:

```text
Why is this document FAILED?
```

But do not persist:

```text
full stack trace
API keys
raw provider responses
sensitive document text in error messages
```

Detailed diagnostics belong in logs and traces.

---

# 38. Timestamps

Likely lifecycle concepts include:

```text
created_at
updated_at
```

Potentially later:

```text
indexed_at
deleted_at
```

They help:

```text
operations
debugging
cleanup
lifecycle visibility
```

Only timestamps with a clear lifecycle purpose should be introduced.

---

# 39. Chunk Persistence

One document produces multiple chunks.

```text
Document
   │
   ├── Chunk 0
   ├── Chunk 1
   ├── Chunk 2
   └── ...
```

Persisted chunk metadata supports:

```text
rebuilds
citations
provenance
deletion
reindexing
debugging
```

---

# 40. Expected Chunk Fields

Architecture-defined concepts include:

```text
chunk_id
document_id
document_version
chunk_index
chunking_version
section
page_number
normalized chunk text, if finalized
```

---

# 41. `chunk_id`

Stable chunk identity.

A future deterministic identity can conceptually derive from:

```text
document_id
+
document_version
+
chunking_version
+
chunk_index
+
normalized chunk content
```

Benefits:

```text
idempotency
deduplication
reproducibility
reindexing
provenance
```

The final hashing implementation belongs to the chunking task.

---

# 42. `document_id` and `document_version` on Chunks

A chunk must be traceable to:

```text
which document?
which version?
```

Example:

```text
Employee Handbook v3
      ↓
Chunk 17
```

This supports correct citations and avoids mixing chunks from different versions.

---

# 43. `chunk_index`

Example:

```text
0, 1, 2, 3...
```

Preserves ordering.

Useful for:

```text
neighboring chunk retrieval
document reconstruction
debugging
deterministic identity
```

---

# 44. `chunking_version`

Chunking strategy can evolve.

Example:

```text
v1 = fixed-size
v2 = paragraph-aware
```

The same document can produce a different set of chunks under each strategy.

So the chunk needs to preserve which processing behavior created it.

---

# 45. `section` and `page_number`

These are provenance fields.

Example:

```text
title:
Employee Handbook

section:
Leave Policy

page:
37
```

They make future citations meaningful:

```text
Employee Handbook — Leave Policy — page 37
```

---

# 46. Should PostgreSQL Store Chunk Text?

The architecture should explicitly decide this.

A robust model can use:

```text
PostgreSQL
   ├── authoritative normalized chunk text
   ├── chunk identity
   ├── provenance
   └── lifecycle metadata

Qdrant
   ├── vectors
   └── retrieval payload/reference
```

Why?

If Qdrant disappears:

```text
PostgreSQL chunk text
      ↓
EmbeddingPort
      ↓
regenerate vectors
      ↓
rebuild Qdrant
```

This gives the system a recovery path without treating the vector DB as the only knowledge store.

---

# 47. Why Not Store Vectors in PostgreSQL Too?

The chosen architecture uses Qdrant for vectors.

Therefore avoid accidentally creating two vector stores:

```text
PostgreSQL vectors
+
Qdrant vectors
```

unless a later ADR intentionally changes that choice.

Current conceptual ownership:

```text
PostgreSQL → authoritative document/chunk state
Qdrant     → vector search/index
```

---

# 48. Database Relationships

Conceptually:

```text
Document Version
      1
      │
      │
      *
      ↓
Document Chunks
```

Foreign-key/relationship design helps prevent:

```text
orphan chunks
ambiguous ownership
chunks linked to nonexistent documents
```

RAG-02 defines the ORM/persistence shape.

RAG-03 creates the actual migration/tables.

---

# 49. Uniqueness

Potential logical uniqueness includes:

```text
document_id + document_version
```

for document versions.

Chunks can use:

```text
stable chunk_id
```

and/or an appropriate compound uniqueness constraint based on document/version/chunk position/chunking version.

Why important?

Repeated ingestion should not silently create duplicate logical state.

The exact final constraint should match the actual repository implementation.

---

# 50. Database Index Planning

Likely access patterns include:

```text
find by document_id
find document version
find by checksum
find by status
load chunks for document/version
```

Useful DB indexes should map to these real operations.

The goal is not to index every field.

---

# 51. Why RAG-02 Does Not Include the Alembic Migration

Separation:

```text
RAG-02
defines persistence shape

RAG-03
creates physical database migration
```

This makes the schema easier to review before changing the database.

---

# 52. Why RAG-02 Does Not Include the Repository

Likewise:

```text
ORM model
!=
repository behavior
```

RAG-04 will later implement operations such as:

```text
create
get
find by checksum
update status
save chunks
delete
```

RAG-02 establishes what those operations will persist.

---

# 53. How RAG-01 and RAG-02 Work Together

This is the most important connection.

RAG-01 provides:

```text
processing policy
```

RAG-02 provides:

```text
processing state
```

Example:

```text
RAG-01:
chunk_size = 800
embedding model = X
index_version = v1
```

After processing, RAG-02 persistence can record conceptually:

```text
Document A

document_version = 3
chunking_version = v1
embedding_model = X
index_version = v1
status = INDEXED
```

Later configuration becomes:

```text
embedding_model = Y
```

Now the application can compare:

```text
desired processing configuration
vs
persisted processing metadata
```

and determine:

```text
Document A needs reindexing
```

This is one of the main reasons both tasks exist.

---

# 54. Complete Example: Employee Handbook

## RAG-01 policy

```text
chunk_size = 800
chunk_overlap = 120
retrieval_top_k = 5
embedding_model = text-embedding-3-small
index_version = v1
```

## RAG-02 document state

```text
document_id = employee-handbook
document_version = 3
checksum = ABC123
status = RECEIVED
```

Processing starts:

```text
status = PROCESSING
```

Future chunker creates:

```text
Chunk 0
Chunk 1
...
Chunk 17
```

Chunk 17:

```text
document_id = employee-handbook
document_version = 3
chunk_index = 17
chunking_version = v1
page_number = 37

text =
"Employees receive 20 annual leave days..."
```

Later embedding task:

```text
Chunk 17
   ↓
EmbeddingPort
   ↓
Vector
```

Later Qdrant task:

```text
Vector + retrieval metadata
   ↓
Qdrant
```

When indexing succeeds:

```text
status = INDEXED
```

Now the system knows this document is ready for retrieval.

---

# 55. Future Query Using This Foundation

User asks:

```text
How much annual leave do employees receive?
```

Future flow:

```text
Question
   ↓
EmbeddingPort
   ↓
Query Vector
   ↓
Qdrant
   ↓
Chunk 17
   ↓
RetrievedChunk
```

Provenance:

```text
document = Employee Handbook
page = 37
```

Then:

```text
Question + Chunk 17
   ↓
RAGPromptBuilder
   ↓
AIInferencePort
   ↓
InferenceRouter
   ├── Ollama
   └── OpenAI
   ↓
Answer
```

Final future response:

```text
Employees receive 20 annual leave days.

Source:
Employee Handbook, page 37
```

That is how the early RAG-01/RAG-02 work eventually contributes to a user-visible AI feature.

---

# 56. Why These Tasks Feel Like "No RAG Yet"

After RAG-01 and RAG-02 you still cannot upload a PDF and ask questions.

That is expected.

They are foundational tasks:

```text
RAG-00 → architecture
RAG-01 → configuration
RAG-02 → persistence representation
RAG-03 → physical DB schema
RAG-04 → persistence operations
later  → ingestion, embedding, retrieval, generation
```

This is the same discipline used in a well-structured backend:

```text
domain
→ config
→ persistence model
→ migration
→ repository
→ use case
→ API
```

---

# 57. Key Engineering Lessons

## 1. Configuration is policy

`RAGSettings` says how future components should behave.

It does not execute the behavior.

## 2. Domain is not database

`Document` describes application meaning.

SQLAlchemy models describe storage.

## 3. Qdrant is an index

Qdrant should support semantic retrieval, not become the only source of knowledge truth.

## 4. Derived data must be reproducible

Chunks, embeddings, and vector indexes are generated artifacts.

Version/checksum metadata helps determine whether they are stale.

## 5. Fail early on known invalid config

Reject:

```text
blank model
batch size <= 0
timeout <= 0
overlap >= chunk size
```

at configuration time.

## 6. Do not invent invariants prematurely

The original `minimum_score 0..1` rule was too specific before score semantics were defined.

## 7. Keep infrastructure behind ports

Future application logic should use:

```text
EmbeddingPort
VectorStorePort
DocumentRepositoryPort
```

rather than directly importing provider/database SDK behavior into use cases.

---

# 58. PostgreSQL vs Qdrant vs Redis

A useful mental shortcut:

```text
PostgreSQL
=
What knowledge exists?
What version is it?
What state is it in?
What authoritative chunks/provenance do I own?

Qdrant
=
Which indexed chunks are semantically closest
to the current question?

Redis
=
Do I have temporary/cached state
that can avoid repeated work?
```

Simplified:

```text
PostgreSQL → authoritative state
Qdrant     → semantic retrieval
Redis      → cache
```

---

# 59. What Comes Next

After RAG-02:

```text
RAG-03
Alembic migration

RAG-04
Document repository

RAG-05
Ingestion API contract

RAG-06
Document loader / extraction

RAG-07
Normalization + chunking

RAG-08
EmbeddingPort revision

RAG-09
Embedding adapter wiring

RAG-10
VectorStorePort finalization

RAG-11
Qdrant adapter

RAG-12
IndexDocumentUseCase

RAG-13
Ingestion lifecycle

RAG-14
Retriever

RAG-15
Dense retrieval baseline

RAG-16
RAGPromptBuilder

RAG-17
RAGQueryUseCase

RAG-18
Citation API contract

RAG-19
RAG response validation
```

Later tasks add:

```text
security
observability
evaluation
caching
recovery
embedding migrations
performance/capacity
```

---

# 60. Final Mental Model

RAG-01 and RAG-02 are not the retrieval engine themselves.

They establish:

```text
RAG-01
CONFIGURATION / POLICY

RAG-02
PERSISTENCE / STATE
```

Later tasks add:

```text
EXECUTION
```

The full progression is:

```text
Architecture
      ↓
Configuration
      ↓
Persistent State
      ↓
Ingestion
      ↓
Chunking
      ↓
Embeddings
      ↓
Vector Index
      ↓
Retrieval
      ↓
Prompt Construction
      ↓
LLM Generation
      ↓
Grounded Answer + Citations
```

The core learning point is:

> A production-oriented RAG system is not just `Embedding + Qdrant + LLM`. It also needs configuration, document lifecycle state, versioning, provenance, idempotency, recovery, validation, and clean infrastructure boundaries.

That is why RAG-01 and RAG-02 are important even though they do not yet produce a visible RAG answer.
