# WAWASAN — Sarawak Government Knowledge Intelligence System
## Product Design Document · AWS Student Community Day Kuching 2026

> **WAWASAN** — *Wawasan Agensi Wakil Awam Sarawak dalam Aksesibiliti Naskah*
> (Sarawak Government Agency Vision for Accessible Document Intelligence)

---

## The Gap That Exists Today

Sarawak has **Dayang** — an AI assistant for citizens to navigate public-facing government services.

Sarawak does **not** have an equivalent for the civil servants *inside* those agencies.

A Sarawak state officer trying to find Circular 3/2022 on procurement limits, the latest SOP for staff leave, or why a particular policy decision was made five years ago — has no intelligent tool. They search through shared drives, email other departments, call the person who "knows where things are", and hope.

This is the exact gap WAWASAN fills. It is the **internal Dayang** — built for civil servants, not citizens.

---

## What WAWASAN Is

WAWASAN is a **closed-corpus, hybrid AI knowledge assistant** for Sarawak state government agencies. It combines four research-backed solution approaches into a single product that has not yet been deployed anywhere in Malaysia or Sarawak.

**In plain language:** Civil servants ask questions in natural language (English in the current MVP; Bahasa Malaysia is on the roadmap). WAWASAN searches across all connected agency document stores, finds the most relevant and current policy/SOP/circular, and returns a cited, trustworthy answer — with the source document, version date, and owning department clearly shown.

If it doesn't know the answer, it says so. It never guesses on policy facts.

---

## The Four-Solution Combination

| Component | Source Solution | What It Contributes |
|---|---|---|
| **Core retrieval engine** | SOL-01 (RAG Document Q&A) | Natural language → cited answer over any document corpus |
| **Accuracy safeguard** | SOL-05 (Hybrid RAG + Rule-based) | Routes factual queries to deterministic engine; no hallucination on structured policy facts |
| **Governance & trust layer** | SOL-06 (GenAI Policy Navigator) | Closed corpus, audit log, role-based access, "I don't know" detection, version awareness |
| **Memory preservation layer** | SOL-03 (Institutional Memory AI) | Captures tacit knowledge from retiring staff; preserves the *why* behind decisions |

What is **deliberately excluded** from the MVP:
- SOL-02 (Amazon Q Business) — too generic, positions the product as configuration not engineering
- SOL-04 (Knowledge Graph) — too complex for MVP; included as the **roadmap Phase 3** architecture

**Why the knowledge graph isn't in the live query path:** graph traversal (Neptune, multi-hop) is inherently slower than a vector ANN lookup — tens of ms for vector search vs. 100ms–low seconds for multi-hop graph queries, depending on hop count and fan-out. LLM generation time (1-3s+) dominates total latency either way, so this isn't the top adoption risk by itself — but putting live KG traversal on every query's hot path adds latency and engineering complexity the 4-hour build can't absorb. The KG is pitched as Phase 3 architecture, not demoed as a live dependency.

---

## How the Combination Works

```
CIVIL SERVANT ASKS A QUESTION
         │
         ▼
┌─────────────────────────────┐
│   WAWASAN Query Router      │  ← SOL-05 contribution
│                             │
│  Is this a structured fact? │
│  (number, date, code, grade)│
└──────┬───────────────┬──────┘
       │ YES           │ NO
       ▼               ▼
┌────────────┐  ┌──────────────────────────────┐
│ Rule Engine│  │  Hybrid RAG Pipeline          │  ← SOL-01 contribution
│ (DynamoDB  │  │  BM25 keyword retrieval       │
│  tables)   │  │  + confidence gate            │
│            │  │  + Bedrock Claude Haiku 4.5   │
└─────┬──────┘  └──────────────┬───────────────┘
      │                        │
      └───────────┬────────────┘
                  ▼
       ┌─────────────────────┐
       │  Answer + Citation  │  ← SOL-06 contribution
       │  Source doc         │
       │  Version date       │
       │  Owning dept        │
       │  Confidence score   │
       │  OR "I don't know"  │
       └─────────────────────┘
                  │
                  ▼
       ┌─────────────────────┐
       │  Audit Log          │  ← SOL-06 contribution
       │  (DynamoDB)         │
       │  Who asked what     │
       │  When               │
       │  What was returned  │
       └─────────────────────┘
```

The **Institutional Memory layer (SOL-03)** feeds into the document corpus — it's not a separate query path but an enrichment of the knowledge base itself. When a retiring civil servant's knowledge interviews are transcribed and indexed, that tacit knowledge becomes part of what WAWASAN can retrieve.

---

## What Makes This Novel for Sarawak

