"""WAWASAN demo: router -> rule engine | BM25 -> confidence gate -> LLM -> audit.

Stdlib only. Run: python3 app.py            (serves http://localhost:8000)
                  python3 app.py --selftest
"""
import datetime
import http.server
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
CORPUS_DIR = ROOT / "corpus"
# Research library: the team's research notes plus any papers dropped into demo/library/.
# PDFs under research/ are skipped because they are generated copies of the notes.
LIBRARY_SOURCES = [(ROOT.parent / "research", {".md"}), (ROOT / "library", {".md", ".txt", ".pdf"})]
CHUNK_WORDS = 180
DB_PATH = ROOT / "audit.db"
# ponytail: lexical confidence gate. Paraphrases ("approves" vs "approval") cause false refusals,
# which is the safer failure for policy answers; add embedding similarity once retrieval goes hybrid.
THRESHOLD = 0.5
REFUSAL = "Information not available in the system."

# "why" is deliberately NOT a stopword: it signals a request for rationale.
STOP = set("""a an the is are was were be been what how do does did i you we for of to in
on at by and or with from can could should my me this that it its as any per
who when where which much many long about must will would has have had there their
these those into also than then only""".split())

FACTUAL = re.compile(r"\b(grade|entitlement|limit|rate|amount|maximum|how many|how much)\b", re.I)


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP]


# --- Swap points: each of these four becomes an AWS call in Phase 2 ---------

def load_corpus():
    docs = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        _, front, body = path.read_text().split("---", 2)
        meta = {}
        for line in front.strip().splitlines():
            key, _, value = line.partition(":")
            value = value.strip()
            meta[key.strip()] = None if value in ("", "null") else value
        meta["body"] = body.strip()
        meta["tf"] = Counter(tokenize(f"{meta['title']} {meta['body']}"))
        meta["len"] = sum(meta["tf"].values())
        docs.append(meta)
    return docs


def clean_markdown(text):
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s and set(s) <= set("|-: "):  # table rules and horizontal rules
            continue
        s = re.sub(r"^(#{1,6}|>)\s*", "", s).replace("**", "").replace("`", "")
        lines.append(s)
    return "\n".join(lines)


def is_heading(p):
    return len(p.split()) <= 8 and not p.rstrip().endswith((".", ":", "?", "!"))


