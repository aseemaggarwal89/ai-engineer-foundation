# RAG From the Beginning — Concepts, Workflow, AI Feature Integration, and RAG-00 Models

## Why This Document Exists

This document answers the question:

> **“RAG is a new thing for me. Explain it from the beginning, explain how RAG will help create new AI feature integrations, and explain the models created in RAG-00.”**

It is intended to be a future learning and architecture reference for the `ai-engineer-foundation` project.

At the end of **RAG-00 — Architecture ADR and Domain Contracts**, the project has defined the vocabulary, architectural boundaries, domain models, and ports required for RAG.

RAG itself is **not implemented yet**.

The following are still future implementation work:

- document ingestion;
- document extraction;
- normalization;
- chunking;
- embedding integration;
- vector storage;
- vector search;
- retrieval;
- RAG prompt construction;
- RAG answer generation;
- citations in the API;
- RAG evaluation;
- RAG security;
- RAG observability.

The existing AI generation infrastructure, however, can be reused.

---

# 1. First: What Does an LLM Normally Do?

Suppose the current AI service receives:

```text
Summarize this text:
...
```

The current application roughly follows:

```text
User
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
  +---- Ollama
  |
  +---- OpenAI
  |
  v
Answer
```

A Large Language Model normally answers using:

1. knowledge learned during model training;
2. information included directly in the current prompt.

This works well for generic operations such as:

```text
summarization
rewriting
classification
general question answering
```

But consider this question:

> What is the leave policy in my company's employee handbook?

The LLM does not automatically know the private contents of your company's employee handbook.

The model might still answer, but it could answer from generic information learned during training.

That answer may be completely different from the real company policy.

This is the problem RAG is designed to address.

---

# 2. Why Not Simply Send the Entire Document to the LLM?

Imagine the employee handbook contains 200 pages.

One naive solution would be:

```text
Prompt:

Here is my entire 200-page employee handbook:

<all 200 pages>

Question:

How many annual leave days do employees receive?
```

Technically, a sufficiently large model context may allow this in some situations.

But it introduces several problems:

```text
Huge prompts
High token usage
Higher cost
Higher latency
Context-window limits
Too much irrelevant information
Harder reasoning
More difficult prompt management
```

The answer may exist on only one page.

For example:

```text
Page 37
```

There is no reason to repeatedly send all 200 pages when only a small section is relevant.

We need a system that first finds the relevant section.

That is where RAG begins.

---

# 3. What Is RAG?

**RAG = Retrieval-Augmented Generation**

The name contains two important ideas:

```text
Retrieval
+
Augmented Generation
```

## Retrieval

Search the external knowledge base and find information relevant to the user's question.

## Augmented Generation

Add that retrieved information to the LLM prompt so the model can generate an answer using the retrieved evidence.

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
Retrieve Relevant Information
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

The LLM is still responsible for generation.

RAG adds a knowledge retrieval system **before generation**.

---

# 4. Concrete RAG Example

Suppose the knowledge base contains:

```text
Employee Handbook

Pages 1-20:
Company information

Pages 21-35:
Working hours

Pages 36-40:
Leave policy

Pages 41-55:
Travel policy

Pages 56-70:
Medical benefits
```

The user asks:

> How many annual leave days do employees get?

Instead of sending the entire handbook to the model, RAG first searches it.

```text
Question:
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

The application can additionally return:

```json
{
  "answer": "Employees receive 20 days of annual leave.",
  "citations": [
    {
      "document_id": "employee-handbook",
      "title": "Employee Handbook",
      "page_number": 37
    }
  ]
}
```

Now the answer has:

```text
retrieved evidence
+
generated explanation
+
source provenance
```

---

# 5. But How Does RAG Search a Document?

Searching becomes more interesting when the question and source use different words.

Suppose the knowledge base contains:

```text
A:
Employees receive 20 annual leave days.

B:
Laptops must be returned before leaving the company.

C:
Medical insurance covers employees and their family.
```

The user asks:

```text
How much vacation time do I get?
```

The user used:

```text
vacation
```

but the document used:

```text
annual leave
```

A basic keyword search may not always understand that these concepts are related.

We want the system to understand:

```text
vacation
≈
annual leave
```

This is where embeddings become useful.

---

# 6. What Is an Embedding?

An **embedding** converts text into a numerical vector.

For example:

```text
"annual leave policy"
        |
        v
Embedding Model
        |
        v
[0.12, -0.48, 0.73, 0.19, ...]
```

Another sentence:

```text
"employee vacation allowance"
        |
        v
Embedding Model
        |
        v
[0.14, -0.45, 0.70, 0.22, ...]
```

The vectors may contain hundreds or thousands of dimensions.

You do not normally interpret individual numbers manually.

The important idea is that text with similar meaning tends to have vector representations that are relatively close in embedding space.

Conceptually:

```text
annual leave
      ●
     /
    /
   ● vacation allowance


                       ● laptop return policy
```

This provides a mathematical representation that can be used for semantic search.

---

# 7. Why Embeddings Help RAG

Consider:

```text
Document:
"Employees receive 20 annual leave days."

Question:
"How much vacation time do I get?"
```

The wording is different.

The meaning is similar.

The flow becomes:

```text
Question
   |
   v
Embedding Model
   |
   v