### 1. No existing equivalent internally
Dayang (citizen-facing) exists. The DDMS (document filing) exists. But **no product combines intelligent retrieval + policy accuracy + institutional memory preservation + governance** in a single internal tool for Sarawak civil servants. This combination is genuinely new.

### 2. Designed to go multilingual (roadmap)
Sarawak's documents span Bahasa Malaysia, English, and community-level records in Iban and other languages. **The MVP is English-only.** The production target uses multilingual embedding models (e.g. Amazon Titan Text Embeddings v2) to accept queries in BM or English and answer in the language of the question. Nothing in the pipeline's design ties it to one language: the router, rule engine and confidence gate are language-agnostic once their keyword lists are localised.

### 3. Version-aware, not just version-storing
The DDMS stores versions. It doesn't *understand* them. WAWASAN tracks temporal relationships between documents — it knows that Circular 7/2024 supersedes Circular 3/2022, and when you ask about the procurement process, it returns the *current* answer, not the most recently uploaded document.

### 4. Built on the Sarawak institutional memory gap
The 2012 UiTM study found Sarawak state agencies had no central records registry and records access was the single weakest practice area. WAWASAN addresses this directly by creating a semantic layer above existing storage — no migration required.

### 5. Aligned with SDEB 2030 but not yet funded by it
The Sarawak Digital Economy Blueprint 2030 explicitly targets 100% online government services and AI-driven public sector. WAWASAN positions itself as the internal enabler that makes that vision functional — civil servants need to find policies fast before they can deliver services fast. This alignment makes it politically viable without being duplicative of existing initiatives.

---

## Advantages

### ✅ Addresses the actual unmet gap
Sarawak has citizen-facing AI (Dayang). It has document storage (DDMS). It has AI policy coordination (SAIC). What it doesn't have is an internal knowledge retrieval tool. WAWASAN fills exactly that gap — no overlap with existing investments.

### ✅ Non-destructive deployment
Works on top of existing document repositories (S3, SharePoint, shared drives). Agencies do not need to migrate, restructure, or replace anything. The barrier to pilot is low.

### ✅ Hallucination-safe on policy facts
The hybrid routing layer (SOL-05) means structured policy facts — salary grades, leave entitlements, procurement thresholds, deadlines — are answered by a deterministic rule engine, not guessed by an LLM. This is the critical trust feature for a government audience.

### ✅ Governance baked in, not bolted on
Every query is logged. Every answer cites its source. Role-based access means a junior officer cannot retrieve classified circulars. The compliance posture is built into the product from day one — directly addressing the Thomson Reuters finding that 1-in-5 agencies using AI have no governance policy.

### ✅ Institutional memory as a competitive moat
By capturing the tacit knowledge of retiring civil servants (transcribed interviews, contextual notes, decision histories), WAWASAN builds a knowledge base that gets *more valuable over time*. Competing tools that only index formal documents will always have shallower institutional memory than WAWASAN.

### ✅ A path to Sarawak's multilingual reality (roadmap)
The MVP is English-only. BM + English is the Phase 2 target, and a multilingual embedding layer would later allow community-level documents in Iban or other Sarawakian languages to be indexed and queried.

### ✅ Aligned with SDEB 2030 and SAIC
The political and budgetary tailwinds are real. SDEB 2030 calls for AI-enabled government services. SAIC coordinates AI adoption. WAWASAN is the product that makes the internal side of that transformation real.

---

## Disadvantages

### ❌ Document quality is the biggest risk
WAWASAN is only as good as the documents fed into it. Sarawak's historical records are inconsistently formatted, partially scanned, and not uniformly structured (UiTM, 2012). A poorly indexed corpus produces confidently wrong answers — exactly what erodes trust in AI tools. **Mitigation:** Build document quality checks into the ingestion pipeline; flag low-confidence documents during indexing.

### ❌ Multilingual support has limits in practice
Multilingual embedding models perform well on BM/English but degrade on low-resource languages like Iban. Community-level records in local languages may not retrieve accurately. **Mitigation:** Start with BM/English corpus only; expand language support incrementally with community-specific fine-tuning.

### ❌ Institutional memory capture requires buy-in from retiring staff
The knowledge interview process (recording retiring officers narrating their work) requires active cooperation and change management effort. Busy or reluctant staff will skip it. **Mitigation:** Position it as legacy preservation ("your knowledge lives on in the system"), not as extra work. Pilot with one willing department first.

### ❌ Rule engine requires manual curation of structured policy tables
The deterministic routing layer works great once the structured fact tables (leave entitlements, procurement limits, etc.) are built — but someone has to build and maintain them. They go stale when policies change. **Mitigation:** Build an admin interface that alerts when a source document has been updated, prompting a rule table review.

