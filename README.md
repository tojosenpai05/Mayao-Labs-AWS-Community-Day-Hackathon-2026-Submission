# WAWASAN — Government Knowledge Intelligence

**Mayao Labs · AWS Student Community Day Kuching 2026 (#SCDKuching2026)**

Government agencies hold thousands of policies, SOPs, circulars and meeting minutes, but officers can't find the right one quickly, can't tell which version is current, and lose the reasoning behind decisions when experienced staff retire.

WAWASAN is an internal knowledge assistant for Sarawak civil servants. You ask a question in plain English, and it returns an answer **quoted from a real document**. It names the exact file and shows that file with the passage highlighted, so anyone can check the answer. When no document covers the question, it **says so instead of guessing**.

**Nothing in this demo is invented.** It searches only real files that exist in this repository: the team's research notes, which cite published studies.

## Team

- Shoaib Ur Rahman Syed
- Kazuki Soma
- Anantojo Mendan

## Screenshots

All screenshots show real answers from DeepSeek (`deepseek-v4-flash`) over the real papers.

**A cited answer, with the only text the AI was given beside it:** *"What is federated information retrieval?"* DeepSeek's summary on the left, the exact passage it received on the right (Melzer et al., CEUR-WS, page 9). Anyone can check that it added nothing.

![Cited answer with source file](demo/screenshots/1-cited-answer-with-source.png)

**Click "Open source file" and the real file pops up:** the PDF of Mathur et al. 2026, scrolled to the cited passage on page 4 (the Conclusion), with buttons to open or download the original.

![Source file pop-up](demo/screenshots/4-source-file-popup.png)

**"Open original" opens the publisher's PDF itself,** at the cited page. Below is page 4 of that paper, rendered straight from the PDF file; the cited Conclusion is at the bottom right. **"Download"** saves the same file, byte-for-byte identical to the original (checked with SHA-256). The server only serves files that are actually indexed, so these links cannot be used to read anything else on the machine.

![Open original: page 4 of the cited PDF](demo/screenshots/6-open-original-pdf-page4.png)

**When the passage doesn't answer, the AI declines:** for *"What are the failure points of RAG systems?"* the search found the Barnett et al. title page. DeepSeek read it, saw the answer wasn't there, and said so instead of answering from its own memory.

![AI declined](demo/screenshots/5-ai-declined.png)

**A question no document covers:** the accuracy check refuses it before any AI is used.

![Refused question](demo/screenshots/2-refused-question.png)

**The full pipeline,** opened via "How was this answered?": sources checked, the accuracy check with matched words, the AI step with its response time, and the activity log.

![Full pipeline](demo/screenshots/3-full-pipeline.png)

## What it searches

**8 published research papers** (77 pages) and the **team's 18 research notes** in [`research/`](research/) that summarise and cite them:

| Paper | Source |
|---|---|
| Barnett et al. 2024, *Seven Failure Points When Engineering a Retrieval Augmented Generation System* | arXiv 2401.05856 |
| *Retrieval-Augmented Generation for Domain-Specific Question Answering* (Pittsburgh and CMU) | arXiv 2411.13691 |
| *Chunking, Retrieval, and Re-ranking: An Empirical Evaluation of RAG Architectures for Policy* | arXiv 2601.15457 |
| Mathur et al. 2026, *Retrieval Improvements Do Not Guarantee Better Answers: A Study of RAG for AI Policy QA* | arXiv 2603.24580 |
| Baldwin 2026, *Knowledge Graph Representations for LLM-Based Policy Compliance Reasoning* | arXiv 2604.27713 |
| Pingili 2025, *AI-driven intelligent document processing in government and public administration* | WJAETS |
| Melzer et al., *Federated Information Retrieval in Cross-Domain Information Systems* | CEUR-WS Vol. 3580 |
| Orji et al. 2024, *A Knowledg Graph Model for e-Government* [sic] | IJISRT |

The PDFs are **downloaded from their publishers, not committed**, to respect their licences. Fetch them once with `sh demo/fetch_papers.sh`. Without them, the demo still runs on the research notes.

Documents are split into passages of roughly 60–180 words, page by page for PDFs. Every answer therefore points to an exact passage and page, not a whole paper. Title blocks and figure captions are folded into real text, so a passage is never just a paper's title. Any other PDF dropped into `demo/library/` is indexed on the next restart (text extracted by `pdftotext` from poppler-utils).

Example questions: *What are the failure points of RAG systems?* (answered from the Barnett et al. paper) · *Does better retrieval guarantee better answers?* (answered from the Conclusion of Mathur et al.) · *Why is DDMS adoption in Malaysia still low?* · *What is the work-from-home policy?* (refused: no document covers it)

**Every answer works with no AI at all.** Without an LLM, the answer is the best-matching passage quoted word for word, and the self-test checks that it appears verbatim in the cited passage. With an LLM connected, the answer card shows the AI's summary **beside the only passage the AI was given**, so anyone can check it added nothing.

## How it works

```
Query → Router ─┬─ FACTUAL ──────→ Rule engine ───────────────────────────┬→ Answer + citation → Audit log
                └─ INTERPRETIVE ─→ BM25 retrieval → Confidence gate → LLM ┘
```

- **Router.** Questions containing structured-fact markers (*grade, entitlement, limit, rate…*) go to the rule engine. *Why* questions always go to retrieval, because a lookup table cannot explain a rationale.
- **Rule engine (policy lookup).** A table of exact values, each pointing at the official circular it came from. **It is empty in this demo**, because we only use verified real documents and have no official circulars yet. Every question therefore goes to document search. In deployment it is filled from an agency's verified circulars.
- **BM25 retrieval** over the document passages. Documents marked as superseded are still retrieved but never used as the answer (no real documents in the demo are superseded yet).
- **Confidence gate.** This is the share of the question's key terms that appear in the top source, with rarer, more specific terms weighted higher. Below 0.50, the system refuses before any LLM call is made.
- **Audit log.** Every query, answer, source and confidence score is recorded.

## Run it

Requires Python 3.10+. **No packages to install**: it uses only the standard library.

```bash
python3 demo/app.py            # http://localhost:8000
python3 demo/app.py --selftest # checks real files, ranking, refusal, verbatim quotes
```

Optional LLM answer generation with Amazon Bedrock, DeepSeek or Groq's free tier:

```bash
# Amazon Bedrock: needs AWS CLI credentials and model access enabled for Claude Haiku 4.5
LLM_PROVIDER=bedrock AWS_REGION=ap-southeast-1 python3 demo/app.py

# DeepSeek (or put the key in demo/.env, copied from demo/.env.example; it is git-ignored)
DEEPSEEK_API_KEY=your_key python3 demo/app.py

# Groq free tier (no credit card)
GROQ_API_KEY=your_key python3 demo/app.py

# Any OpenAI-compatible endpoint (e.g. a self-hosted model): add LLM_BASE_URL=<url>/chat/completions
```

See [Connecting Amazon Bedrock](#connecting-amazon-bedrock) for the full setup.

## Connecting Amazon Bedrock

The demo calls Bedrock through the AWS CLI, so there is nothing extra to install in Python. You need the AWS CLI v2, an AWS account, and about 10 minutes.

**1. Create credentials with Bedrock permission.** In the IAM console, create a user (or use an existing one) and attach a policy that allows `bedrock:InvokeModel`. The Converse API the demo uses requires this permission. For a demo this is enough:

```json
{
  "Version": "2012-10-17",
  "Statement": [{ "Effect": "Allow", "Action": "bedrock:InvokeModel", "Resource": "*" }]
}
```

Scope `Resource` down to the specific model and inference-profile ARNs for anything beyond a demo. Then create an access key for the user.

**2. Configure the CLI** in your own terminal. Never put keys in the repo.

```bash
aws configure            # access key, secret key, region: ap-southeast-1, output: json
aws sts get-caller-identity   # should print your account and user
```

**3. Enable the model.** In the Bedrock console (region `ap-southeast-1`), check that **Claude Haiku 4.5** is available to your account. If the console shows a *Model access* page, request access there. The first use of an Anthropic model may ask for a short one-time use-case form.

**4. Test Bedrock directly:**

```bash
aws bedrock-runtime converse --region ap-southeast-1 \
  --model-id global.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --messages '[{"role":"user","content":[{"text":"Reply with OK"}]}]'
```

If you get a JSON response containing `"OK"`, you're connected.

**5. Run the demo on Bedrock:**

```bash
LLM_PROVIDER=bedrock AWS_REGION=ap-southeast-1 python3 demo/app.py
```

The startup line should say `LLM: Amazon Bedrock`. Answers then show an **AI summary · Bedrock** badge, and the *Quoted from source* badge disappears.

**Troubleshooting.** Errors are printed in the terminal running `app.py`. The demo keeps working with extractive answers while you fix them.

| Error | Fix |
|---|---|
| `NoCredentials` | Step 2 wasn't done in the shell running the demo |
| `AccessDeniedException` | The IAM policy (step 1) or model access (step 3) is missing |
| `ValidationException` about the model identifier | Copy the Haiku 4.5 inference profile ID shown in the Bedrock console for your region, and set `BEDROCK_MODEL_ID=<that id>` |

**Notes**
- The default `global.` inference profile may process requests outside `ap-southeast-1`. A deployment that needs data residency would use an in-region model or a geography-specific profile instead.
- Cost is about US$0.003 per answered question. Refused questions never call the model.

Open `http://localhost:8000/?q=your+question` to run a question directly from the URL.

## AWS deployment target

The demo runs locally. Each component maps one-to-one onto AWS, and the functions in `demo/app.py` that touch storage or the LLM (`load_library`, `call_llm`, `log_audit`) are the swap points:

| Demo today | On AWS |
|---|---|
| `research/*.md`, `demo/library/` | Amazon S3 |
| Router + BM25 (Python) | AWS Lambda behind a Function URL |
| Rule table (empty until verified circulars exist) | Amazon DynamoDB |
| Groq / extractive fallback | Amazon Bedrock, Claude Haiku 4.5 (already supported via `LLM_PROVIDER=bedrock`) |
| SQLite audit log | Amazon DynamoDB + CloudWatch |

**Estimated cost to run the demo on AWS: about US$1.** That covers ~300 queries at ~$0.003 each on Bedrock Haiku 4.5. Lambda, DynamoDB and S3 stay within the free tier at this volume. We deliberately do **not** use OpenSearch Serverless: at this corpus size BM25 inside Lambda is enough, and OpenSearch bills continuously (~$0.48/hr) whether it is queried or not.

## Roadmap

**Phase 2: production pilot (one agency)**
- Bedrock for answer generation, deployed on Lambda, DynamoDB and S3 as above
- Hybrid retrieval (BM25 + dense embeddings) once the corpus outgrows keyword search
- Role-based access (Amazon Cognito), so classified circulars are visible only to cleared roles
- Bedrock Guardrails for content filtering
- An admin interface for maintaining the rule table, which flags rules whose source circular has changed
- **Bahasa Malaysia + English** queries and documents. The demo is English-only.
- **Knowledge capture pipeline (SOL-03).** Retiring officers record exit interviews, transcribed by Amazon Transcribe. AI-guided follow-up questions fill the gaps, and the result is structured into indexed documents that WAWASAN searches like any other file.
- Filling the policy lookup table and version (supersession) links from an agency's verified official circulars

**Phase 3: ecosystem**
- Knowledge graph (Amazon Neptune) for cross-agency relationships, e.g. "Circular X changed, and these four SOPs reference it". It sits outside the live query path to keep latency down.
- Federated search across agencies without moving their data
- Integration with Dayang, Sarawak's citizen-facing assistant

## Research and design

- [`research/00-SYNTHESIS.md`](research/00-SYNTHESIS.md) covers the problem at international, Malaysian and Sarawak level, with seven recurring pain factors.
- [`research/solutions/`](research/solutions/) contains six candidate solutions and their ratings.
- [`PRODUCT-DESIGN.md`](PRODUCT-DESIGN.md) is the full product design.

## Note on the demo data

The demo searches only real files in this repository: the team's research notes in `research/`, plus any PDFs placed in `demo/library/`. An earlier version used invented sample circulars. They were removed because the demo must not present fabricated policy as fact.