Question Vector
```

The document chunk was already converted to another vector during ingestion.

The system compares those vectors.

If they are semantically similar, the document chunk should appear near the top of the retrieval results.

Therefore RAG can retrieve relevant knowledge even when the exact wording differs.

---

# 8. What Is a Vector Database?

Once document chunks have embeddings, those vectors need to be stored somewhere that supports efficient similarity search.

That is the role of a vector database.

Conceptually, it stores records such as:

```text
Chunk 1

text:
"Employees receive 20 annual leave days."

vector:
[0.12, -0.48, 0.73, ...]

metadata:
document_id = employee-handbook
page = 37
```

Another record:

```text
Chunk 2

text:
"Employees must return company laptops."

vector:
[-0.42, 0.11, 0.19, ...]

metadata:
document_id = employee-handbook
page = 85
```

Another:

```text
Chunk 3

text:
"Medical insurance covers employees..."

vector:
[...]
```

Now consider the user question:

```text
How much vacation time do employees get?
```

The system creates an embedding:

```text
Question
   |
   v
Embedding Model
   |
   v
[0.13, -0.46, 0.72, ...]
```

The vector database searches for stored vectors closest to the question vector.

Possible result:

```text
1. Annual leave chunk       score 0.91
2. Leave carry-forward      score 0.84
3. Leave approval policy    score 0.78
```

Those chunks become the context supplied to the LLM.

The planned project architecture will hide the actual vector database behind:

```text
VectorStorePort
```

A future implementation can use:

```text
Qdrant
```

without coupling application logic directly to Qdrant APIs.

---


# 8A. What Is Qdrant?

**Qdrant** is a vector database.

In this project, Qdrant is planned as the infrastructure that will store document embeddings and perform similarity search for RAG.

The name itself does not represent a RAG concept. Qdrant is a specific technology/product that implements the vector-search part of the architecture.

The relationship is:

```text
RAG
 |
 +--> needs vector search
          |
          v
    VectorStorePort
          |
          v
   QdrantVectorStore
          |
          v
        Qdrant
```

The application should not depend directly on Qdrant.

Instead:

```text
Application / Retriever
        |
        v
VectorStorePort
        |
        v
Qdrant Adapter
        |
        v
Qdrant
```

This keeps Qdrant as an infrastructure implementation rather than making it part of the core RAG domain.

---

# 8B. What Does Qdrant Store?

Suppose this document chunk exists:

```text
"Employees receive 20 annual leave days each calendar year."
```

The embedding model converts it into a vector:

```text
[0.12, -0.48, 0.73, 0.19, ...]
```

Qdrant can store:

```text
Vector:
[0.12, -0.48, 0.73, ...]

Payload / Metadata:
document_id = employee-handbook
chunk_id = chunk-37
title = Employee Handbook
page_number = 37

Text or text reference:
"Employees receive 20 annual leave days each calendar year."
```

Conceptually:

```text
Qdrant Record
├── vector
├── chunk_id
├── document_id
├── page_number
├── title
└── other retrieval metadata
```

The exact storage design will be decided in later implementation tasks.

---

# 8C. What Does Qdrant Do During a RAG Query?

The user asks:

```text
How much vacation time do employees receive?
```

First:

```text
Question
   |
   v
EmbeddingPort
   |
   v
Question Vector
```

For example:

```text
[0.13, -0.46, 0.72, ...]
```

Then the application asks the vector store:

```text
Find the stored vectors most similar to this query vector.
```

The future flow is:

```text
Question Vector
      |
      v
VectorStorePort.search(...)
      |
      v
QdrantVectorStore
      |
      v
Qdrant Similarity Search
      |
      v
Relevant Chunks
```

Qdrant may return results conceptually like:

```text
1. Employee Handbook / Leave Policy
   score = 0.91

2. Employee Handbook / Carry Forward Policy
   score = 0.84

3. Employee Handbook / Leave Approval
   score = 0.78
```

The Qdrant adapter converts those infrastructure results into application-owned:

```text
RetrievedChunk[]
```

The rest of the RAG application does not need to know that Qdrant was used.

---

# 8D. Why Use Qdrant Instead of PostgreSQL for Everything?

PostgreSQL and Qdrant solve different problems in the proposed architecture.

## PostgreSQL

Used for authoritative business/application state:

```text
document identity
document version
checksum
processing status
indexing status
created_at
updated_at
```

## Qdrant

Used for retrieval:

```text
embedding vectors
similarity search
chunk retrieval metadata
```

Conceptually:

```text
                 RAG Data

        +-----------------------+
        |                       |
        v                       v
   PostgreSQL                Qdrant
        |                       |
authoritative state       retrieval index
        |                       |
document lifecycle        embeddings
versions                  chunks
status                    similarity search
```

The design deliberately avoids making Qdrant the only authoritative document store.

---

# 8E. Why Qdrant Is Called a Rebuildable Retrieval Index

Suppose Qdrant data is lost.

The system should eventually be able to rebuild it:

```text
Authoritative Document
        |
        v
Load Content
        |
        v
Chunk
        |
        v
Generate Embeddings
        |
        v
Re-index Into Qdrant
```

Therefore:

```text
Qdrant
=
optimized searchable index
```

not:

```text
Qdrant
=
only source of document truth
```

This is why PostgreSQL and document lifecycle metadata remain important.

---

# 8F. Qdrant vs `VectorStorePort`

These two names have different meanings.

## `VectorStorePort`

This is **our application interface**.

It defines what the RAG application needs:

```text
store vectors
search vectors
delete document vectors
possibly health/check operations
```

It does not know which product performs those operations.

## Qdrant

Qdrant is **one infrastructure implementation** of that interface.

Future architecture:

```text
VectorStorePort
      |
      +--> QdrantVectorStore
      |
      +--> another implementation, if ever needed
