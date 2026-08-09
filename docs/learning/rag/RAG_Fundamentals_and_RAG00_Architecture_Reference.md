# RAG Fundamentals and RAG-00 Architecture Reference

## Purpose

This document explains Retrieval-Augmented Generation (RAG) from first principles and connects the concept directly to the `ai-engineer-foundation` architecture established in **RAG-00 — Architecture ADR and Domain Contracts**.

It is intended as a long-term reference for:

- understanding what RAG is;
- understanding why RAG is useful;
- understanding the difference between ingestion and query workflows;
- understanding embeddings and vector databases;
- understanding how RAG reuses the existing AI generation platform;
- understanding the domain models and ports introduced in RAG-00;
- understanding how the generic RAG platform can later support features such as document chat, knowledge assistants, support assistants, and eventually OdinSync integration.

---

# 1. The Problem RAG Solves

A Large Language Model (LLM) such as an Ollama-hosted model or OpenAI model can answer using:

1. knowledge learned during training;
2. information included directly in the prompt.

Suppose a user asks:

> What is the annual leave policy in my company's employee handbook?

The model does not automatically know the contents of a private employee handbook.

If the model answers anyway, it may produce a generic answer based on its training data rather than the company's real policy.

That creates a reliability problem.

The basic non-RAG flow looks like:

```text
User Question
     |
     v
FastAPI
     |
     v
Guardrails
     |
     v
AIInferencePort
     |
     v
InferenceRouter
     |
  +--+--+
  |     |
Ollama OpenAI
     |
     v
Answer
```

This works well for general generation tasks such as summarization, but it is not enough when the answer must come from a private or application-specific knowledge source.

---

# 2. Why Not Send the Entire Document to the LLM?

One possible solution is to place the entire document inside the prompt.

For example:

```text
Here is my entire employee handbook:

<200 pages of text>

Question:
How many annual leave days do employees receive?
```

This is inefficient because it can cause:

- very large prompts;
- higher token usage;
- higher cost;
- higher latency;
- context-window limits;
- too much irrelevant information;
- harder reasoning for the model.

Usually only a small part of the document is needed.

For example, if the answer is on page 37, the system should ideally retrieve only the relevant section instead of sending all 200 pages.

This is the core problem RAG solves.

---

# 3. What RAG Means

**RAG = Retrieval-Augmented Generation**

It combines two capabilities:

```text
Retrieval
+
Generation
```

## Retrieval

Find the pieces of external knowledge that are most relevant to the user's question.

## Augmented Generation

Provide those retrieved pieces to the LLM as context and ask the model to generate an answer using that evidence.

Without RAG:

```text
Question
   |
   v
LLM
   |
   v
Answer
```

With RAG:

```text
Question
   |
   v
Search Knowledge Base
   |
   v
Find Relevant Information
   |
   v
Build Context
   |
   v
LLM
   |
   v
Answer
```

---

# 4. Simple RAG Example

Assume the knowledge base contains:

```text
Employee Handbook

Pages 1-20  : Company information
Pages 21-35 : Working hours
Pages 36-40 : Leave policy
Pages 41-55 : Travel policy
Pages 56-70 : Medical benefits
```

A user asks:

> How many annual leave days do employees get?

RAG performs retrieval first.

```text
Question
"How many annual leave days do employees get?"
                  |
                  v
              Retrieval
                  |
                  v
Relevant chunks:

Chunk 48:
"Employees are entitled to 20 days
of annual leave each calendar year."

Chunk 49:
"Unused annual leave may..."
                  |
                  v
             Build Prompt
                  |
                  v
LLM receives:

Question:
How many annual leave days do employees get?

Context:
Employees are entitled to 20 days
of annual leave each calendar year.

Instruction:
Answer using only the supplied context.
                  |
                  v
Answer:
"Employees receive 20 days of annual leave."
```

The API can also return provenance:

```json
{
  "answer": "Employees receive 20 days of annual leave.",
  "citations": [
    {
      "title": "Employee Handbook",
      "page_number": 37
    }
  ]
}
```

The answer is therefore based on retrieved evidence rather than unrestricted model memory.

---

# 5. Embeddings

To perform semantic retrieval, text is converted into a numerical vector called an **embedding**.

Example:

```text
"annual leave policy"
        |
        v
Embedding Model
        |
        v
[0.12, -0.48, 0.73, 0.19, ...]
```

Another phrase:

