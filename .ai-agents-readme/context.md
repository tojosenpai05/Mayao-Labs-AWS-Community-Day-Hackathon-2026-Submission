# Product

This project is a hackathon submission for **AWS Student Community Day Kuching 2026** (#SCDKuching2026), held on 7 October 2026 at Swinburne Sarawak.

**Submission requirements:**
- GitHub repository must be public
- README must include all group members' names
- README must include 2–3 screenshots of the project
- Deadline: 3:00 PM, 7 October 2026

**Product: WAWASAN** — an internal knowledge assistant for Sarawak civil servants.

- **Problem:** officers can't find the right policy, SOP or circular, can't tell which version is current, and lose the reasoning behind decisions when experienced staff retire.
- **What it does:** a question goes through a router. Structured facts are answered by a deterministic rule table. Everything else goes to BM25 retrieval and then a confidence gate (refuses below 0.60), with an optional LLM producing the final answer. Every answer cites its source, superseded circulars are never used as answers, and every query is audit-logged. Captured knowledge interviews with retiring officers are indexed alongside circulars (SOL-03).
- **Build status:** working local demo in `demo/` (Python stdlib only; run `python3 demo/app.py`). Optional Amazon Bedrock answer generation via `LLM_PROVIDER=bedrock`. English only.
- **Production target:** S3 · Lambda · DynamoDB · Bedrock. See `PIPELINE-FULL.md`.
- **Key docs:** `README.md` (submission), `PRODUCT-DESIGN.md` (design + roadmap), `research/00-SYNTHESIS.md` (problem research), `research/solutions/` (solution ratings).