```

This separation provides:

```text
clean architecture
testability
provider isolation
easier local fakes
less infrastructure coupling
```

For example, a unit test can use:

```text
FakeVectorStore
```

instead of starting Qdrant.

---

# 8G. Simple Way to Remember Qdrant

Use this mental model:

```text
PostgreSQL
=
"What documents do I have and what is their state?"

Qdrant
=
"Which chunks are semantically closest to this question?"

Redis
=
"Do I already have a temporary/cached result?"
```

Or even simpler:

```text
PostgreSQL -> source-of-truth metadata
Qdrant     -> semantic search
Redis      -> cache
```

For RAG:

```text
Document
   |
   v
Chunk
   |
   v
Embedding
   |
   v
Qdrant
   |
   v
Semantic Retrieval
   |
   v
LLM
```


# 9. RAG Has Two Completely Different Workflows

This is one of the most important concepts to understand.

There are two major flows:

```text
1. INGESTION / INDEXING
2. QUERY / RETRIEVAL / GENERATION
```

These happen at different times.

---

# 10. Workflow A — Document Ingestion

Ingestion prepares documents for future search.

Example:

```text
Employee Handbook.pdf
        |
        v
Load Document
        |
        v
Extract Text
        |
        v
Normalize Text
        |
        v
Split Into Chunks
        |
        v
Generate Embedding For Every Chunk
        |
        v
Store Vectors + Metadata
        |
        v
Knowledge Base Ready
```

A more architecture-oriented version is:

```text
Document
   |
   v
DocumentLoaderPort
   |
   v
LoadedDocumentContent
   |
   v
TextNormalizer
   |
   v
TextChunker
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

The ingestion workflow normally happens when:

```text
a new document is uploaded
a document changes
a document is re-indexed
the embedding model changes
the chunking strategy changes
the vector index is rebuilt
```

It does not need to run for every question.

---

# 11. Workflow B — RAG Query

The query workflow happens when a user asks a question.

Example:

```text
Question
   |
   v
Generate Query Embedding
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
   +---- Ollama
   |
   +---- OpenAI
   |
   v
Generated Answer
   |
   v
Validation
   |
   v
Answer + Citations
```

So the difference is:

```text
Ingestion:
knowledge -> searchable representation

Query:
question -> relevant knowledge -> answer
```

---

# 12. Why Your Existing AI Platform Is Valuable

The project already has many components that RAG needs for the **generation** portion:

```text
FastAPI

dependency injection

ServiceContainer

AIInferencePort

InferenceRouter

ModelRegistry

OllamaAdapter

OpenAIAdapter

timeouts

retry

provider fallback

circuit breakers

Redis

guardrails

response pipelines

exception handling

structured logging

Prometheus metrics

OpenTelemetry tracing
```

Therefore RAG should not rebuild generation.

The architecture should become:

```text
                     NEW RAG AREA

Question
   |
   v
Retriever
   |
   +---- EmbeddingPort
   |
   +---- VectorStorePort
   |
   v
RetrievedChunk[]
   |
   v
RAGPromptBuilder

                 EXISTING AI PLATFORM
                           |
                           v
                    AIInferencePort
                           |
                           v
                    InferenceRouter
                      /         \
                  Ollama       OpenAI
                           |
                           v
                    Generated Answer

                     NEW RAG AREA
                           |
                           v
                 Validation + Citations
```

This is an important architecture advantage.

---

# 13. What We Do NOT Need to Rebuild

RAG should not create another provider stack like:

```text
RAGOpenAIAdapter

RAGOllamaAdapter

RAGInferenceRouter

RAGModelRegistry
```

Instead:

```text
RAG
 |
 v
existing AIInferencePort
 |
 v
existing InferenceRouter
 |
 v
existing provider adapters
```

The RAG layer is built **around** the existing inference platform.

---

# 14. Why RAG Is Not `AICapability.RAG`

RAG-00 formally decided that RAG is an **application workflow**.

RAG consists of:

```text
document ingestion
+
text extraction
+
chunking
+
embeddings
+
vector storage
+
retrieval
+
prompt construction
+
generation
+
citations
+
validation
```

Therefore:

```text
RAG
!=
single model operation
```

A model capability might be:

```text
text generation
chat
embedding
```

An application workflow can be:

```text
summarization
RAG query
document ingestion
```

The generation portion of RAG can reuse an existing generation capability.

---

# 15. Generation and Embeddings Are Different

The project already has a generic:

```text
EmbeddingPort
```

RAG-00 intentionally keeps embeddings outside the RAG-specific domain package.

The conceptual ownership is:

```text
AIInferencePort
       |
       +--> text generation

EmbeddingPort
       |
       +--> embeddings / vectors
```

Then:

```text
RAG
 |
 +--> uses EmbeddingPort
 |
 +--> uses AIInferencePort
```

Embeddings may later also support features beyond RAG:

```text
semantic search

recommendations

duplicate detection

similarity matching

clustering
```

Therefore embeddings are a generic AI capability.

---

# 16. How RAG Enables New AI Features

