# Initial Solution Thoughts — kaz

> Part of this was written based on `SOL-00-SOLUTIONS-OVERVIEW.md`, before
> `SOL-SYNTHESIS-AND-RATING.md` existed. Sorry if anything sounds weird, I may
> have messed something up.

Define **PF = pain factor** (see `research/00-SYNTHESIS.md`).

Database where all organizational documents are dumped + AI agent that reads
through that database and gives results (I think this is similar to what you're
talking about when you mentioned RAG? Dynamically building a knowledge graph
from that database sounds good too) -> solves PFs 1, 2, 3, partial 6

- questions

    - how do we get people to actually use it? related to PF 5

    - security considerations -> might need a classification class type tag
      thing in db? more thinking required (solved in
      `SOL-SYNTHESIS-AND-RATING.md`, I like what you have going there)

    - might need a version tag as well to solve the currency problem

    - how does out-of-corpus detection work? is it proven to work well?

    - is having a knowledge graph significantly better for query to response 
      latency? having a slow service will reduce adoption 

PF 4 is a challenge that would ideally be addressed, is it even possible to
solve this without something BCI related? maybe consider integrating SOL-03?

    - maybe speech-based AI can be a solution? dictate organizational
      knowledge, AI asks questions to fill in gaps, then turns knowledge into
      documentation?

---

## Fact-check against `research/` (added by Kiro)

Checked the above against `00-SYNTHESIS.md`, `SOL-00`, `SOL-01`, `SOL-03`, and
`SOL-SYNTHESIS-AND-RATING.md`. Overall it holds up — the intuitions match the
research. A few notes where a claim is slightly stronger than the sources
strictly support, or worth sharpening:

- **"database + AI agent = RAG" — correct.** SOL-01 describes exactly this:
  retrieval over a document store feeding an LLM that returns grounded, cited
  answers. The "dynamically building a knowledge graph" idea maps to SOL-04
  (Amazon Neptune KG) and SOL-03's indexing layer.

- **"solves PFs 1, 2, 3, partial 6" — mostly right, one nuance.** In SOL-00's
  mapping, plain RAG (SOL-01) is the primary fix for PF1 (can't find docs) and
  PF6 (slow decisions), and only partial on PF2 (version confusion). PF3 (siloed
  systems) is really the knowledge graph's job (SOL-04) rather than RAG's — so
  the claim works *because* you included the knowledge-graph idea. RAG alone
  wouldn't cover PF3.

- **Version tag / currency — well supported.** PF2 plus SOL-01's "temporal/
  version awareness is not built in" weakness and the Deltek finding (needs
  chronological awareness or it returns once-correct-but-now-outdated answers)
  back this up. A version/supersession tag is a real need, not optional.

- **Security / classification tag — matches the synthesis.** SOL-SYNTHESIS's
  "role-based access → junior staff can't access classified circulars" is
  exactly the classification-tag idea.

- **Out-of-corpus detection — real, but your skepticism is justified.** SOL-01
  is explicit that confidence calibration ("knowing when to say I don't know")
  must be deliberately engineered — it doesn't come for free, and hallucination
  *increases* when the relevant document is absent from the corpus
  (arXiv 2026 finding). So: it works, but it is not a solved/guaranteed feature.

- **PF4 + SOL-03 + speech capture — directly supported.** SOL-03's Layer 1
  (Capture) literally describes AI-assisted "knowledge extraction" interviews:
  staff narrate tasks while AI transcribes, tags, and structures the knowledge
  (AWS stack uses Amazon Transcribe). Your "dictate knowledge, AI asks questions
  to fill gaps, turn into documentation" idea is essentially SOL-03's capture
  workflow. No BCI needed. Caveat from SOL-03: it depends on cooperation from
  the exact (busy, retiring) staff you most want to capture, and the capture
  format is hard to standardize.

**Bottom line:** nothing here is wrong. The composite you're gesturing at
(RAG core + knowledge graph + classification/version metadata + SOL-03 capture
for PF4) lines up with the recommended composite in `SOL-SYNTHESIS-AND-RATING.md`
(SOL-01 + SOL-05 + SOL-06, with SOL-03/SOL-04 as narrative/vision).
