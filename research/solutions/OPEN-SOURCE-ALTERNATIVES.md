# Open Source & Free Stack Alternatives to WAWASAN Pipeline
## AWS Student Community Day Kuching 2026

> **Status: alternatives considered, not chosen.** The hackathon build is a dependency-free local pipeline
> (`demo/`) with Amazon Bedrock as the optional LLM and S3 / Lambda / DynamoDB as the production target.
> See [`PIPELINE-FULL.md`](../../PIPELINE-FULL.md) for the actual stack and why the Ollama / VPS route was
> rejected (model download size, CPU inference latency). This document is kept as reference for
> agencies that cannot send data to any cloud. Its "Recommended Hackathon Approach" section below predates
> that decision.

> **Context:** The WAWASAN pipeline uses paid AWS services (Bedrock, OpenSearch, Textract, etc.).
> This document maps every component to a free/open-source alternative —
> useful if the team wants a fully $0 stack, has no AWS credits, or wants
> to pitch data sovereignty (all data stays on your own server).

---

## Component-by-Component Replacement Map

| WAWASAN (AWS) | Open Source Alternative | Cost | Notes |
|---|---|---|---|
| Amazon Bedrock (LLM) | **Ollama + Llama 3 / Qwen3 / Mistral** | $0 | Runs locally on any modern laptop |
| Amazon Bedrock Knowledge Bases | **LlamaIndex** or **LangChain** | $0 | Python frameworks, full control |
| Amazon OpenSearch (vector + BM25) | **Chroma** / **Qdrant** / **FAISS** | $0 | Self-hosted vector stores |
| Amazon Textract (OCR) | **Tesseract OCR** + **PyMuPDF** | $0 | Open source OCR and PDF parser |
| Amazon Transcribe | **OpenAI Whisper** (local) | $0 | Runs offline, no API call needed |
| Amazon Cognito (auth) | **Keycloak** / **Authentik** | $0 | Open source identity providers |
| Amazon DynamoDB (audit log) | **SQLite** / **PostgreSQL** | $0 | Standard open source databases |
| AWS Lambda (serverless compute) | **FastAPI** on any server | $0 | Python web framework |
| AWS Amplify (frontend) | **Streamlit** / **Gradio** / **Next.js** | $0 | Chat UI in minutes |
| Amazon Neptune (KG, Phase 2) | **Neo4j Community** / **Apache Jena** | $0 | Open source graph databases |
| Bedrock Guardrails | **LlamaGuard** (Meta, open source) | $0 | Content moderation model |

---

## Three Ready-Made Open Source Stacks

Rather than assembling every piece yourself, these are complete platforms that already wire everything together:

---

### Stack A — Ollama + Open WebUI *(Easiest, hackathon-ready)*

**Best for:** Fastest demo with zero cost, no cloud dependency

```
Documents (PDF, DOCX)
    → PyMuPDF (parse) + Tesseract (OCR for scans)
    → Open WebUI built-in RAG pipeline
    → Ollama (local LLM: Llama 3.1 8B or Qwen3 7B)
    → FAISS or Chroma (vector store, built-in)
    → Open WebUI chat interface
```

**What it gives you:**
- Full chat UI out of the box — drag-and-drop PDF upload, instant Q&A
- Runs completely offline — no internet needed during demo
- BM25 + vector hybrid search available in Open WebUI
- Document citations shown per answer
- Free forever, no account needed

**What it lacks vs WAWASAN:**
- No role-based access control (everyone sees everything)
- No audit log
- Slower than Bedrock on large corpora (depends on your laptop GPU)
- No multilingual fine-tuning — Llama 3.1 handles BM reasonably but not optimally

**Setup time:** 20–30 minutes
**Hardware requirement:** 8GB RAM minimum, 16GB recommended for 7B model

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b

