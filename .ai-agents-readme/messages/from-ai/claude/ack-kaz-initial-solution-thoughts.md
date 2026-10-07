# Ack: kaz — Initial Solution Thoughts

Re: `messages/from-human/kaz/initial-solution-thoughts.md`

Read it, along with Kiro's fact-check. Agree with the bottom line — your composite
(RAG core + KG + classification/version metadata + SOL-03 capture for PF4) matches
what `PRODUCT-DESIGN.md` (WAWASAN) already specifies.

## What was already covered in the docs

| Your point | Where it lives |
|---|---|
| Adoption (PF5) | `PRODUCT-DESIGN.md` → Disadvantages → "Change management is not a technical problem" |
| Classification / security tag | `PRODUCT-DESIGN.md` → role-based access; `SOL-SYNTHESIS-AND-RATING.md` |
| Version tag / currency | `PRODUCT-DESIGN.md` → "Version-aware, not just version-storing" |
| Out-of-corpus detection | `PRODUCT-DESIGN.md` → "If it doesn't know the answer, it says so" (SOL-06) |
| PF4 speech capture | `PRODUCT-DESIGN.md` → Institutional Memory layer (SOL-03, Transcribe pipeline) |

## What was missing — now merged

**KG query latency** was the one open question with no answer in the docs. Added to
`PRODUCT-DESIGN.md` under "deliberately excluded":

- Yes, graph traversal is slower than vector search (tens of ms vs. 100ms–low seconds
  for multi-hop queries).
- But LLM generation (1-3s+) dominates total latency either way, so retrieval method
  alone isn't what kills adoption.
- The real cost is putting live KG traversal on every query's hot path — added latency
  plus engineering complexity we can't absorb in 4 hours. So KG stays as Phase 3
  architecture in the pitch, not a live demo dependency.

Note: these latency ranges are general engineering estimates, not from our research
sources — no paper in `research/` benchmarks this. Treat as directional.

Also fixed an inconsistency: `PRODUCT-DESIGN.md` said KG was "roadmap Phase 2" but the
roadmap section lists it under Phase 3. Now says Phase 3 in both places.

— Claude (for Anantojo)
