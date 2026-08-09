# Retrieval Score Threshold Semantics in RAG

This note explains the `RAG-01A` correction to `minimum_score`.

It is meant for future implementation work and for learning how vector retrieval should be designed in a backend application.

## 1. Why This Change Was Needed

During `RAG-01`, the project introduced:

```python
minimum_score: float = 0.3
```

The first implementation validated it conceptually like this:

```python
if not 0 <= minimum_score <= 1:
    raise ValueError(...)
```

That looked reasonable at first, but it accidentally encoded a hidden assumption:

```text
all retrieval relevance scores = normalized values between 0 and 1
```

The architecture had not established that contract.

No vector-store adapter existed yet.

No Qdrant retrieval behavior existed yet.

No retriever policy existed yet.

So `0..1` was not a known domain invariant. It was an assumption about future infrastructure.

## 2. What `minimum_score` Means

`minimum_score` is a configured retrieval threshold.

Conceptually:

```text
Question
   |
   v
Vector Search
   |
   +--> Result A score = ...
   +--> Result B score = ...
   +--> Result C score = ...
```

The retrieval layer may use the configured threshold to decide which results are sufficiently relevant.

Conceptually:

```text
retrieve candidates
then
keep only candidates satisfying the active retrieval policy
```

The important detail is that the configuration layer stores the threshold. It does not yet define how that threshold is interpreted.

Comparison direction is also not globally defined yet. Some retrieval APIs expose similarity-like values, where higher may be better. Others expose distance-like values, where lower may be better.

## 3. What Is a Retrieval Score?

RAG uses embeddings to compare meaning.

Documents are split into chunks, and chunks are converted into vectors:

```text
Document Chunk
      |
      v
Embedding
      |
      v
Vector
```

The user's question is also converted into a vector:

```text
Question
      |
      v
Embedding
      |
      v
Vector
```

The vector store compares these mathematical representations.

The result of that comparison may be represented as:

```text
similarity score
```

or:

```text
distance
```

depending on the metric and provider API.

That number is useful only when the retrieval policy defines what it means.

## 4. Similarity vs Distance

### Similarity

Conceptually:

```text
higher value may mean more similar
```

That depends on the selected metric and how the provider exposes the result.

### Distance

Conceptually:

```text
lower value may mean closer / more similar
```

Small distance means vectors are close together in vector space.

The architectural point:

```text
one generic field named score
does not automatically imply
0..1 semantics
```

## 5. Why `0..1` Is Not a Safe Generic Assumption

Different vector metrics can have different numeric behavior.

Examples:

- cosine similarity
- dot product
- Euclidean distance
- Manhattan distance

Different metrics:

- can have different ranges
- may have different directionality
- may expose distance or similarity differently
- may not be safely comparable across embedding/index configurations

Therefore this is too restrictive for a generic RAG domain invariant:

```text
0 <= score <= 1
```

That may be correct for one future normalized relevance policy, but it is not automatically correct for all vector-store implementations.

## 6. Why This Matters for Qdrant

Qdrant will eventually sit behind the generic vector-store boundary:

```text
VectorStorePort
      |
      v
Qdrant adapter
      |
      v
Qdrant
```

Qdrant will perform vector search.

But the application should not assume Qdrant-native retrieval semantics before the adapter and retrieval policy exist.

The architecture should remain:

```text
Qdrant-specific behavior
        |
        v
Qdrant adapter / retrieval policy
        |
        v
application-owned retrieval contract
```

not:

```text
Qdrant assumptions
        |
        v
global RAG configuration
```

This keeps generic RAG configuration independent from a specific vector database or distance metric.

## 7. Why Configuration Should Remain Generic

`RAGSettings` stores configuration.

It should enforce known invariants, such as:

- chunk size must be positive
- chunk overlap cannot be negative
- timeouts must be positive
- `minimum_score` must be a valid finite number

It should not prematurely define vector-store score semantics.

The separation is:

```text
RAGSettings
    |
    | minimum_score
    v
Retriever
    |
    | interprets threshold according
    | to defined retrieval semantics
    v
VectorStorePort
    |
    v
Qdrant Adapter
```

So:

```text
minimum_score = configured retrieval threshold
```

but:

```text
interpretation = retriever + vector-store adapter + retrieval policy
```

## 8. What Changed in RAG-01A

The actual project behavior now is:

```text
minimum_score must be finite
```

The project accepts finite values such as:

```text
-0.5
0
0.3
1
1.5
10
```

The project rejects:

```text
NaN
+Infinity
-Infinity
```

This applies to:

- `RAGSettings.minimum_score`
- `RetrievalQuery.minimum_score`
- `RetrievedChunk.score`

The relevant code lives in:

```text
app/core/config.py
app/application/ai/rag/domain/retrieval.py
```

## 9. Why Reject NaN and Infinity?

A value can technically be a Python `float` but still be unusable for retrieval logic.

Examples:

```python
float("nan")
float("inf")
float("-inf")
```