def chunk(text, limit=CHUNK_WORDS):
    """Group paragraphs into ~limit-word passages so citations point at a passage, not a whole paper.
    Whole long documents would also defeat the confidence gate: they contain almost every term."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur, words = [], [], 0
    for p in paras:
        n = len(p.split())
        if cur and words + n > limit:
            carry = [cur.pop()] if len(cur) > 1 and is_heading(cur[-1]) else []  # heading belongs to what follows
            chunks.append("\n\n".join(cur))
            cur, words = carry, sum(len(c.split()) for c in carry)
        cur.append(p)
        words += n
    if cur:
        chunks.append("\n\n".join(cur))
    return [c for c in chunks if len(c.split()) >= 5]


def read_pages(path):
    """[(page_number or None, text)] for a library file."""
    if path.suffix.lower() == ".pdf":
        out = subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), "-"],
                             capture_output=True, text=True, timeout=120)
        if out.returncode:
            print(f"Skipping {path.name}: {out.stderr.strip()}", file=sys.stderr)
            return []
        return [(i + 1, page) for i, page in enumerate(out.stdout.split("\f")) if page.strip()]
    text = path.read_text(errors="replace")
    return [(None, clean_markdown(text) if path.suffix.lower() == ".md" else text)]


def load_library():
    files = sorted(p for folder, exts in LIBRARY_SOURCES if folder.exists()
                   for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in exts)
    chunks = []
    for path in files:
        raw = path.read_text(errors="replace") if path.suffix.lower() == ".md" else ""
        heading = re.search(r"^#\s+(.+)$", raw, re.M)
        title = heading.group(1).strip() if heading else path.stem.replace("-", " ").replace("_", " ")
        rel = str(path.relative_to(ROOT.parent))
        n = 0
        for page, text in read_pages(path):
            for body in chunk(text):
                n += 1
                tf = Counter(tokenize(f"{title} {body}"))
                chunks.append({"id": f"{path.stem}#{n}", "type": "research", "title": title, "dept": rel,
                               "date": None, "page": page, "superseded_by": None, "body": body,
                               "tf": tf, "len": sum(tf.values())})
    return chunks


def load_rules():
    return [
        {"topic": "Annual leave entitlement", "needs": {"annual", "leave"}, "source": "SC-4-2022",
         "by_grade": [(19, 40, "20 days"), (41, 43, "25 days"), (44, 52, "30 days"), (54, 99, "35 days")]},
        {"topic": "Medical leave", "needs": {"medical", "leave"}, "source": "SC-9-2022",
         "value": "Up to 90 days per calendar year (government medical officer certification)"},
        {"topic": "Direct procurement limit", "needs": {"procurement"}, "source": "SC-7-2024",
         "value": "RM 50,000 per transaction", "previous": "RM 20,000 per transaction"},
        {"topic": "Mileage rate", "needs": {"mileage"}, "source": "SC-2-2023",
         "value": "RM 0.70 per kilometre"},
        {"topic": "Overtime rate", "needs": {"overtime"}, "source": "SC-6-2023",
         "value": "1.5x hourly rate on a working day; 2.0x on a rest day or public holiday"},
        {"topic": "Accommodation ceiling", "needs": {"accommodation"}, "source": "SC-2-2023",
         "by_grade": [(1, 43, "RM 160 per night"), (44, 99, "RM 220 per night")]},
    ]


def llm_provider():
    if os.environ.get("LLM_PROVIDER", "").lower() == "bedrock":
        return "bedrock"
    return "groq" if os.environ.get("GROQ_API_KEY") else None


def call_llm(prompt):
    provider = llm_provider()
    if provider == "bedrock":
        return _bedrock(prompt)
    if provider == "groq":
        return _groq(prompt)
    return None


def _bedrock(prompt):
    # The AWS CLI signs the request with the configured credentials, so no boto3 / SigV4 code is needed.
    request = {
        "modelId": os.environ.get("BEDROCK_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0"),
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 400, "temperature": 0},
    }
    try:
        out = subprocess.run(["aws", "bedrock-runtime", "converse", "--cli-input-json", json.dumps(request),
                              "--output", "json"], capture_output=True, text=True, timeout=25)
        if out.returncode:
            print(f"Bedrock call failed: {out.stderr.strip()}", file=sys.stderr)
            return None
        return json.loads(out.stdout)["output"]["message"]["content"][0]["text"].strip()
    except Exception as exc:
        print(f"Bedrock call failed: {exc}", file=sys.stderr)
        return None


def _groq(prompt):
    key = os.environ["GROQ_API_KEY"]
    body = json.dumps({
        "model": os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile"),
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": "wawasan-demo"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # a dead network must degrade the demo, not crash it
        print(f"LLM call failed: {exc}", file=sys.stderr)
        return None


def log_audit(query, route, answer, source_id, confidence):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, user TEXT,
                      ts TEXT, query TEXT, route TEXT, answer TEXT, source TEXT, confidence REAL)""")
        cur = db.execute(
            "INSERT INTO audit (user, ts, query, route, answer, source, confidence) VALUES (?,?,?,?,?,?,?)",
            ("demo_officer", datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
             query, route, answer, source_id, confidence))
        return cur.lastrowid


# --- Pipeline -----------------------------------------------------------------

def classify(query):
    if re.search(r"\bwhy\b", query, re.I):
        return "INTERPRETIVE", "asks for rationale ('why') - a lookup table cannot answer it"
    hits = sorted({m.lower() for m in FACTUAL.findall(query)})
    if hits:
        return "FACTUAL", "structured-fact markers: " + ", ".join(hits)
    return "INTERPRETIVE", "no structured-fact markers"


def match_rule(query, rules):
    words = set(tokenize(query))
    grade = re.search(r"grade\s*(\d+)", query, re.I)
    for rule in rules:
        if not rule["needs"] <= words:
            continue
        if "by_grade" not in rule:
            return rule, rule["value"]
        if not grade:
            return None, None
        g = int(grade.group(1))
        for lo, hi, value in rule["by_grade"]:
            if lo <= g <= hi:
                return rule, f"{value} (Grade {g})"
    return None, None


def bm25(query, docs, k1=1.5, b=0.75):
    terms = tokenize(query)
    n = len(docs)
    avgdl = sum(d["len"] for d in docs) / n
    idf = {}
    for t in set(terms):
        df = sum(1 for x in docs if t in x["tf"])
        idf[t] = math.log(1 + (n - df + 0.5) / (df + 0.5))
    scored = []
    for d in docs:
        score = 0.0
        for t in terms:
            tf = d["tf"].get(t, 0)
            if tf:
                score += idf[t] * tf * (k1 + 1) / (tf + k1 * (1 - b + b * d["len"] / avgdl))
        scored.append((score, d))
    scored.sort(key=lambda x: -x[0])
    return scored