```text
"employee vacation allowance"
        |
        v
Embedding Model
        |
        v
[0.14, -0.45, 0.70, 0.22, ...]
```

The two vectors should be relatively close because the phrases have similar semantic meaning.

Conceptually:

```text
annual leave
     ●
    /
   /
  ● vacation allowance


                       ● laptop return policy
```

This is useful because a user may use different words from the source document.

Example:

```text
User:
"How much vacation time do I get?"

Document:
"Employees receive 20 annual leave days."
```

A purely keyword-based search may not always understand that:

```text
vacation
≈
annual leave
```

Embeddings help represent semantic similarity.

---

# 6. Vector Database

A vector database stores embeddings and supports similarity search.

Conceptually:

```text
Chunk 1
text:
"Employees receive 20 annual leave days."

vector:
[0.12, -0.48, 0.73, ...]


Chunk 2
text:
"Employees must return company laptops."

vector:
[-0.42, 0.11, 0.19, ...]


Chunk 3
text:
"Medical insurance covers..."

vector:
[...]
```

When the user asks:

```text
How much vacation do employees get?
```

the question is also embedded:

```text
Question
   |
Embedding Model
   |
   v
[0.13, -0.46, 0.72, ...]
```

The vector database searches for the nearest stored vectors.

It may return:

```text
1. Annual leave chunk       score 0.91
2. Leave carry-forward      score 0.84
3. Leave approval policy    score 0.78
```

Those retrieved chunks become the evidence supplied to the LLM.

The planned generic architecture uses a provider-independent `VectorStorePort`, with a future adapter such as Qdrant.

---

# 7. RAG Has Two Separate Workflows

This is one of the most important concepts in RAG.

RAG is not one single request flow.

There are two main workflows:

1. ingestion/indexing;
2. querying/retrieval/generation.

---

# 8. Workflow A — Document Ingestion

The ingestion workflow prepares the knowledge base.

```text
Document
   |
   v
Load / Extract Text
   |
   v
Normalize
   |
   v
Split into Chunks
   |
   v
Generate Embeddings
   |
   v
Store Embeddings + Metadata
   |
   v
Knowledge Base Ready
```

Example:

```text
Employee Handbook.pdf
        |
        v
PDF Loader
        |
        v
Extracted Text
        |
        v
Text Normalizer
        |
        v
Text Chunker
        |
        v
DocumentChunk[]
        |
        v
EmbeddingPort
        |
        v
EmbeddedChunk[]
        |
        v
VectorStorePort
        |
        v
Vector Database
```

This normally happens when documents are added, updated, or re-indexed.

It does not need to run every time a user asks a question.

---

# 9. Workflow B — RAG Query

The query workflow runs when a user asks a question.

```text
User Question
    |
    v
Create Query Embedding
    |
    v
Vector Search
    |
    v
Retrieve Relevant Chunks
    |
    v
Build RAG Prompt
    |
    v
Existing AIInferencePort
    |
    v
InferenceRouter
    |
  +--+--+
  |     |
Ollama OpenAI
    |
    v
Generated Answer
    |
    v
Validation + Citations
    |
    v
RAGResult
```

The key distinction is:

```text
Ingestion prepares knowledge.

Query consumes knowledge.
```

---

# 10. How RAG Reuses the Existing AI Platform

The current project already has major AI backend infrastructure:

```text
AIInferencePort
InferenceRouter
ModelRegistry
OllamaAdapter
OpenAIAdapter
timeouts
retries
provider fallback
circuit breakers
Redis cache
guardrails
response pipelines
exception handling
structured logging
Prometheus metrics
OpenTelemetry tracing
```

RAG should not duplicate this infrastructure.

The future RAG generation path should be:

```text
RAGQueryUseCase
      |
      v
Retriever
      |
      v
RAGPromptBuilder
      |
      v
AIInferencePort
      |
      v
InferenceRouter
      |
      v
ModelRegistry
      |
   +--+--+
   |     |
Ollama OpenAI
      |
      v
Generated Answer
```

Therefore, RAG should **not** create:

```text
RAGOpenAIAdapter
RAGOllamaAdapter
RAGInferenceRouter
RAGModelRegistry
```

The current generation platform is reused.

---

# 11. RAG Is a Workflow, Not an AICapability

RAG-00 formally defines RAG as an application workflow.

It should not simply become:

```python
AICapability.RAG
```

RAG is composed of multiple stages:

```text
RAG
=
Document Ingestion
+
Chunking
+
Embedding
+
Vector Storage
+
Retrieval
+
Prompt Construction
+
Text Generation
+
Citation Handling
+
Validation
```

Text generation is only one part of RAG.

The distinction is:

```text
Model capabilities:
- text generation
- chat
- embeddings

Application workflows:
- summarization
- RAG query
- document ingestion
```

---

# 12. Generation and Embeddings Are Different Capabilities

The project already has a generic `EmbeddingPort`.

RAG-00 intentionally avoids creating:

```text
app/application/ai/rag/domain/embedding_port.py
```

when the generic abstraction already belongs under:

```text
app/application/ai/domain/embedding_port.py
```

The conceptual ownership is:

```text
AIInferencePort
    |
    +--> text generation

EmbeddingPort
    |
    +--> vector generation
```

RAG uses both.

Embeddings may also later support:

```text
semantic search
recommendations
clustering
duplicate detection
similarity matching
```

Therefore embeddings should remain generic AI infrastructure rather than being owned only by RAG.

---

# 13. Features Enabled by Generic RAG

Once the generic RAG capability is implemented, it can support many AI features.

## 13.1 Chat With Documents

```text
Upload PDF
   |
   v
Index Document
   |
   v
Ask Questions
```

Example:

> What does this insurance contract say about accidental damage?

---

## 13.2 Company Knowledge Assistant

Index:

```text
HR policies
IT policies
travel policies
security procedures
employee handbook
```

Then ask:

> Can I carry forward unused annual leave?

---

## 13.3 Technical Documentation Assistant

Index:

```text
architecture documents
API documentation
runbooks
ADRs
engineering standards
```

Then ask:

> How does authentication work in this system?

---

## 13.4 Customer Support Assistant

Index:

```text
FAQs
product manuals
troubleshooting guides
return policies
support documentation
```

Then ask:

> My device displays error E43. What should I do?

---

## 13.5 Contract / Policy Search

Index:

```text
contracts
agreements
policies
```

Then ask:

> What is the termination notice period?

The answer can be returned with the relevant source.

---

# 14. Future OdinSync Integration

The first RAG implementation is intentionally generic.

No OdinSync-specific fields or business logic are required yet.

Later, OdinSync may use the generic RAG platform for knowledge such as:

```text
sales playbooks
company policies
product documentation
customer contracts
inventory procedures
technical documentation
```

A future OdinSync assistant could combine two kinds of information:

```text
Question:
Which leads have been inactive for 30 days
and what should I do next?
```

The architecture could become:

```text
                   Question
                      |
              +-------+-------+
              |               |
              v               v
       OdinSync CRM           RAG
       live data       Sales Playbook
              |               |
              +-------+-------+
                      |
                      v
                     LLM
                      |
                      v
               Combined Answer
```

Structured business data would come from OdinSync APIs.

Unstructured knowledge would come from RAG.

---

# 15. Domain Models Created in RAG-00

RAG-00 introduced the domain vocabulary for the future RAG platform.

These models are intentionally independent of:

```text
FastAPI
SQLAlchemy
Qdrant
Redis
OpenAI SDK
HTTPX
PDF parser libraries
```

This keeps the application layer testable and infrastructure-independent.

---

# 16. `Document`

File:

```text
app/application/ai/rag/domain/document.py
```

`Document` represents one logical knowledge source.

Examples:

```text
Employee Handbook
Product Manual
Technical Documentation
Policy Document
Markdown Article
Contract
PDF
```

Conceptually:

```text
Document
├── document_id
├── title
├── source
├── content_type
├── version
├── checksum
├── status
├── created_at
└── updated_at
```

Important distinction:

```text
Document != PDF parser object
Document != Qdrant point
Document != SQLAlchemy ORM row
```

It is the application's own representation of a knowledge document.

---

# 17. `DocumentStatus`

File:

```text
app/application/ai/rag/domain/document.py
```

`DocumentStatus` represents the lifecycle of a document during ingestion/indexing.

Conceptually:

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
   |           |
   |         Reindex
   |
   +------> DELETED

FAILED
   |
   +------> PROCESSING
   |           |
   |          Retry
   |
   +------> DELETED
```

Why this matters:

Without an explicit status, it becomes difficult to know whether:

```text
the upload was accepted
text extraction completed
embeddings were generated
vector indexing succeeded
the document is ready for retrieval
indexing failed
the document was deleted
```

The status provides a stable lifecycle contract.

---

# 18. `LoadedDocumentContent`

File:

```text
app/application/ai/rag/domain/document.py
```

`LoadedDocumentContent` represents the result of extracting content from a document source.

Conceptual flow:

```text
PDF
Markdown
TXT
 |
 v