These values can cause:

- unpredictable comparisons
- invalid query behavior
- serialization problems
- provider API failures
- hard-to-debug configuration issues

The correct generic rule is:

```text
minimum_score must be finite
```

not:

```text
minimum_score must be between 0 and 1
```

## 10. Example Showing the Architectural Problem

Incorrect assumption:

```text
RAG configuration:

minimum_score = 0.75

Assumption:

all providers return normalized 0..1 similarity scores
```

That assumption may work for one implementation.

But another metric or provider could expose scores differently:

```text
Provider / Metric A:

score 0.90
score 0.80
score 0.50

Provider / Metric B:

score 2.1
score 1.4
score 0.7
```

A generic configuration validator should not reject Provider B just because its values can exceed `1`.

This also does not automatically mean:

```text
2.1 is better than 0.7
```

The active retrieval semantics must define that.

## 11. Future Design Decision Still Required

`RAG-01A` does not settle the final retrieval score API.

Future implementation must choose a clear contract.

### Option A: Native Scores

```text
RetrievedChunk.score = provider/vector-store native score
```

Benefits:

- simple
- no artificial normalization

Tradeoff:

- application code must understand metric-specific semantics

### Option B: Application-Normalized Relevance Score

```text
RetrievedChunk.score = application-defined normalized relevance
```

Potential benefit:

- consistent abstraction

Potential drawbacks:

- normalization may lose meaning
- different metrics may not map naturally
- implementation becomes more complex

### Option C: Explicit Metric-Aware Result

Conceptually:

```text
RetrievedChunk
├── raw_score
├── metric
└── interpretation
```

This may make the contract more explicit, but it should be decided when retrieval is implemented.

No option is selected yet.

## 12. When the Decision Should Be Finalized

The score contract should be finalized during:

- `VectorStorePort` implementation
- Qdrant adapter implementation
- Retriever implementation
- dense retrieval baseline

That is when the project will know:

- which distance metric is configured
- how Qdrant exposes the result
- how threshold filtering behaves
- whether higher or lower is better
- whether normalization adds value

## 13. Relationship to `RetrievalQuery`

`RetrievalQuery` can carry:

```text
RetrievalQuery
├── query
├── top_k
└── minimum_score
```

But it should not currently state:

```text
minimum_score must be 0..1
```

unless a future architecture decision explicitly standardizes that contract.

For now, `minimum_score` must only be finite.

## 14. Relationship to `RetrievedChunk.score`

`RetrievedChunk.score` must also avoid undocumented `0..1` assumptions.

Conceptually:

```text
RetrievedChunk
├── text
├── document_id
├── chunk_id
└── score
```

Future work must answer:

- Is score similarity or distance?
- Is higher better?
- Is lower better?
- Is it raw or normalized?
- Which metric produced it?
- Can scores be compared across embedding/index configurations?

For now, `score` must only be finite.

## 15. Why This Is an Architecture Issue

Changing:

```text
0 <= minimum_score <= 1
```

is not merely relaxing validation.

It prevents an early configuration choice from becoming an accidental architecture contract.

This protects future work from coupling generic RAG code to:

- one vector store
- one distance metric
- one score range
- one normalization scheme

## 16. General Engineering Lesson

Principle:

> Do not validate a value more narrowly than the domain contract actually guarantees.

Configuration validation should enforce known invariants, not assumptions about future infrastructure.

In this project, the known invariant is:

```text
minimum_score must be finite
```

The not-yet-known part is:

```text
what that score means for a specific retrieval metric
```

## 17. Before vs After

| Area | Before | After |
| --- | --- | --- |
| `minimum_score` meaning | Implicitly normalized score | Generic configured threshold |
| Valid range | `0..1` | Any finite float |
| NaN | Rejected by finite validation | Rejected |
| Infinity | Rejected by finite validation | Rejected |
| Metric semantics | Implicitly fixed | Deferred |
| Qdrant coupling | Risk of implicit assumptions | Avoided |
| Normalization | Implicitly assumed | Explicitly undecided |
| Ownership | Settings layer | Retrieval policy |

## 18. Beginner Mental Model

```text
Embedding
    |
    v
Vector Search
    |
    v
Raw Retrieval Result
    |
    v
Retrieval Policy
    |
    +--> interpret score/distance
    +--> apply minimum threshold
    +--> apply top-k
    |
    v
RetrievedChunk[]
```

And:

```text
RAGSettings
does not decide
what a Qdrant score mathematically means.
```

## 19. Larger RAG Learning Guide

Related learning/reference documents:

- `docs/architecture/RAG_Complete_Beginner_Guide_and_RAG00_Models.md`
- `docs/architecture/RAG_Complete_Beginner_Guide_and_RAG00_Models_v2.md`
- `docs/architecture/RAG_Fundamentals_and_RAG00_Architecture_Reference.md`

Those guides explain the broader RAG model structure. This document focuses specifically on retrieval score threshold semantics.