def best_current(ranked):
    """Top-ranked document that has not been superseded."""
    for score, d in ranked:
        if score > 0 and not d.get("superseded_by"):
            return score, d
    return 0.0, None


def coverage(query, doc, docs):
    """IDF-weighted share of the query's terms found in doc. Weighting matters on broad corpora:
    matching common words ('policy', 'work') must not outweigh missing the specific one ('home')."""
    terms = set(tokenize(query))
    matched = sorted(t for t in terms if doc and t in doc["tf"])
    missing = sorted(terms - set(matched))
    if not terms:
        return 0.0, matched, missing
    n = len(docs)
    weight = {t: math.log(1 + (n - df + 0.5) / (df + 0.5))
              for t in terms for df in [sum(1 for x in docs if t in x["tf"])]}
    return sum(weight[t] for t in matched) / sum(weight.values()), matched, missing


def extract(query, doc, limit=600):
    """No-LLM fallback: best-matching passage plus what follows it, skipping the
    interviewer's questions and the circular's one-line preamble (they echo the
    question rather than answer it)."""
    terms = set(tokenize(query))
    paras = [p.strip() for p in doc["body"].split("\n\n") if p.strip()]
    cands = [p for i, p in enumerate(paras)
             if not p.startswith("Interviewer:") and not (i == 0 and p.startswith("This circular"))] or paras
    best = max(range(len(cands)), key=lambda i: len(terms & set(tokenize(cands[i]))))
    out = [cands[best]]
    for p in cands[best + 1:]:
        if sum(map(len, out)) + len(p) > limit:
            break
        out.append(p)
    while len(out) > 1 and is_heading(out[-1]):  # a trailing heading introduces text we did not include
        out.pop()
    return re.sub(r"^Officer:\s*", "", "\n\n".join(out), flags=re.M)


def source_info(doc, by_id):
    if not doc:
        return None
    info = {k: doc.get(k) for k in ("id", "type", "title", "dept", "date", "officer", "page")}
    sup = doc.get("supersedes")
    info["supersedes"] = {"id": sup, "title": by_id[sup]["title"], "date": by_id[sup]["date"]} if sup in by_id else None
    return info


def answer(query, docs, rules):
    by_id = {d["id"]: d for d in docs}
    route, reason = classify(query)
    trace = {"query": query, "route": route, "route_reason": reason, "rule": None,
             "retrieval": [], "confidence": None, "llm": {"used": False}, "refused": False}

    if route == "FACTUAL":
        rule, value = match_rule(query, rules)
        trace["rule"] = {"matched": bool(rule), "topic": rule["topic"] if rule else None,
                         "previous": rule.get("previous") if rule else None}
        if rule:
            trace.update(answer=value, source=source_info(by_id[rule["source"]], by_id),
                         confidence={"value": 1.0, "threshold": THRESHOLD, "pass": True,
                                     "matched": [], "missing": [], "note": "exact rule match"})
            trace["audit_id"] = log_audit(query, route, value, rule["source"], 1.0)
            return trace

    ranked = bm25(query, docs)
    top = max(ranked[0][0], 1e-9)
    trace["retrieval"] = [{"id": d["id"], "title": d["title"], "type": d.get("type"),
                           "score": round(s, 2), "relative": round(s / top, 2),
                           "superseded_by": d.get("superseded_by")}
                          for s, d in ranked[:5] if s > 0]
    _, doc = best_current(ranked)
    conf, matched, missing = coverage(query, doc, docs)
    trace["confidence"] = {"value": round(conf, 2), "threshold": THRESHOLD, "pass": conf >= THRESHOLD,
                           "matched": matched, "missing": missing,
                           "note": "share of the question's key terms found in the top source, rarer terms weighted higher"}

    if conf < THRESHOLD:
        trace.update(refused=True, answer=REFUSAL, source=None)
        trace["audit_id"] = log_audit(query, route, REFUSAL, None, conf)
        return trace

    started = time.time()
    prompt = (f"Answer the question using ONLY the source below. Be concise (2-4 sentences). "
              f"If the source does not answer it, reply exactly: {REFUSAL}\n\n"
              f"SOURCE ({doc['id']}, {doc['title']}):\n{doc['body']}\n\nQUESTION: {query}")
    generated = call_llm(prompt)
    trace["llm"] = {"used": generated is not None, "provider": llm_provider(),
                    "ms": round((time.time() - started) * 1000),
                    "fallback": None if generated else "extractive (best-matching passage)"}
    text = generated or extract(query, doc)
    trace.update(answer=text, source=source_info(doc, by_id))
    trace["audit_id"] = log_audit(query, route, text, doc["id"], conf)
    return trace