# Open WebUI (Docker)
docker run -d -p 3000:8080 \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  ghcr.io/open-webui/open-webui:main
```

---

### Stack B — LlamaIndex + Qdrant + Ollama *(Most similar to WAWASAN architecture)*

**Best for:** A custom-built solution that mirrors the WAWASAN pipeline exactly but costs $0

```
Documents
    → PyMuPDF + Tesseract (ingestion)
    → LlamaIndex (chunking + embedding)
    → Ollama nomic-embed-text (embeddings, multilingual)
    → Qdrant (vector store, self-hosted via Docker)
    → BM25Retriever (LlamaIndex built-in)
    → Hybrid retrieval (BM25 + dense vector)
    → Ollama Qwen3 7B (answer generation)
    → FastAPI (query router + confidence check)
    → SQLite (audit log)
    → Streamlit (chat UI)
```

**What it gives you:**
- Hybrid BM25 + vector retrieval — same as WAWASAN SOL-05
- Full control over chunking strategy, embedding model, reranker
- Qdrant supports metadata filtering — version dates, department tags, supersession links
- Runs on any server or laptop — fully air-gapped if needed
- Closest open-source equivalent to the full WAWASAN architecture

**What it lacks:**
- More setup than Stack A — you wire the pieces yourself
- No built-in guardrails (add LlamaGuard separately if needed)
- Qwen3 7B is good at BM but less polished than Claude Sonnet on formal government language

**Setup time:** 1–2 hours (bring this as your dev stack, not the hackathon build)

**Key libraries:**
```bash
pip install llama-index llama-index-vector-stores-qdrant \
            llama-index-retrievers-bm25 \
            llama-index-llms-ollama \
            llama-index-embeddings-ollama \
            fastapi streamlit qdrant-client pymupdf
```

---

### Stack C — RAGFlow *(Most powerful all-in-one, government-grade)*

**Best for:** A production-ready deployment with UI, connectors, and deep document parsing

RAGFlow is a full open-source RAG platform with a web UI, document parsing (including scanned PDFs with layout understanding), multi-source connectors, and hybrid retrieval. It is the closest open-source equivalent to Amazon Q Business.

```
Documents (PDF, DOCX, scanned images, web pages)
    → RAGFlow built-in document parser (layout-aware, table extraction)
    → RAGFlow hybrid retrieval (BM25 + vector)
    → Any LLM backend: Ollama / Qwen3 / local Mistral
    → RAGFlow chat UI (multi-user, conversation history)
    → Citation on every answer
    → API for integration with other systems
