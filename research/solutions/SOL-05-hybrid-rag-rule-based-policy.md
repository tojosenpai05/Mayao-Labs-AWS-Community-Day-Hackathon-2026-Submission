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

---

## Advantages

### ✅ Eliminates the most dangerous failure mode in government AI
Hallucinating a salary grade or a procurement limit is not just wrong — it's a compliance failure. The hybrid approach routes all deterministic, structured-fact queries through a rule engine that cannot hallucinate. This is the critical trust differentiator for a government audience.

### ✅ "Side-by-side" demo is the most technically convincing moment in a hackathon
Show pure RAG answering "what is the leave entitlement for Grade 41?" with a confident but wrong answer. Then show hybrid routing giving the correct answer from the rule table. That single demonstration is more persuasive than 10 minutes of explanation.

### ✅ Best research backing of any individual solution
Three 2025–2026 papers specifically on policy document retrieval (Frontiers in AI, AGORA corpus, arXiv faithfulness study) all support this approach. The evidence base is current and domain-specific.

### ✅ Directly addresses Sarawak SOPs and circulars
Sarawak government documents are full of structured facts: Grade-based entitlements, procurement limits by department level, deadlines, approval authorities. Every one of these is a query where pure RAG will eventually fail and hybrid routing will always get right.

### ✅ Modular — can be added to any RAG core
The query classification layer is a lightweight Lambda function sitting in front of the RAG pipeline. It doesn't require rebuilding the RAG system. Any team that has already built SOL-01 can add SOL-05 in roughly an hour.

### ✅ Confidence scoring makes the system self-aware
The hybrid pipeline produces confidence scores alongside every RAG answer. Low confidence triggers an "I don't have reliable information on this" response rather than a guess. This is not default RAG behaviour — it requires explicit engineering and is a meaningful differentiator.

---

## Disadvantages

### ❌ Rule tables require manual curation and ongoing maintenance
Someone must extract all structured policy facts from government documents and populate the rule tables in DynamoDB. This is manual work upfront and must be repeated every time a policy changes. If the rule tables go stale, the system produces confidently wrong deterministic answers — worse than a hallucination because it appears authoritative.

### ❌ Query classification is imperfect
The Lambda classifier decides whether a query is "factual" or "interpretive." Edge cases exist — "what is the general process for approving a procurement above the threshold?" is partly factual, partly interpretive. Misclassification sends a factual query to RAG (where it may hallucinate) or an interpretive query to the rule engine (where it gets no answer). The classifier needs testing and iteration.

### ❌ Adds ~1–2 hours to a hackathon build
The RAG core is straightforward. The classification layer and rule tables add significant scoped time. A team that underestimates this ends up with an incomplete hybrid and a worse demo than a clean SOL-01 build.

### ❌ DynamoDB rule tables don't scale gracefully to thousands of policy facts
A pilot with 50 structured facts is manageable. A production system covering every Sarawak state agency's structured policy facts across all departments runs to thousands of entries. Managing this at scale requires a proper admin interface and governance workflow that is well beyond a hackathon scope.

### ❌ Doesn't solve the silo or institutional memory problems
Like SOL-01, this solution improves retrieval quality but doesn't address why documents are fragmented across systems, or why knowledge held by experienced staff isn't captured anywhere. It's a better search engine, not a knowledge management system.
