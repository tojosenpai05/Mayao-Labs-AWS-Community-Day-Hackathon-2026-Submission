# WAWASAN — Full Pipeline Reference
## AWS Student Community Day Kuching 2026 · Mayao Labs

> **WAWASAN** — Wawasan Agensi Wakil Awam Sarawak dalam Aksesibiliti Naskah
> The internal Dayang — built for Sarawak civil servants, not citizens.

---

## Status: what is built and what is planned

| | Built (hackathon MVP, `demo/`) | Production target (AWS) |
|---|---|---|
| **Runs on** | Any machine with Python 3.10+, standard library only | S3 · Lambda · DynamoDB · Bedrock |
| **Corpus** | 15 fictional circulars + 3 knowledge-interview transcripts | One pilot agency's real documents |
| **Retrieval** | BM25, in-process | BM25 in Lambda; hybrid BM25 + dense once the corpus grows |
| **LLM** | Optional: Bedrock or Groq; extractive fallback when absent | Bedrock, Claude Haiku 4.5 |
| **Language** | English | Bahasa Malaysia + English |
| **Cost** | $0 | ~$1 for a demo; ~$20–35/month for a pilot (see below) |

**Design principle:** build the pipeline logic locally, prove it works, then move each component to AWS. The four functions in `demo/app.py` that touch storage or the model (`load_corpus`, `load_rules`, `call_llm`, `log_audit`) are the only things that change.

---

## Pipeline overview

WAWASAN combines four research-backed solutions:

| Layer | Solution | Contribution |
|---|---|---|
| Core retrieval | SOL-01 RAG Document Q&A | Natural language → cited answer |
| Accuracy safeguard | SOL-05 Hybrid RAG + Rule-based | Routes facts to a rule engine; the LLM never guesses them |
| Governance & trust | SOL-06 GenAI Policy Navigator | Closed corpus, citations, refusal, version awareness, audit log |
| Institutional memory | SOL-03 Institutional Memory AI | Captured interviews with retiring officers become searchable documents |

```
Query → Router ─┬─ FACTUAL ──────→ Rule engine ───────────────────────────┬→ Answer + citation → Audit log
                └─ INTERPRETIVE ─→ BM25 retrieval → Confidence gate → LLM ┘
```

---

## Step-by-step pipeline

### Step 1 — Document sources

| Type | Examples | In the demo | Layer |
|---|---|---|---|
| Formal policy documents | Policies, SOPs, circulars | 15 fictional circulars (`SC-*.md`) | SOL-01 |
| Knowledge interviews | Retiring officers explaining *why* decisions were made | 3 fictional transcripts (`KI-*.md`) | SOL-03 |
| Structured policy facts | Grade entitlements, procurement limits | Rule table in `app.py` | SOL-05 |
| Scanned legacy records, meeting minutes | Old PDFs, printed circulars | Not in the demo | SOL-01 |

Each document carries metadata: id, type, title, owning department, date, and `supersedes` / `superseded_by` links.

### Step 2 — Document processing

| Demo | AWS |
|---|---|
| None needed: documents are already text (Markdown with metadata) | **Amazon Textract** for PDFs and scans · **Amazon Transcribe** for recorded knowledge interviews (SOL-03 capture workflow) |

### Step 3 — Retrieval

| Demo | AWS |
|---|---|
| BM25 (k1 = 1.5, b = 0.75) over title + body, computed in-process | Same code inside **Lambda** for the pilot. Add dense embeddings (e.g. Titan Text Embeddings v2) for hybrid retrieval once the corpus outgrows keyword search |

**Superseded documents are still retrieved but never used as the answer.** The UI shows them struck through, with a pointer to the circular that replaced them.

**Why no Amazon OpenSearch Serverless (yet):** at pilot scale, BM25 in Lambda memory is enough. OpenSearch Serverless bills compute continuously (~$0.48/hr minimum, roughly $350/month) whether or not it is queried. It was ~93% of the original cost estimate. Add it only when the corpus is too large to index in memory. If it is ever used for a demo, delete the collection afterwards.

### Step 4 — Query router (SOL-05)

| Rule | Route |
|---|---|
| Question contains *why* | INTERPRETIVE, since a lookup table cannot explain a rationale |
| Contains a structured-fact marker (*grade, entitlement, limit, rate, amount, maximum, how many, how much*) | FACTUAL |
| Otherwise | INTERPRETIVE |

A FACTUAL question with no matching rule falls through to retrieval. Demo: regex in `app.py`. AWS: the same code in Lambda.

### Step 5 — Rule engine (SOL-05)

Exact answers for structured facts, each pointing at its source circular. The LLM is never involved.

| Example | Answer | Source |
|---|---|---|
| Annual leave, Grade 41 | 25 days | SC-4-2022 |
| Direct procurement limit | RM 50,000 (previously RM 20,000 under SC-3-2022) | SC-7-2024 |

| Demo | AWS |
|---|---|
| Python dict | **DynamoDB** table (always-free tier) |

### Step 6 — Confidence gate (SOL-06)

The confidence score is the **share of the question's key terms found in the top non-superseded source**. If it is below **0.60**, the system replies *"Information not available in the system"* **before any LLM call is made**.

