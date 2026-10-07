# Solution 5: Hybrid RAG + Rule-Based Reasoning for Policy Documents

**Pain Point Addressed:** No single source of truth + Version confusion + AI hallucination on policy docs  
**Type:** Advanced RAG Architecture  
**Maturity:** Research — 2025/2026 papers, emerging production use

---

## What It Is

Standard vector-based RAG uses semantic similarity to retrieve documents — it finds chunks that are *semantically close* to the query. This works well for general knowledge but fails for policy and regulatory documents where **precision, not just relevance, is required**. A hybrid approach combines:

1. **Dense vector retrieval** (semantic similarity — finds what's contextually related)
2. **Sparse BM25 retrieval** (keyword matching — finds exact terms, circular numbers, dates)
3. **Rule-based reasoning** (deterministic logic for structured policy requirements — never hallucinate on "what is the procurement limit?")

---

## Key Research

### Hybrid RAG + Rule-Based Reasoning for Technical Documents (Frontiers in AI, 2026)
**Source:** [frontiersin.org/journals/artificial-intelligence](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1922508/full)

Current RAG systems relying solely on dense vector embeddings **cannot offer the deterministic accuracy** that policy and regulatory environments require. The paper proposes a hybrid framework where:
- Dense retrieval handles **intent-based queries** ("what is the general process for staff promotion?")
- Rule-based reasoning handles **fact-based queries** ("what is the maximum leave entitlement for Grade 41?") — these are deterministic and must never be guessed

Key finding: pure vector RAG applied to technical/policy documents produces **confident but wrong answers** on structured factual queries. The hybrid approach eliminates this class of errors by routing deterministic questions through a rule engine rather than an LLM.

### RAG for Policy QA — AGORA Corpus (arXiv, 2026)
**Source:** [arxiv.org/html/2603.24580](https://arxiv.org/html/2603.24580)

Study on 947 AI policy documents. Finding: improvements to individual RAG components (better retrieval, better reranking) **do not consistently improve end-to-end answer quality**. Specifically, stronger retrieval sometimes produces *more* confident hallucinations when relevant documents are absent from the corpus — the model becomes more assertive, not less wrong.

Key implication: for government policy use cases, the system must have explicit "out-of-corpus" detection — if the answer is not in the document store, say so clearly rather than generating a plausible-sounding fabrication.

### Retrieval Improvements Do Not Guarantee Better Answers (arXiv, 2025)
**Source:** [arxiv.org/html/2603.24580v1](https://arxiv.org/html/2603.24580v1)

Domain-specific fine-tuning of retrievers with ColBERT + contrastive learning improves retrieval metrics. Advanced RAG (DPO-aligned generator) achieves faithfulness of **0.797 vs 0.347 baseline**. But the gap between retrieval quality and answer quality persists — retrieval is necessary but not sufficient.

---

## Architecture for Government Policy Q&A

```
User Query
    ↓
Query Classification
    ├─ Factual/Deterministic? → Rule Engine
    │       (e.g., "What is the deadline for X?" → parse structured policy table)
    │
    └─ Conceptual/Interpretive? → Hybrid RAG
            ├─ BM25 (keyword) retrieval
            ├─ FAISS (dense vector) retrieval
            ├─ Reranker (cross-encoder)
            └─ LLM answer generation (with citation)
                    ↓
            Confidence scoring
            ├─ High confidence → Return answer + citations
            └─ Low confidence → "I don't have current information on this"
```

---

## AWS Implementation Stack

```
Documents → Amazon Textract → chunking pipeline
    → Amazon Bedrock Embeddings (Titan v2)
    → Amazon OpenSearch (BM25 + KNN vector index)
    → Amazon Bedrock (Claude 3 Haiku / Sonnet for answer generation)
    → AWS Lambda (query classification + routing logic)
    → DynamoDB (structured policy tables for rule-based facts)
    → CloudWatch (confidence score logging)
```

---

## Why This Matters for Government Documents

Government circulars and SOPs contain two types of information:
1. **Structured facts** — salary grades, leave days, procurement thresholds, deadlines. These must never be wrong.
2. **Interpretive guidance** — policy intent, context, reasoning. These can be synthesized by an LLM.

A single-mode RAG system handles both identically and fails on type 1. The hybrid approach correctly routes each query type to the appropriate engine.

---

## Hackathon Note

For a 4-hour build, implement the pure RAG path first (most of the work). Add query classification as a lightweight Lambda function that checks if the query contains structured data keywords (numbers, dates, codes). This is a 1-hour addition that makes the demo significantly more impressive and resilient.

---

*Content paraphrased for compliance with licensing restrictions.*