Once the generic RAG platform is implemented, the AI service becomes capable of much more than simple summarization.

---

## Feature 1 — Chat With Documents

A user uploads:

```text
insurance-policy.pdf
```

Then asks:

> What does this policy say about accidental damage?

Flow:

```text
PDF
 |
 v
Index Document
 |
 v
Ask Question
 |
 v
Retrieve Relevant Clause
 |
 v
Generate Answer
 |
 v
Return Citation
```

---

## Feature 2 — Company Knowledge Assistant

Index:

```text
Employee Handbook

HR Policies

IT Policies

Travel Policies

Security Procedures
```

Then employees can ask:

> Can I carry forward unused annual leave?

The assistant retrieves the real company policy before answering.

---

## Feature 3 — Technical Documentation Assistant

Index:

```text
architecture documents

API documentation

ADRs

runbooks

engineering standards

deployment documents
```

Then ask:

> How does authentication work in the platform?

The assistant can answer from the actual internal documentation.

---

## Feature 4 — Customer Support Assistant

Index:

```text
FAQs

product manuals

troubleshooting guides

return policies

support documentation
```

Ask:

> My device displays error E43. What should I do?

RAG retrieves the relevant troubleshooting section.

---

## Feature 5 — Contract or Policy Assistant

Index:

```text
contracts

agreements

policies
```

Ask:

> What is the termination notice period?

The system can answer and point to the relevant clause.

---

# 17. Future OdinSync Integration

The first RAG platform should remain generic.

Later OdinSync may use it for:

```text
sales playbooks

product documentation

customer contracts

inventory procedures

company policies

technical documents
```

A future query could be:

> Which leads have been inactive for 30 days and what does the sales playbook recommend?

That question contains two different information sources.

### Structured live information

```text
Which leads have been inactive for 30 days?
```

This should come from:

```text
OdinSync CRM API
```

### Unstructured knowledge

```text
What does the sales playbook recommend?
```

This can come from:

```text
RAG
```

Combined future architecture:

```text
                    Question
                       |
               +-------+-------+
               |               |
               v               v
         OdinSync CRM          RAG
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

This is much stronger than storing all CRM rows in a vector database.

---

# 18. Models Created in RAG-00

RAG-00 created the domain vocabulary needed for future RAG implementation.

These models are intended to stay independent of:

```text
FastAPI

SQLAlchemy

Qdrant

Redis

OpenAI SDK

HTTPX

PDF parser libraries
```

This separation makes the architecture easier to test, maintain, and extend.

---

# 19. `Document`

File:

```text
app/application/ai/rag/domain/document.py
```

`Document` represents a logical knowledge source.

Examples:

```text
Employee Handbook

Product Manual

Policy Document

Technical Documentation

Markdown Article

Customer Contract
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

Important:

```text
Document
!=
PDF parser object

Document
!=
Qdrant point

Document
!=
SQLAlchemy ORM object
```

It is the application's own domain representation.

---

# 20. Why `Document` Matters

Without a domain `Document`, different parts of the application could pass around:

```text
file names

database rows

Qdrant metadata

random dictionaries
```

Instead the application gets one stable concept:

```text
Document
```

Infrastructure can change while the domain concept remains stable.

---

# 21. `DocumentStatus`

Also located in:

```text
document.py
```

It represents the document lifecycle.

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
```

Later:

```text
INDEXED
   |
   +------> PROCESSING
   |            |
   |          Reindex
   |
   +------> DELETED
```

Possible retry:

```text
FAILED
   |
   v
PROCESSING
```

This helps answer operational questions such as:

```text
Was the document received?

Is extraction running?

Was embedding successful?

Is the document searchable?

Did indexing fail?

Was the document deleted?
```

---

# 22. `LoadedDocumentContent`

File:

```text
app/application/ai/rag/domain/document.py
```

A document may originate from:

```text
PDF
TXT
Markdown
```

Different infrastructure libraries may be required to extract those formats.

But the rest of the application should not care which parser was used.

The boundary becomes:

```text
PDF
TXT
Markdown
 |
 v
DocumentLoaderPort
 |
 v
LoadedDocumentContent
```

Then:

```text
LoadedDocumentContent
 |
 v
TextNormalizer
 |
 v
TextChunker
```

So parser-specific objects do not leak into RAG application code.

---

# 23. `DocumentChunk`

File:

```text
app/application/ai/rag/domain/chunk.py
```

A complete document is often too large and too broad to use as one retrieval unit.

It is split into smaller pieces.

Example:

```text
Employee Handbook
   |
   +--> Chunk 0
   |    Company introduction
   |
   +--> Chunk 1
   |    Working hours
   |
   +--> Chunk 2
   |    Annual leave
   |
   +--> Chunk 3
        Medical insurance
```

A conceptual `DocumentChunk` includes:

```text
chunk_id

document_id

document_version

chunk_index

text

chunking_version

page_number

section
```

The chunk becomes the fundamental searchable knowledge unit.

---

# 24. Why Chunk Documents?

Suppose the full handbook contains:

```text
50,000 words
```

The user asks one leave-related question.

Retrieving the entire handbook is unnecessary.

Instead:

```text
Question
    |
    v
Find Leave-Related Chunk
    |
    v