Example: *"What is the work-from-home policy?"* matches only *work* (in the overtime circular). That is 1 of 3 terms, so confidence is 0.33 and the question is refused.

This is deliberately simple and explainable: a judge or an officer can see exactly which terms were missing. With hybrid retrieval in production, embedding similarity can be added as a second signal.

### Step 7 — Answer generation

| Demo | AWS |
|---|---|
| `LLM_PROVIDER=bedrock` → Bedrock via the AWS CLI · or `GROQ_API_KEY` → Groq free tier · or neither → **extractive fallback**: quote the best-matching passage of the cited source | **Amazon Bedrock**, Claude Haiku 4.5 ($1.10 / $5.50 per million input/output tokens) |

The model is instructed to answer only from the cited source, and to return the refusal message if the source does not answer the question.

**Data residency caveat:** the demo defaults to the `global.` Bedrock inference profile, which may process requests in any commercial region. A deployment that must keep data in-region needs an in-region model or a geography-specific profile, confirmed per model.

**All five demo scenarios work with no LLM.** The deterministic paths (rule engine, refusal, supersession) never call one. The retrieval answers fall back to quoting the source.

### Step 8 — Audit log (SOL-06)

Every query is logged: user, timestamp, query, route, answer, source document, confidence.

| Demo | AWS |
|---|---|
| SQLite (`demo/audit.db`), shown live in the UI | **DynamoDB** + CloudWatch |

### Step 9 — Frontend

| Demo | AWS |
|---|---|
| Single page served by the Python server. It visualises each pipeline stage: route taken, retrieval scores, confidence against threshold, LLM used or skipped | Same page served from the Lambda Function URL (or S3 + CloudFront) |

### Not in the MVP

- **Auth / role-based access:** Amazon Cognito, so classified circulars are only visible to cleared roles
- **Content filtering:** Amazon Bedrock Guardrails

---

## Cost summary

### Running the demo on AWS (~300 queries)

| Component | Cost |
|---|---|
| Bedrock Haiku 4.5 (~1,550 input + ~250 output tokens/query ≈ $0.003) | ~$0.90 |
| Lambda, DynamoDB, S3, Function URL | $0 (free tier) |
| **Total** | **~$1** |

### Monthly pilot (one agency, 10,000 queries/month)

| Component | Cost |
|---|---|
| Bedrock Haiku 4.5 | up to ~$31 if every query reached the model; less in practice, since rule-engine and refused queries make no LLM call |
| Lambda (10,000 invocations) | $0 (free tier) |
| DynamoDB on-demand, S3 | < $1 |
| CloudWatch logs | ~$1 |
| **Total** | **~$20–35/month** |

Nothing in this stack bills while idle, so forgetting to tear it down costs nothing. Token counts per query are estimates; prices are as of October 2026.

---

## Alternatives considered

An **Azure for Students VPS running Ollama (Qwen3 7B) + Qdrant + Open WebUI** was evaluated and rejected for the hackathon:
- ~5 GB model download on conference wifi, before any building could start
- CPU-only inference at ~5–15 s per query, which would mean watching a spinner on stage
- Open WebUI's generic chat interface hides the pipeline, which is our main differentiator

Self-hosted open-source stacks remain relevant for agencies that cannot send data to any cloud. See [`research/solutions/OPEN-SOURCE-ALTERNATIVES.md`](research/solutions/OPEN-SOURCE-ALTERNATIVES.md).

---

## The pitch line

> *"Every policy fact WAWASAN gives you comes from a rule table or a cited circular, never from a model's guess. If the answer isn't in the corpus, it says so. And when a senior officer retires, the reasons behind their decisions stay searchable. The demo runs on the Python standard library; in production it runs on S3, Lambda, DynamoDB and Bedrock for about a dollar a demo."*

---

## Roadmap

### Phase 1 — Hackathon MVP (built)
- Router, rule engine, BM25 retrieval, confidence gate, version supersession, audit log
- Knowledge-interview transcripts indexed alongside circulars (SOL-03 output)
- Pipeline-visualising UI; optional Bedrock answer generation; English only

### Phase 2 — Pilot and production on AWS (3–12 months)
- Deploy on S3 · Lambda · DynamoDB · Bedrock
- Hybrid retrieval (BM25 + dense embeddings)
- Bahasa Malaysia + English
- Rule-table admin interface with alerts when a source circular changes
- Knowledge capture workflow (SOL-03): Transcribe for exit interviews, with AI-guided follow-up questions
- Cognito role-based access, Bedrock Guardrails
- Offline cache for low-connectivity district offices

### Phase 3 — Ecosystem (12–24 months)
- Knowledge graph (Amazon Neptune) for relationship queries and change propagation, kept off the per-query hot path
- Cross-agency federated search (no data movement)
- Policy change alerts ("Circular X has been updated; these 4 SOPs reference it")
- Integration with Dayang (Sarawak's citizen-facing AI)
- SAIC oversight dashboard

---

*Sources: Amazon Bedrock model card for Claude Haiku 4.5 (inference profile IDs); Bedrock pricing as of October 2026; AWS free-tier terms. Earlier VPS and open-source pricing research is retained in `research/solutions/OPEN-SOURCE-ALTERNATIVES.md`.*