### ❌ Rural connectivity limits real-time access
Sarawak's rural-urban digital divide means agencies outside Kuching/Miri may have limited bandwidth. A cloud-native real-time system may perform poorly or be inaccessible in remote district offices. **Mitigation:** Offline mode with cached knowledge snapshots; async sync when connectivity is available.

### ❌ Change management is not a technical problem
Malaysia's history of low DDMS adoption is not a technology failure — it's a culture failure. Even a perfect technical product will fail if civil servants don't trust it or are not trained to use it. **Mitigation:** Co-design rollout with one pilot department; measure time-to-answer improvement; let staff experience the win before scaling.

### ❌ Data sovereignty concerns
Sarawak government documents are sensitive. Routing them through cloud AI services (even AWS) raises data sovereignty questions that some agency heads will have. **Mitigation:** Host storage and compute (S3, Lambda, DynamoDB) in the AWS Asia Pacific (Singapore) region, ap-southeast-1, the closest region to Kuching. For the LLM call, note that Bedrock's *global* cross-region inference profiles may process requests outside the region. Data residency therefore needs an in-region model or a geography-specific inference profile, which should be confirmed per model before any production deployment. Highly sensitive agencies may need a self-hosted model instead (see `research/solutions/OPEN-SOURCE-ALTERNATIVES.md`).

---

## Product Roadmap

### Phase 1 — Hackathon MVP (built: see `demo/`)
- Dependency-free pipeline: query router, deterministic rule engine, BM25 retrieval, confidence gate with refusal, version supersession, audit log
- Captured knowledge-interview transcripts indexed alongside circulars (the *output* of the SOL-03 capture workflow)
- Web UI that visualises each pipeline stage's decision
- Optional answer generation via Amazon Bedrock (Claude Haiku 4.5); every scenario also works without an LLM
- Sample corpus of fictional circulars; English only

### Phase 2 — Pilot and production on AWS (3–12 months)
- Deploy the MVP: S3 corpus · Lambda (Function URL) for router + retrieval · DynamoDB for rule tables + audit log · Bedrock for answers
- Hybrid retrieval (BM25 + dense embeddings) once the corpus outgrows keyword search
- **Bahasa Malaysia + English** queries and documents
- Multi-agency S3 connectors
- Rule engine admin interface that flags rules whose source circular has changed
- Institutional memory capture workflow (Transcribe + Textract pipeline)
- Role-based access (Cognito)
- Bedrock Guardrails (content filtering)
- Offline cache for low-connectivity district offices

### Phase 3 — Ecosystem (12–24 months)
- Knowledge Graph layer (Amazon Neptune) alongside the retrieval index, for relationship queries and change propagation, and kept off the per-query hot path
- Cross-agency semantic search (federated, no data movement)
- Policy change propagation alerts ("Circular X has been updated — these 4 SOPs reference it")
- Integration with Dayang (citizen-facing AI) so Dayang can route internal knowledge questions to WAWASAN
- SAIC oversight dashboard — which agencies are most active, what questions are being asked most

---

## The Pitch in One Sentence

> *"WAWASAN is the internal Dayang — an AI knowledge assistant for Sarawak civil servants that turns decades of government documents into instant, cited, trustworthy answers, so no knowledge is ever lost when a civil servant retires and no officer ever wastes an afternoon searching for a circular that already exists."*

---

## Why This Hasn't Been Built Yet

| Reason | Explanation |
|---|---|
| **Dayang filled the visible gap** | The citizen-facing problem was more politically visible; the internal civil servant problem was invisible |
| **DDMS was seen as "solved"** | Malaysia deployed DDMS in the 2000s; the fact that it doesn't enable intelligent retrieval was never framed as a gap to fill |
| **RAG + rule-based + memory = too complex for one team** | Each component has been researched in isolation; combining all three in a government-specific product with governance built in is new work |
| **No one owns the problem** | SAIC coordinates AI policy but doesn't build products. Agencies use DDMS but don't have AI budgets. The gap falls between mandates. |
| **Language barrier was unsolved** | Multilingual BM/EN government document retrieval with reliable quality has only become feasible with modern embedding models (2024–2025) |

WAWASAN is buildable now because the production components it relies on (Bedrock foundation models, multilingual embeddings, managed hybrid search, Guardrails) all reached production maturity in 2024–2025. The MVP in `demo/` makes the complementary point: the core pipeline logic of routing, rule lookup, retrieval, refusal and supersession needs no heavy infrastructure at all.

---

*Sources: UiTM Sarawak (2012), The Edge Malaysia (2026), IBM IBV (2026), Esper (2024), Deakin University (2024), Frontiers in AI (2026), NORC (2025), ICMA (2025), Thomson Reuters (2026), AWS ML Blog (2024)*