DocumentLoaderPort
 |
 v
LoadedDocumentContent
```

This prevents parser-specific objects from leaking into the RAG application.

For example:

```text
PDF Loader
   |
   v
LoadedDocumentContent
   |
   v
TextNormalizer
   |
   v
TextChunker
```

A future PDF parser can be replaced without changing the rest of the application.

---

# 19. `DocumentChunk`

File:

```text
app/application/ai/rag/domain/chunk.py
```

A full document is usually too large to retrieve as one unit.

It is split into smaller pieces called chunks.

Example:

```text
Employee Handbook
   |
   +--> Chunk 0: Company introduction
   +--> Chunk 1: Working hours
   +--> Chunk 2: Leave policy
   +--> Chunk 3: Medical benefits
```

A conceptual chunk contains:

```text
DocumentChunk
├── chunk_id
├── document_id
├── document_version
├── chunk_index
├── text
├── chunking_version
├── section
└── page_number
```

The chunk becomes the main unit used for retrieval.

---

# 20. `EmbeddedChunk`

File:

```text
app/application/ai/rag/domain/chunk.py
```

`EmbeddedChunk` represents a document chunk plus its embedding.

Conceptually:

```text
DocumentChunk
      |
      v
EmbeddingPort
      |
      v
EmbeddedChunk
```

Example:

```text
EmbeddedChunk
├── chunk
│   └── "Employees receive 20 annual leave days."
│
├── embedding
│   └── [0.12, -0.48, 0.73, ...]
│
├── embedding_model
└── embedding_version
```

This becomes the logical object passed to the vector store.

The chunking layer does not need to know about Qdrant.

The embedding layer does not need to know about Qdrant.

The vector-store adapter accepts application-owned data.

---

# 21. `Citation`

File:

```text
app/application/ai/rag/domain/citation.py
```

`Citation` represents provenance for a generated answer.

Example:

```json
{
  "document_id": "employee-handbook",
  "chunk_id": "chunk-17",
  "title": "Employee Handbook",
  "page_number": 37
}
```

A citation should be provider-independent.

It should not expose infrastructure details such as:

```text
Qdrant point ID
Qdrant collection
embedding vector
internal database primary key
```

The application owns the citation concept.

---

# 22. `RetrievalQuery`

File:

```text
app/application/ai/rag/domain/retrieval.py
```

`RetrievalQuery` represents what the application wants to search for.

Conceptually:

```text
RetrievalQuery
├── query
├── top_k
├── minimum_score
└── optional controlled filters
```

Example:

```text
query:
"How much annual leave do employees receive?"

top_k:
5

minimum_score:
0.3
```

Score note:

```text
minimum_score is a configured threshold, not a guaranteed 0..1 normalized score.
Its final meaning belongs to the retriever/vector-store policy.
See docs/learning/rag/retrieval-score-semantics.md
```

This becomes the input to the retrieval service.

---

# 23. `RetrievedChunk`

File:

```text
app/application/ai/rag/domain/retrieval.py
```

`RetrievedChunk` represents one search result returned from vector retrieval.

Conceptually:

```text
RetrievedChunk
├── chunk_id
├── document_id
├── text
├── score
├── title
├── page_number
└── provenance metadata
```

Example:

```text
document_id: handbook
chunk_id: chunk-37
text: "Employees receive 20 annual leave days..."
score: 0.91
page_number: 37
```

The important architecture rule is:

```text
Vector DB SDK Result
        |
        v
Infrastructure Adapter
        |
        v
RetrievedChunk
        |
        v
Application
```

Application code should not depend directly on Qdrant SDK result classes.

---

# 24. `RetrievalResult`

File:

```text
app/application/ai/rag/domain/retrieval.py
```

A retrieval operation may return multiple relevant chunks.

Conceptually:

```text
RetrievalResult
    |
    +--> RetrievedChunk
    +--> RetrievedChunk
    +--> RetrievedChunk
```

This object represents the evidence retrieved for one question.

The result can later be used by:

```text
RAGPromptBuilder
RAGResponsePipeline
Citation assembly
Evaluation
```

---

# 25. `RAGResult`

File:

```text
app/application/ai/rag/domain/rag_result.py
```

`RAGResult` represents the final application/domain result of a RAG query.

Conceptually:

```text
RAGResult
├── status
├── answer
└── citations
```

Example:

```text
status:
SUCCESS