# --- HTTP ---------------------------------------------------------------------

class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/status":
            status = {"llm": llm_provider(), "rules": len(RULES),
                      "corpora": {"circulars": {"documents": len(CORPORA["circulars"])},
                                  "library": {"documents": len({d["dept"] for d in CORPORA["library"]}),
                                              "passages": len(CORPORA["library"])}}}
            self._send(200, json.dumps(status), "application/json")
        elif path == "/api/audit":
            with sqlite3.connect(DB_PATH) as db:
                db.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, user TEXT, ts TEXT, "
                           "query TEXT, route TEXT, answer TEXT, source TEXT, confidence REAL)")
                rows = db.execute("SELECT id, ts, query, route, source, confidence FROM audit "
                                  "ORDER BY id DESC LIMIT 10").fetchall()
                total, refused = db.execute(
                    "SELECT COUNT(*), COALESCE(SUM(answer = ?), 0) FROM audit", (REFUSAL,)).fetchone()
            keys = ("id", "ts", "query", "route", "source", "confidence")
            summary = {"total": total, "answered": total - refused, "refused": refused}
            self._send(200, json.dumps({"rows": [dict(zip(keys, r)) for r in rows], "summary": summary}),
                       "application/json")
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/query":
            return self._send(404, "not found", "text/plain")
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        query = str(body.get("query", "")).strip()[:500]
        corpus = body.get("corpus", "circulars")
        if not query:
            return self._send(400, json.dumps({"error": "empty query"}), "application/json")
        if corpus not in CORPORA or not CORPORA[corpus]:
            return self._send(400, json.dumps({"error": f"unknown or empty corpus: {corpus}"}), "application/json")
        # The rule table holds circular facts; it does not apply to the research library.
        rules = RULES if corpus == "circulars" else []
        self._send(200, json.dumps(answer(query, CORPORA[corpus], rules)), "application/json")


def selftest():
    docs, rules = load_corpus(), load_rules()
    assert classify("What is the annual leave entitlement for Grade 41?")[0] == "FACTUAL"
    assert classify("How do I apply for annual leave?")[0] == "INTERPRETIVE"
    assert classify("Why was the procurement threshold raised in 2024?")[0] == "INTERPRETIVE"

    rule, value = match_rule("What is the annual leave entitlement for Grade 41?", rules)
    assert rule["source"] == "SC-4-2022" and value.startswith("25 days"), value

    _, top = best_current(bm25("How do I apply for annual leave?", docs))
    assert top["id"] == "SC-5-2022", top["id"]

    _, top = best_current(bm25("What is the work-from-home policy?", docs))
    assert coverage("What is the work-from-home policy?", top, docs)[0] < THRESHOLD

    ranked = bm25("direct procurement limit", docs)
    assert {"SC-3-2022", "SC-7-2024"} <= {d["id"] for _, d in ranked[:3]}, "both versions should be retrieved"
    assert best_current(ranked)[1]["id"] == "SC-7-2024", "superseded circular must not be the answer"

    q = "Why was the procurement threshold raised in 2024?"
    _, top = best_current(bm25(q, docs))
    assert top["type"] == "interview", top["id"]
    assert extract(q, top).startswith("The reason the threshold was raised"), "fallback must quote the answer, not the question"

    q = "How do I apply for annual leave?"
    assert "Step 1" in extract(q, best_current(bm25(q, docs))[1])

    lib = load_library()
    assert len(lib) > 50, "research library should be chunked into passages"
    assert all(len(c["body"].split()) <= CHUNK_WORDS * 3 for c in lib), "a passage is unreasonably long"
    _, top = best_current(bm25("What are the failure points of RAG systems?", lib))
    assert top["id"].startswith("03-seven-failure-points"), top["id"]
    q = "What is the work-from-home policy?"
    assert coverage(q, best_current(bm25(q, lib))[1], lib)[0] < THRESHOLD, "common words must not pass the gate"

    print(f"selftest OK ({len(docs)} documents, {len(rules)} rules, {len(lib)} library passages)")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit()
    CORPORA, RULES = {"circulars": load_corpus(), "library": load_library()}, load_rules()
    DOCS = CORPORA["circulars"]
    port = int(os.environ.get("PORT", 8000))
    llm = {"bedrock": "Amazon Bedrock", "groq": "Groq"}.get(llm_provider(), "none (extractive fallback)")
    lib = CORPORA["library"]
    print(f"WAWASAN demo: {len(DOCS)} circulars, {len(RULES)} rules, "
          f"library {len({d['dept'] for d in lib})} files / {len(lib)} passages, LLM: {llm}")
    print(f"http://localhost:{port}")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