Provide Small Relevant Context
```

Chunking improves the precision of retrieval and reduces prompt size.

Later tasks will determine the chunking strategy.

---

# 25. `EmbeddedChunk`

File:

```text
app/application/ai/rag/domain/chunk.py
```

A `DocumentChunk` contains text.

An `EmbeddedChunk` contains:

```text
DocumentChunk
+
Embedding Vector
+
Embedding Metadata
```

Flow:

```text
DocumentChunk
      |
      v
EmbeddingPort
      |
      v
EmbeddedChunk
```

Conceptually:

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

This is the type of information the vector-store adapter can index.

---

# 26. Why Separate `DocumentChunk` and `EmbeddedChunk`?

Because these represent different stages.

```text
DocumentChunk
=
text prepared for indexing
```

while:

```text
EmbeddedChunk
=
text + numerical semantic representation
```

This keeps chunking independent from embedding generation.

---

# 27. `RetrievalQuery`

File:

```text
app/application/ai/rag/domain/retrieval.py
```

When a user asks:

```text
How much annual leave do employees receive?
```

the retrieval system needs a structured request.

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

The system can then ask:

> Find up to five sufficiently relevant knowledge chunks.

---

# 28. `RetrievedChunk`

File:

```text
app/application/ai/rag/domain/retrieval.py
```

The vector store returns matches.

A match is converted into an application-owned:

```text
RetrievedChunk
```

Conceptually:

```text
RetrievedChunk
├── document_id
├── chunk_id
├── text
├── score
├── title
├── page_number
└── provenance metadata
```

Example:

```text
document_id:
employee-handbook

chunk_id:
chunk-37

text:
"Employees receive 20 annual leave days."

score:
0.91

page_number:
37
```

The vector-store SDK object stays inside infrastructure.

---

# 29. Why `RetrievedChunk` Matters

Without this abstraction:

```text
RAGQueryUseCase
 |
 v
Qdrant SDK object
```

The application becomes coupled to Qdrant.

Instead:

```text
Qdrant SDK object
      |
      v
QdrantVectorStore
      |
      v
RetrievedChunk
      |
      v
Application
```

The application understands retrieval concepts rather than Qdrant implementation details.

---

# 30. `RetrievalResult`

File:

```text
app/application/ai/rag/domain/retrieval.py
```

A retrieval operation can return multiple chunks.

For example:

```text
RetrievedChunk 1
score: 0.91

RetrievedChunk 2
score: 0.84

RetrievedChunk 3
score: 0.78
```

Together they form:

```text
RetrievalResult
```

Conceptually:

```text
RetrievalResult
    |
    +--> RetrievedChunk
    |
    +--> RetrievedChunk
    |
    +--> RetrievedChunk
```

This becomes the evidence available to the RAG workflow.

---

# 31. `Citation`

File:

```text
app/application/ai/rag/domain/citation.py
```

The system should be able to tell the user where an answer came from.

A conceptual citation:

```json
{
  "document_id": "employee-handbook",
  "chunk_id": "chunk-37",
  "title": "Employee Handbook",
  "page_number": 37
}
```

The public citation should not expose infrastructure details such as:

```text
Qdrant internal point ID

Qdrant collection name

embedding vector

internal database primary key
```

A citation represents user/application-level provenance.

---

# 32. Citation Provenance

The provenance chain should be preserved throughout RAG:

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

The application should not generate citations by guessing which source was probably used.

Citations should come from the actual evidence included in the RAG context.

---

# 33. `RAGResult`

File:

```text
app/application/ai/rag/domain/rag_result.py
```

This is the final **domain result** of a RAG query.

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

Important:

```text
RAGResult
!=
FastAPI HTTP response schema
```

Later:

```text
RAGResult
   |
   v
RAGResponse
   |
   v
JSON
```

The domain remains independent of FastAPI.

---

# 34. `RAGResultStatus`

Also in:

```text
rag_result.py
```

A crucial RAG outcome is:

```text
NO_CONTEXT
```

Suppose the user asks:

> What is our policy for employees travelling to Mars?

The knowledge base has no relevant information.

The system should **not** automatically do this:

```text
No Retrieved Context
      |
      v
Ask LLM Using Model Memory
      |
      v
Possibly Invented Answer
```

Instead:

```text
No Retrieved Context
      |
      v
RAGResult
status = NO_CONTEXT
```

The key rule is:

```text
No Evidence
!=
Permission To Invent
```

No-context is therefore a normal domain outcome.

---

# 35. Ports Created in RAG-00

Ports are not ordinary data models.

They are interfaces/contracts.

A port says:

> The application needs this capability, but it does not care which infrastructure technology provides it.

General architecture:

```text
Application
    |
    v
Port
    |
    v
Infrastructure Adapter
```

---

# 36. `DocumentLoaderPort`

File:

```text
app/application/ai/rag/domain/document_loader_port.py
```

Its responsibility is:

```text
Document Source
      |
      v
DocumentLoaderPort
      |
      v
LoadedDocumentContent
```

Future implementations can include:

```text
PlainTextDocumentLoader

MarkdownDocumentLoader

PDFDocumentLoader
```

The use case should not directly import a PDF library.

---

# 37. Why `DocumentLoaderPort` Matters

Without the port:

```text
IndexDocumentUseCase
      |
      v
PyPDF / parser library
```

Now application logic depends directly on infrastructure.

With the port:

```text
IndexDocumentUseCase
      |
      v
DocumentLoaderPort
      |
      +--> PDF implementation
      |
      +--> Markdown implementation
      |
      +--> Text implementation
