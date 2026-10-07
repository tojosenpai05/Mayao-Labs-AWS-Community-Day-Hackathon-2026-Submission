# Seven Failure Points When Engineering a Retrieval Augmented Generation System

**Source:** Barnett et al. (2024) — Applied Artificial Intelligence Institute, Deakin University  
**Published:** 3rd International Conference on AI Engineering (SE4AI), April 2024, Lisbon  
**URL:** https://arxiv.org/html/2401.05856v1  
**Scope:** International / Technical  
**Type:** Peer-reviewed conference paper

---

## Core Argument

RAG systems are increasingly used to give AI agents access to domain-specific knowledge — including government documents — but they suffer from a predictable set of failure points that engineers must design around. The key insight: **robustness in RAG is evolved, not designed in from the start**, and validation only becomes feasible during operation.

---

## The 7 Failure Points

| # | Failure Point | Description |
|---|---|---|
| FP1 | **Missing Content** | Question cannot be answered from available documents; system may hallucinate an answer anyway |
| FP2 | **Missed Top Ranked Documents** | Answer exists in the corpus but didn't rank high enough to be retrieved |
| FP3 | **Not in Context** | Relevant document was retrieved but got dropped during consolidation/compression before reaching the LLM |
| FP4 | **Not Extracted** | Answer was in the context but LLM failed to extract it due to noise or contradicting information |
| FP5 | **Wrong Format** | LLM ignored formatting instructions (e.g., should return a table, returned plain text) |
| FP6 | **Incorrect Specificity** | Answer is too general or too specific for the user's actual need |
| FP7 | **Incomplete** | Answer is partially correct but misses information that was available in context |

---

## Key Pain Points Highlighted

- **Chunking quality matters enormously** — if chunks are too small, questions can't be answered; too large, generated noise pollutes the answer
- **Domain-specific questions need domain-tuned embeddings** — generic embeddings underperform on specialized government/legal language
- **Document formats are a barrier** — PDFs, scanned documents, tables, and figures require preprocessing pipelines before they can be indexed
- **RAG systems are hard to test upfront** — no test data exists at build time; it must be generated synthetically or discovered through live piloting
- **LLM token limits cap context window** — when too many documents are retrieved, a consolidation strategy is needed, introducing another failure point
- **Ambiguous queries degrade retrieval** — government staff often don't know how to phrase their query precisely

---

## Case Studies Referenced

1. **Cognitive Reviewer** (Deakin University) — RAG for scientific literature review; revealed chunking and ranking challenges
2. **AI Tutor** (Deakin University, 200 students) — RAG over learning content including PDFs and transcribed videos; revealed query rewriting and context window issues
3. **BioASQ Biomedical QA** — Large-scale (15,000 docs, 1,000 questions); revealed ranking failure and hallucination when answers are absent from corpus

---

## Relevance to Problem Statement

For government document Q&A, this paper provides a technical blueprint of exactly what can go wrong. The failure points (FP1–FP7) are directly applicable when building a system to query policies, SOPs, and circulars. Government documents are often:
- Poorly formatted (scanned PDFs, old Word docs)
- Full of legal/bureaucratic language requiring domain-specific embeddings
- Structured in overlapping and sometimes conflicting versions

Designing against these failure points from day one is critical for a credible demo.

---

*Content was paraphrased for compliance with licensing restrictions.*