answer:
"Employees receive 20 annual leave days."

citations:
- Employee Handbook, page 37
```

Important distinction:

```text
RAGResult
!=
FastAPI HTTP response schema
```

The HTTP layer can later map:

```text
RAGResult
   |
   v
RAGResponse
   |
   v
JSON
```

The domain model should remain independent of FastAPI.

---

# 26. `RAGResultStatus`

File:

```text
app/application/ai/rag/domain/rag_result.py
```

This represents the kind of result produced by the RAG workflow.

A very important state is the no-context case.

Example:

```text
Question:
"What is our policy for employees travelling to Mars?"
```

If the knowledge base contains nothing relevant, the system should not do this:

```text
No retrieval result
      |
      v
Ask LLM using unrestricted model knowledge
      |
      v
Possibly invented answer
```

Instead:

```text
No retrieval result
      |
      v
RAGResult
status = NO_CONTEXT
```

The fundamental rule is:

```text
No Evidence
!=
Permission To Invent
```

No-context is treated as a normal domain result rather than necessarily being an infrastructure exception.

---

# 27. Ports Created in RAG-00

Ports are interfaces/contracts.

They define what the application needs without specifying which technology implements it.

Conceptually:

```text
Application
    |
    v
Port
    |
    v
Infrastructure Adapter
```

This allows the application logic to remain testable and provider-independent.

---

# 28. `DocumentLoaderPort`

File:

```text
app/application/ai/rag/domain/document_loader_port.py
```

Purpose:

```text
File / Source
     |
     v
DocumentLoaderPort
     |
     v
LoadedDocumentContent
```

Future implementations may include:

```text
PlainTextDocumentLoader
MarkdownDocumentLoader
PDFDocumentLoader
```

The ingestion use case should not directly depend on a PDF parsing library.

---

# 29. `DocumentRepositoryPort`

File:

```text
app/application/ai/rag/domain/document_repository_port.py
```

Purpose:

```text
Document Metadata
      |
      v
DocumentRepositoryPort
      |
      v
SQLAlchemy Adapter
      |
      v
PostgreSQL
```

Future responsibilities may include:

```text
document identity
checksum
document version
status
index version
processing state
created_at
updated_at
```

This repository will support:

```text
idempotent ingestion
reindexing
recovery
document lifecycle
```

without exposing SQLAlchemy types to application code.

---

# 30. `VectorStorePort`

File:

```text
app/application/ai/rag/domain/vector_store_port.py
```

Purpose:

```text
EmbeddedChunk[]
      |
      v
VectorStorePort
      |
      v
Qdrant Adapter
      |
      v
Vector Database
```

It will also support retrieval:

```text
Query Embedding
      |
      v
VectorStorePort.search(...)
      |
      v
RetrievedChunk[]
```

The application therefore uses:

```python
vector_store.search(...)
```

rather than:

```python
qdrant_client.search(...)
```

The main benefit is not arbitrary vendor swapping.

The main benefits are:

```text
dependency direction
testability
infrastructure isolation
clean application contracts
```

---

# 31. Data Ownership

RAG-00 establishes a clear future ownership model.

## PostgreSQL

Future authoritative metadata store:

```text
document identity
document version
checksum
ingestion state
indexing state
processing versions
timestamps
```

## Vector Store

Future rebuildable retrieval index:

```text
vectors
chunk retrieval representation
similarity-search metadata
```

## Redis

Future temporary/cache infrastructure:

```text
RAG answer cache
short-lived coordination data
temporary cache
```

Redis is not document persistence.

The important recovery principle is:

```text
Vector Database Lost
        |
        v
Rebuild Retrieval Index
from Authoritative Document State
```

---

# 32. Provenance Chain

RAG-00 establishes provenance as part of the architecture.

The future chain is:

```text
Document
   |
   v
DocumentChunk
   |
   v
EmbeddedChunk
   |
   v
RetrievedChunk
   |
   v
RAG Context
   |
   v
Generated Answer
   |
   v