```

The application remains stable if extraction technology changes.

---

# 38. `DocumentRepositoryPort`

File:

```text
app/application/ai/rag/domain/document_repository_port.py
```

It represents persistence of authoritative document metadata.

Future:

```text
DocumentRepositoryPort
       |
       v
SQLAlchemyDocumentRepository
       |
       v
PostgreSQL
```

Possible stored information:

```text
document identity

checksum

document version

document status

indexing status

chunking version

embedding version

timestamps
```

It supports future behaviors such as:

```text
idempotent ingestion

reindexing

retry

recovery

document lifecycle management
```

---

# 39. `VectorStorePort`

File:

```text
app/application/ai/rag/domain/vector_store_port.py
```

It abstracts vector indexing and retrieval.

Indexing:

```text
EmbeddedChunk[]
      |
      v
VectorStorePort
      |
      v
QdrantVectorStore
      |
      v
Qdrant
```

Searching:

```text
Query Embedding
      |
      v
VectorStorePort.search(...)
      |
      v
RetrievedChunk[]
```

The application should use:

```python
vector_store.search(...)
```

rather than directly using:

```python
qdrant_client.search(...)
```

---

# 40. Why Use `VectorStorePort`?

The primary benefits are:

```text
clean dependency direction

unit testability

infrastructure isolation

stable application contracts
```

It also makes changing implementations possible later, but provider swapping is not the main goal.

For unit tests:

```text
Retriever
   |
   v
FakeVectorStore
```

No real Qdrant service is needed.

---

# 41. Future Ingestion Flow Using the New Models

The models created in RAG-00 will eventually fit together like this:

```text
Document
   |
   v
DocumentLoaderPort
   |
   v
LoadedDocumentContent
   |
   v
TextNormalizer
   |
   v
TextChunker
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

The `DocumentRepositoryPort` separately maintains authoritative document lifecycle state.

---

# 42. Future Query Flow Using the New Models

The query side will eventually become:

```text
User Question
    |
    v
RetrievalQuery
    |
    v
EmbeddingPort
    |
    v
Query Embedding
    |
    v
VectorStorePort
    |
    v
RetrievalResult
    |
    +--> RetrievedChunk
    +--> RetrievedChunk
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
    +---- Ollama
    |
    +---- OpenAI
    |
    v
Generated Answer
    |
    v
RAGResponsePipeline
    |
    v
RAGResult
    |
    +--> Answer
    |
    +--> Citation[]
```

---

# 43. PostgreSQL, Vector Store, and Redis Have Different Responsibilities

RAG-00 establishes a future separation of data ownership.

## PostgreSQL

Authoritative application metadata:

```text
document identity

document version

checksum

document status

ingestion state

indexing state

processing versions

timestamps
```

---

## Vector Store

Rebuildable retrieval index:

```text
embedding vectors

chunk retrieval representation

similarity-search metadata
```

---

## Redis

Temporary/cache infrastructure:

```text
RAG answer cache

short-lived coordination state

temporary data
```

Redis is not document persistence.

---

# 44. Why the Vector Database Is Not the Source of Truth

Suppose Qdrant is corrupted or lost.

A robust architecture should support:

```text
Vector Database Lost
        |
        v
Read Authoritative Document State
        |
        v
Recreate Chunks
        |
        v
Recreate Embeddings
        |
        v
Rebuild Vector Index
```

Therefore the vector database is an optimized search index, not the only copy of the knowledge state.

---

# 45. Why RAG-00 Did Not Implement Qdrant Yet

RAG-00 intentionally stopped at architecture and contracts.

It did **not** implement:

```text
Qdrant

database migrations

document ORM models

document upload APIs

PDF parsing

chunking

embedding batching

retrieval

RAG generation

RAG HTTP endpoints

LangChain

LlamaIndex
```

This is intentional.

Before RAG-00:

```text
"We want RAG."
```

After RAG-00:

```text
"We know what RAG means in this project,
which components are generic,
which domain models exist,
which ports are required,
and how future infrastructure must connect."
```

---

# 46. Current Architecture After RAG-00

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
                                         |
                                         +-- DocumentRepositoryPort
                                         |
                                         +-- VectorStorePort
```

---

# 47. Full Future Generic RAG Architecture

```text
                         Client
                           |
                           v
                    FastAPI RAG API
                           |
                    Request Guardrails
                           |
               +-----------+-----------+
               |                       |
               v                       v
         Ingestion Flow            Query Flow
               |                       |
               v                       v
      IndexDocumentUseCase        RAGQueryUseCase
               |                       |
               v                       v
      DocumentLoaderPort             Retriever
               |                       |
               v                 +-----+-----+
 LoadedDocumentContent           |           |
               |                 v           v
               v           EmbeddingPort VectorStorePort
        TextNormalizer            |           |
               |                  +-----+-----+
               v                        |
          TextChunker                    v
               |                 RetrievalResult
               v                        |
       DocumentChunk[]                  v
               |                 RAGPromptBuilder
               v                        |
        EmbeddingPort                   v
               |                AIInferencePort
               v                        |
       EmbeddedChunk[]             InferenceRouter
               |                    /        \
               v                Ollama      OpenAI
       VectorStorePort                  |
               |                        v
               v                Response Validation
          Vector DB                     |
                                        v
                                RAGResult + Citations