```

**What it gives you:**
- Layout-aware PDF parsing — understands tables, columns, headers (better than simple chunking)
- Multi-user with conversation history
- Source citations built in
- Supports multiple document types including scanned images
- Self-hosted, fully open source (Apache 2.0 license)
- Docker deployment in under 10 minutes

**What it lacks:**
- Needs a server with at least 16GB RAM for comfortable use
- No built-in role-based access (add Authentik/Keycloak in front)
- Ollama integration can be slower on CPU-only machines

**Deployment:**
```bash
git clone https://github.com/infiniflow/ragflow
cd ragflow
docker compose up -d
# UI at http://localhost
```

---

## Model Recommendations (Free, Multilingual, Government-Suitable)

| Model | Size | BM Support | English | Why |
|---|---|---|---|---|
| **Qwen3 7B** | 7B | ✅ Good | ✅ Good | Best BM + EN balance for small hardware; made by Alibaba, strong SEA language support |
| **Llama 3.1 8B** | 8B | ✅ Decent | ✅ Excellent | Meta's open model; strong English, acceptable BM |
| **Mistral 7B** | 7B | ✅ Decent | ✅ Good | Fast, efficient; good for structured fact extraction |
| **Gemma 3 4B** | 4B | ⚠️ Limited | ✅ Good | Google's lightweight model; runs on 6GB RAM |
| **DeepSeek-R1 7B** | 7B | ✅ Good | ✅ Good | Strong reasoning; good for policy interpretation |

**For WAWASAN specifically:** Use **Qwen3 7B** via Ollama — it has the best Bahasa Malaysia coverage among freely available models as of 2026, and handles formal government language well.

**Embedding model:** `nomic-embed-text` via Ollama — free, multilingual, 768-dimension, works well with hybrid retrieval.

---

## Advantages of the Open Source Stack

### ✅ Completely $0 — no API costs ever
Every token processed locally costs nothing. A Sarawak government agency running 10,000 queries/month on the open source stack pays $0 in inference costs forever.

### ✅ Full data sovereignty
Government documents never leave the server. No document, query, or answer is transmitted to AWS, OpenAI, Anthropic, or any third party. For sensitive Sarawak state circulars and policy documents, this is a significant governance advantage.

### ✅ No vendor lock-in
The stack is portable. If a better model comes out next month, swap it in with one command. No contract, no migration, no pricing change.

### ✅ Air-gapped deployment possible
For agencies with no internet access or strict network isolation requirements (e.g., defence-adjacent agencies), the entire stack runs offline. Nothing requires outbound connectivity.

### ✅ Hackathon pitch angle: data sovereignty + zero ongoing cost
"Our solution runs entirely within Sarawak's own servers — no government document ever touches an external cloud" is a powerful pitch line that the AWS stack cannot match.

---

## Disadvantages of the Open Source Stack

### ❌ Answer quality is lower than Claude Sonnet
Llama 3.1 8B and Qwen3 7B are significantly less capable than Claude 3.5 Sonnet for nuanced policy language interpretation. Formal Bahasa Malaysia government circulars are complex — smaller local models may produce grammatically awkward or imprecise answers.

### ❌ Requires hardware you own or rent
Ollama needs a real machine. A laptop with 16GB RAM works for a demo. Production at any scale requires a dedicated server — either on-premises or a rented VM. That VM costs money. The "free" label applies to software licensing, not infrastructure.

### ❌ OCR quality is lower than Amazon Textract
Tesseract is good for clean scans. Sarawak's older government documents — mixed layout, low DPI scans, handwritten annotations — will produce worse OCR output than Textract, directly reducing retrieval quality.

### ❌ More setup and maintenance responsibility
Ollama doesn't update itself. Qdrant doesn't patch itself. Models don't fine-tune themselves. The team owns the entire stack operationally — security patches, version updates, capacity planning. For a government agency without a dedicated AI ops team, this is a real burden.

### ❌ Multilingual support is less polished
AWS Titan's multilingual embeddings are specifically optimized. Qwen3's BM support is good but inconsistent on formal bureaucratic language. Mixed BM/EN documents may produce lower-quality embeddings and worse retrieval than the AWS equivalent.

### ❌ No managed guardrails
Bedrock Guardrails is a managed content safety layer. Replacing it with LlamaGuard requires additional setup and is less battle-tested for government-specific content moderation requirements.

---

## Head-to-Head: AWS Stack vs Open Source Stack

| Dimension | AWS (WAWASAN) | Open Source (Stack B) |
|---|---|---|
| **Cost (hackathon)** | ~$2–3 | $0 |
| **Cost (production/month)** | $70–130 | $0 software + server cost |
| **Answer quality** | ⭐⭐⭐⭐⭐ Claude Sonnet | ⭐⭐⭐ Qwen3 7B |
| **BM language support** | ⭐⭐⭐⭐ Titan multilingual | ⭐⭐⭐ Qwen3 |
| **OCR quality** | ⭐⭐⭐⭐⭐ Textract | ⭐⭐⭐ Tesseract |
| **Data sovereignty** | ⚠️ Data sent to AWS | ✅ Fully local |
| **Setup complexity** | Medium (console UI) | Higher (code + Docker) |
| **Hackathon build speed** | Faster | Slower |
| **Vendor lock-in** | High | None |
| **Offline capability** | ❌ | ✅ |
| **Scalability** | ✅ Auto-scales | Manual |
| **Governance / audit** | ✅ Built-in | DIY |

---

## Recommended Hackathon Approach

**Use AWS for the demo, mention open source in the pitch.**

The AWS stack builds faster in 4 hours (Bedrock console UI vs writing Python glue code) and produces a higher-quality demo (Claude Sonnet vs Qwen3 7B). But in the 5-minute pitch, explicitly mention:

> *"For data-sovereign deployments — where government documents cannot leave Sarawak's own servers — WAWASAN can run entirely on open-source components: Ollama with Qwen3 for the LLM, RAGFlow for the RAG pipeline, and Qdrant for the vector store. The architecture is the same. The data never leaves the building."*

This wins on both fronts: you get the polished AWS demo AND you demonstrate awareness of data sovereignty — which is a real concern for Sarawak government and will resonate with any technically literate judge.

---

*Sources: onyx.app Self-Hosted RAG Landscape (2026), markaicode.com Best Local RAG Stack (2026), dev.to Local LLM Guide (2026), RAGFlow GitHub (Apache 2.0), Open WebUI GitHub (MIT), LlamaIndex docs, Qdrant docs*

---

## Stack D — VPS-Hosted Ollama *(Best balance: free software, real server, anywhere access)*

**Best for:** Teams who want a $0 software stack but need reliable performance accessible from any device

Rather than running Ollama on your laptop (dependent on RAM, battery, connectivity), deploy it on a rented VPS. The software stack is identical — Ollama, Qdrant, Open WebUI — but it runs on a real server accessible by the whole team from any browser.

### Why VPS beats local for a hackathon

- The demo endpoint works from any device — phones, other laptops, judge's browser
- No "my laptop crashed" risk mid-demo
- Consistent latency regardless of background processes
- Stays up after the hackathon for a real pilot

### Hardware needed for Qwen3 7B

- **Minimum:** 8 GB RAM, 4 vCPU (slow, ~5 tok/s)
- **Recommended:** 16 GB RAM, 8 vCPU (comfortable, ~10 tok/s CPU-only)
- **Ideal:** 16 GB RAM + 8–12 GB VRAM GPU (40–80 tok/s, production speed)

### Cheapest CPU-only VPS options (Oct 2026)

| Provider | Plan | RAM | Cost/month | Cost for 4hr hackathon |
|---|---|---|---|---|
| **Hetzner CX43** | Shared AMD | 16 GB | ~$12 | **~$0.08** |
| **Contabo VPS M** | Standard | 16 GB | ~$9 | ~$0.05 |
| **Oracle Cloud** | ARM Free Tier | 24 GB | **$0 forever** | **$0** |

### Cheapest GPU VPS options (for production speed)

| Provider | GPU | VRAM | Cost/hr | Hackathon (4hr) |
|---|---|---|---|---|
| **RunPod Community** | RTX 3080 | 10 GB | ~$0.19 | **~$0.76** |
| **Vast.ai** | RTX 3080/3090 | 10–24 GB | ~$0.16–0.30 | ~$0.65–$1.20 |

### One-command Docker Compose deploy

```yaml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: [ollama_data:/root/.ollama]

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: [qdrant_data:/qdrant/storage]

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports: ["3000:8080"]
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes: [webui_data:/app/backend/data]

volumes:
  ollama_data:
  qdrant_data:
  webui_data:
```

```bash
docker compose up -d
docker exec ollama ollama pull qwen3:7b
docker exec ollama ollama pull nomic-embed-text
# Team accesses: http://<vps-ip>:3000
```

### Hackathon pitch line for data sovereignty

> *"WAWASAN runs on a RM 50/month server inside Sarawak's own infrastructure — no government document ever leaves the building, and the ongoing cost is cheaper than a staff meal allowance."*

This answers both major government objections: **data sovereignty** (docs stay on Sarawak soil) and **cost** (RM 50/month vs RM 300–600 on AWS).

### Hidden gem: Oracle Cloud Free Tier

Oracle's always-free tier gives you **4 ARM vCPU + 24 GB RAM, permanently free**. Qwen3 7B runs at ~8–12 tok/s on it — more than enough for a hackathon demo and a months-long pilot at zero cost.

*Sources: Hetzner pricing (Oct 2026), RunPod pricing (2026), cybernews.com VPS for Ollama (2026), youstable.com Ollama VPS requirements (2026)*