Citation
```

Citations should therefore come from actual retrieved evidence rather than being guessed after generation.

---

# 33. No Premature Infrastructure

RAG-00 intentionally does not implement:

```text
Qdrant
RAG routes
Alembic document tables
PDF extraction
chunking implementation
retrieval
RAG generation
RAG API
LangChain
LlamaIndex
```

This is intentional.

Before RAG-00:

```text
"We want to add RAG."
```

After RAG-00:

```text
"We know how RAG fits into the existing system,
which domain concepts exist,
which ports are required,
which infrastructure is reusable,
and which responsibilities belong where."
```

---

# 34. Current Architecture After RAG-00

```text
                    AI Foundation
                          |
             +------------+------------+
             |                         |
      Generic AI Infrastructure      RAG Domain
             |                         |
      AIInferencePort                Document
      EmbeddingPort                  DocumentStatus
      InferenceRouter                LoadedDocumentContent
      ModelRegistry                  DocumentChunk
      Ollama/OpenAI                  EmbeddedChunk
      Redis                          Citation
      Logging                        RetrievalQuery
      Metrics                        RetrievedChunk
      Tracing                        RetrievalResult
                                     RAGResult
                                     RAGResultStatus
                                         |
                                         +-- DocumentLoaderPort
                                         +-- DocumentRepositoryPort
                                         +-- VectorStorePort
```

---

# 35. Future Complete RAG Architecture

The eventual ingestion path should resemble:

```text
POST /rag/documents
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

The eventual query path should resemble:

```text
POST /rag/query
      |
      v
RAGQueryUseCase
      |
      +--> Query Guardrails
      |
      +--> Retriever
      |       |
      |       +--> EmbeddingPort
      |       |
      |       +--> VectorStorePort
      |
      +--> RAGPromptBuilder
      |
      +--> AIInferencePort
      |       |
      |       v
      |  InferenceRouter
      |       |
      |   Ollama/OpenAI
      |
      +--> RAGResponsePipeline
      |
      v
RAGResult
   |
   +--> Answer
   +--> Citations
```

---

# 36. Simple Mental Model

The easiest way to remember RAG is:

```text
STORE
  ↓
SEARCH
  ↓
ANSWER
```

## STORE

```text
Document
-> Extract
-> Chunk
-> Embed
-> Vector Database
```

## SEARCH

```text
Question
-> Embed
-> Similarity Search
-> Relevant Chunks
```

## ANSWER

```text
Question
+
Relevant Chunks
-> LLM
-> Grounded Answer
-> Citations
```

---

# 37. What RAG Does Not Do

RAG does **not** permanently retrain or teach the model.

It does not normally modify model weights.

Instead:

```text
Knowledge Base
      |
      v
Retrieve Relevant Evidence
      |
      v
Supply Evidence at Request Time
      |
      v
Generate Answer
```

This distinction is important.

RAG is primarily a retrieval-and-context architecture around an existing LLM.

---

# 38. Key Architectural Rules Going Forward

1. RAG is an application workflow.
2. Reuse `AIInferencePort` for final text generation.
3. Reuse the existing `InferenceRouter`, `ModelRegistry`, Ollama and OpenAI adapters.
4. Keep embeddings under the generic `EmbeddingPort`.
5. Do not duplicate provider clients inside RAG.
6. Access vector infrastructure through `VectorStorePort`.
7. Keep PostgreSQL as the authoritative lifecycle metadata store.
8. Treat the vector database as a rebuildable retrieval index.
9. Use Redis only for cache/temporary concerns.
10. Keep ingestion and querying as separate workflows.
11. Preserve provenance throughout the entire pipeline.
12. No relevant context must not silently fall back to unrestricted model knowledge.
13. Retrieved content should be treated as evidence, not trusted system instructions.
14. Keep infrastructure SDK types out of use cases.
15. Keep the first RAG implementation generic and independent of OdinSync.
16. Add OdinSync-specific tenancy, authorization, and business-data integration later.

---

# 39. Recommended Learning Sequence

To understand the implementation as it evolves, study RAG in this order:

```text
1. RAG fundamentals
2. Documents
3. Chunking
4. Embeddings
5. Vector databases
6. Similarity search
7. Retrieval
8. RAG prompt construction
9. Generation
10. Citations
11. Groundedness
12. Evaluation
13. Security
14. Observability
15. Scaling
16. Multi-tenant integration
17. OdinSync integration
```

This matches the architecture being built in `ai-engineer-foundation`.

---

# 40. One-Sentence Summary

**RAG extends an LLM by retrieving relevant external knowledge at request time, supplying that knowledge as context, and generating a source-aware answer without retraining the model.**

RAG-00 establishes the domain vocabulary and architecture required to build that workflow cleanly on top of the existing AI platform.