```

---

# 48. The Simplest Mental Model

You can remember RAG using three words:

```text
STORE
  ↓
SEARCH
  ↓
ANSWER
```

---

# 49. STORE

```text
Document
   |
   v
Extract Text
   |
   v
Chunk
   |
   v
Embed
   |
   v
Vector Database
```

This prepares knowledge.

---

# 50. SEARCH

```text
Question
   |
   v
Embed Question
   |
   v
Similarity Search
   |
   v
Retrieve Relevant Chunks
```

This finds evidence.

---

# 51. ANSWER

```text
Question
+
Relevant Chunks
   |
   v
LLM
   |
   v
Grounded Answer
   |
   v
Citations
```

This generates a useful response.

---

# 52. Why We Need All the Extra Architecture

The basic RAG idea is simple:

```text
STORE
SEARCH
ANSWER
```

But a production-oriented backend also needs:

```text
domain contracts

versioning

idempotency

persistence

timeouts

retries

circuit breakers

security

guardrails

logging

metrics

tracing

evaluation

citations

recovery

caching

concurrency control

provider abstraction
```

These additional components turn a simple RAG demo into a maintainable backend capability.

---

# 53. RAG Does Not Train the Model

This distinction is critical.

RAG generally does **not** permanently teach the model.

It does not normally modify the model weights.

Instead:

```text
External Knowledge
      |
      v
Retrieve Relevant Knowledge
      |
      v
Insert Knowledge Into Current Prompt
      |
      v
Generate Answer
```

The knowledge is supplied at **request time**.

Therefore:

```text
RAG
!=
model training

RAG
!=
fine-tuning

RAG
!=
permanently teaching the LLM
```

RAG is primarily:

```text
retrieval
+
context construction
+
generation
```

around an existing LLM.

---

# 54. A Complete Example From Upload to Answer

Imagine the future API accepts:

```text
Employee-Handbook.pdf
```

## Step 1 — Represent the document

```text
Document
```

stores its domain identity and lifecycle information.

## Step 2 — Load content

```text
DocumentLoaderPort
```

extracts text.

Output:

```text
LoadedDocumentContent
```

## Step 3 — Split text

```text
TextChunker
```

produces:

```text
DocumentChunk[]
```

## Step 4 — Generate embeddings

```text
EmbeddingPort
```

converts the chunks into vectors.

Output:

```text
EmbeddedChunk[]
```

## Step 5 — Index them

```text
VectorStorePort
```

writes them to the vector database.

The knowledge base is now searchable.

---

# 55. User Asks a Question

User:

> How many annual leave days do employees receive?

Create:

```text
RetrievalQuery
```

Then:

```text
RetrievalQuery
      |
      v
EmbeddingPort
      |
      v
Query Vector
      |
      v
VectorStorePort
      |
      v
RetrievalResult
```

The result contains:

```text
RetrievedChunk[]
```

For example:

```text
RetrievedChunk

document:
Employee Handbook

page:
37

text:
"Employees receive 20 annual leave days."

score:
0.91
```

---

# 56. Build the Final RAG Prompt

The future prompt builder may conceptually create:

```text
SYSTEM:

Answer the user's question using the retrieved context.
Do not invent information that is not supported by the context.

QUESTION:

How many annual leave days do employees receive?

RETRIEVED CONTEXT:

[Employee Handbook — page 37]

Employees receive 20 annual leave days each calendar year.

OUTPUT:

Provide a concise answer and cite the source.
```

Then:

```text
RAGPromptBuilder
      |
      v
AIInferencePort
      |
      v
InferenceRouter
      |
      +---- Ollama
      |
      +---- OpenAI
      |
      v
Generated Answer
```

---

# 57. Build the Final RAG Result

The application validates the generated answer and attaches provenance.

Conceptually:

```text
RAGResult
```

Example:

```json
{
  "status": "SUCCESS",
  "answer": "Employees receive 20 annual leave days each calendar year.",
  "citations": [
    {
      "document_id": "employee-handbook",
      "chunk_id": "chunk-37",
      "title": "Employee Handbook",
      "page_number": 37
    }
  ]
}
```

That is the complete RAG concept.

---

# 58. What Happens When the Knowledge Base Has No Answer?

Question:

> What is the company policy for employees travelling to Mars?

Retrieval:

```text
No relevant chunk above threshold
```

The workflow should not do:

```text
Ask LLM from general memory anyway
```

Instead:

```text
RAGResultStatus.NO_CONTEXT
```

Conceptually:

```json
{
  "status": "NO_CONTEXT",
  "answer": "The indexed knowledge base does not contain enough information to answer this question.",
  "citations": []
}
```

This is an important enterprise behavior because it reduces unsupported answers.

---

# 59. RAG-00 Model Relationships

The models can be grouped by stage.

## Document lifecycle

```text
Document
DocumentStatus
LoadedDocumentContent
```

## Indexing

```text
DocumentChunk
EmbeddedChunk
```

## Retrieval

```text
RetrievalQuery
RetrievedChunk
RetrievalResult
```

## Response

```text
Citation
RAGResult
RAGResultStatus
```

## Infrastructure boundaries

```text
DocumentLoaderPort
DocumentRepositoryPort
VectorStorePort
```

---

# 60. Model Relationship Diagram

```text
Document
   |
   +--> DocumentStatus
   |
   v
DocumentLoaderPort
   |
   v
LoadedDocumentContent
   |
   v
DocumentChunk
   |
   v
EmbeddingPort
   |
   v
EmbeddedChunk
   |
   v
VectorStorePort
   |
   v
Vector Database


Question
   |
   v
RetrievalQuery
   |
   v
EmbeddingPort
   |
   v
VectorStorePort
   |
   v
RetrievalResult
   |
   +--> RetrievedChunk
   +--> RetrievedChunk
   |
   v
RAGPromptBuilder
   |
   v
AIInferencePort
   |
   v
Generated Answer
   |
   v
Citation[]
   |
   v
RAGResult
   |
   +--> RAGResultStatus
```

---

# 61. Why This Architecture Helps Future AI Feature Development

The objective is not to build one hard-coded chatbot.

The goal is to build reusable capabilities.

For example:

```text
DocumentLoaderPort
```

can support:

```text
document chat
policy assistant
contract assistant
support knowledge base
technical-document assistant
```

`EmbeddingPort` can support:

```text
RAG
semantic search
duplicate detection
similarity matching
recommendations
```

`VectorStorePort` can support:

```text
semantic retrieval
knowledge search
future filtered retrieval
hybrid search infrastructure
```

`AIInferencePort` already supports reusable generation.

This means new AI features can be composed from shared infrastructure rather than rewritten from scratch.

---

# 62. Future AI Feature Composition

A future feature could look like:

```text
Customer Support AI
      |
      +--> RAG knowledge search
      |
      +--> AIInferencePort
      |
      +--> citations
```

Another:

```text
Engineering Assistant
      |
      +--> RAG architecture docs
      |
      +--> RAG runbooks
      |
      +--> AIInferencePort
```

Another:

```text
Policy Assistant
      |
      +--> RAG HR policies
      |
      +--> AIInferencePort
```

All can reuse the same generic RAG foundation.

---

# 63. What Has Actually Been Completed at RAG-00?

Completed:

```text
RAG architecture definition

domain vocabulary

document lifecycle concepts

retrieval contracts

citation contract

RAG result contract

document-loader abstraction

document-repository abstraction

vector-store abstraction

generation reuse decision

embedding ownership decision

no-context behavior decision

persistence ownership decision
```

Not completed yet:

```text
actual ingestion

actual text extraction

actual chunking

actual vector creation

actual vector database

actual retrieval

actual RAG prompt

actual query endpoint

actual answer generation

actual citation output
```

This distinction is important.

RAG-00 created the **foundation**, not the full feature.

---

# 64. Recommended Learning Sequence From Here

As implementation continues, learn the concepts in this order:

```text
1. RAG fundamentals

2. Document lifecycle

3. Text extraction

4. Chunking

5. Embeddings

6. Vector databases

7. Similarity search

8. Retrieval

9. RAG prompt construction

10. Grounded generation

11. Citations

12. No-context handling

13. Evaluation

14. Security

15. Observability

16. Reliability

17. Caching

18. Scaling

19. Multi-tenant RAG

20. OdinSync integration
```

This allows each Codex task to also become a learning milestone.

---

# 65. Key Terms to Remember

## LLM

The model that generates text.

## Embedding

A numerical vector representation of text semantics.

## Vector

A list of numbers representing the embedding.

## Chunk

A small piece of a larger document.

## Vector Database

A database optimized for storing vectors and searching by similarity.

## Retrieval

Finding the most relevant knowledge chunks for a question.

## RAG Context

The retrieved information supplied to the LLM.

## Citation

Information identifying the source used for an answer.

## Grounded Answer

An answer based on retrieved evidence rather than unrestricted model knowledge.

## No Context

A valid result indicating that the knowledge base does not contain sufficient evidence.

## Ingestion

Processing documents and preparing them for retrieval.

## Indexing

Storing searchable vector representations of document chunks.

---

# 66. Final Mental Model

The entire system can be reduced to:

```text
                 KNOWLEDGE PREPARATION

Document
   |
   v
Chunk
   |
   v
Embedding
   |
   v
Vector Database


                     QUESTION

User Question
     |
     v
Embedding
     |
     v
Similarity Search
     |
     v
Relevant Chunks
     |
     v
RAG Prompt
     |
     v
Existing LLM Infrastructure
     |
     v
Grounded Answer
     |
     v
Citations
```

Or even more simply:

```text
STORE
  ↓
SEARCH
  ↓
ANSWER
```

---

# 67. Final Takeaway

RAG extends an LLM with external knowledge **without permanently retraining the model**.

It works by:

```text
1. preparing external knowledge;

2. retrieving the most relevant evidence for a question;

3. placing that evidence into the model's current context;

4. generating an answer using the evidence;

5. preserving the sources used for the answer.
```

The simple RAG concept is:

```text
Document
-> Chunk
-> Embed
-> Store

Question
-> Embed
-> Search
-> Retrieve

Question + Retrieved Context
-> LLM
-> Answer + Citations
```

The additional work being built in `ai-engineer-foundation`—ports, domain models, provider abstraction, versioning, persistence, guardrails, observability, security, reliability, caching, recovery, and evaluation—is what turns this simple workflow into a maintainable, production-oriented AI backend.

Most importantly:

> **RAG does not train the model or teach it permanently. It retrieves external knowledge at request time and supplies that knowledge as context for generation.**

That distinction is fundamental to understanding the architecture and the implementation tasks that follow RAG-00.
