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
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
# The policy lookup table stays empty until it can be filled from verified official circulars:
# the demo never invents policy values, so every question currently goes to document search.
RULES = []
# Research library: the team's research notes plus any papers dropped into demo/library/.
# PDFs under research/ are skipped because they are generated copies of the notes.
LIBRARY_SOURCES = [(ROOT.parent / "research", {".md"}), (ROOT / "library", {".md", ".txt", ".pdf"})]
CHUNK_WORDS = 180
MIN_CHUNK_WORDS = 60
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
    # A tiny passage (a paper's title/author block) carries matching words but no content, so it would win
    # retrieval and hand the AI nothing to answer from. Fold it into the passage that follows.
    merged = []
    for c in chunks:
        if merged and len(merged[-1].split()) < MIN_CHUNK_WORDS:
            merged[-1] += "\n\n" + c
        else:
            merged.append(c)
    if len(merged) > 1 and len(merged[-1].split()) < MIN_CHUNK_WORDS:  # same for a small trailing passage
        tail = merged.pop()
        merged[-1] += "\n\n" + tail
    # Scraps like a lone figure caption carry the paper's title words but nothing to answer from.
    return [c for c in merged if len(c.split()) >= 20]


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


def pdf_title(path):
    """Embedded title metadata if it is real, else the first title-like line of page 1."""
    info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, timeout=30).stdout
    meta = re.search(r"^Title:\s*(.+)$", info, re.M)
    if meta and len(meta.group(1).strip()) > 12 and "paper title" not in meta.group(1).lower():
        return meta.group(1).strip()
    page1 = subprocess.run(["pdftotext", "-l", "1", "-enc", "UTF-8", str(path), "-"],
                           capture_output=True, text=True, timeout=60).stdout
    skip = re.compile(r"arxiv|volume|issue|journal|issn|https?://|doi|©|copyright", re.I)
    for line in (l.strip() for l in page1.splitlines()):
        if len(line.split()) >= 4 and not skip.search(line):
            return line.rstrip(":")
    return None


def load_library():
    files = sorted(p for folder, exts in LIBRARY_SOURCES if folder.exists()
                   for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in exts)
    chunks = []
    for path in files:
        raw = path.read_text(errors="replace") if path.suffix.lower() == ".md" else ""
        heading = re.search(r"^#\s+(.+)$", raw, re.M)
        title = (heading.group(1).strip() if heading
                 else pdf_title(path) if path.suffix.lower() == ".pdf"
                 else None) or path.stem.replace("-", " ").replace("_", " ")
        rel = path.relative_to(ROOT.parent).as_posix()
        source = ("Mayao Labs research notes" if rel.startswith("research/")
                  else "Published paper (PDF)" if path.suffix.lower() == ".pdf" else "Document library")
        n = 0
        for page, text in read_pages(path):
            for body in chunk(text):
                n += 1
                tf = Counter(tokenize(f"{title} {body}"))
                chunks.append({"id": f"{path.stem}#{n}", "type": "research", "title": title, "dept": source,
                               "date": None, "page": page, "superseded_by": None, "body": body, "file": rel,
                               "tf": tf, "len": sum(tf.values())})
    return chunks


# OpenAI-compatible chat endpoints: (key env var, URL, default model)
OPENAI_COMPATIBLE = {
    "deepseek": ("DEEPSEEK_API_KEY", "https://api.deepseek.com/chat/completions", "deepseek-v4-flash"),
    "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
}


def llm_provider():
    if os.environ.get("LLM_PROVIDER", "").lower() == "bedrock":
        return "bedrock"
    return next((name for name, (env, _, _) in OPENAI_COMPATIBLE.items() if os.environ.get(env)), None)


def call_llm(prompt):
    provider = llm_provider()
    if provider == "bedrock":
        return _bedrock(prompt)
    if provider:
        return _openai_compatible(provider, prompt)
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


def _openai_compatible(provider, prompt):
    env, url, default_model = OPENAI_COMPATIBLE[provider]
    url = os.environ.get("LLM_BASE_URL", url)  # any OpenAI-compatible endpoint, e.g. a self-hosted model
    key = os.environ[env]
    body = json.dumps({
        "model": os.environ.get("LLM_MODEL", default_model),
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        url, data=body,
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
    info = {k: doc.get(k) for k in ("id", "type", "title", "dept", "date", "officer", "page", "file")}
    sup = doc.get("supersedes")
    info["supersedes"] = ({"id": sup, "title": by_id[sup]["title"], "date": by_id[sup]["date"], "file": by_id[sup]["file"]}
                          if sup in by_id else None)
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
                           "superseded_by": d.get("superseded_by"), "file": d["file"], "page": d.get("page")}
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
    if generated:
        trace["llm"]["input"] = doc["body"]  # shown beside the summary so readers can check nothing was added
        # The model was told to reply with REFUSAL when the passage does not answer; surface that honestly.
        trace["llm"]["declined"] = generated.startswith(REFUSAL.rstrip("."))
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
        elif path == "/api/doc":
            # The exact indexed text of one file, passage by passage, so the viewer shows what was searched.
            wanted = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("file", [""])[0]
            parts = [d for d in DOCS if d["file"] == wanted]
            if not parts:
                return self._send(404, json.dumps({"error": "not an indexed document"}), "application/json")
            doc = {"file": wanted, "title": parts[0]["title"],
                   "passages": [{"id": d["id"], "page": d.get("page"), "text": d["body"]} for d in parts]}
            self._send(200, json.dumps(doc), "application/json")
        elif path == "/api/file":
            # Serve only files that are actually indexed: the whitelist is what makes this safe from path traversal.
            wanted = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("path", [""])[0]
            target = FILES.get(wanted)
            if not target:
                return self._send(404, "not an indexed document", "text/plain")
            ctype = "application/pdf" if target.suffix.lower() == ".pdf" else "text/plain; charset=utf-8"
            self._send(200, target.read_bytes(), ctype)
        elif path == "/api/status":
            status = {"llm": llm_provider(), "rules": len(RULES),
                      "documents": len({d["file"] for d in DOCS}), "passages": len(DOCS)}
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
        if not query:
            return self._send(400, json.dumps({"error": "empty query"}), "application/json")
        self._send(200, json.dumps(answer(query, DOCS, RULES)), "application/json")


def selftest():
    global DB_PATH
    DB_PATH = Path(os.environ.get("TMPDIR", "/tmp")) / "wawasan-selftest.db"
    lib = load_library()
    assert all((ROOT.parent / d["file"]).is_file() for d in lib), "every citation must point at a real file"
    assert len(lib) > 50, "the library should be chunked into passages"
    assert all(len(c["body"].split()) <= CHUNK_WORDS * 3 for c in lib), "a passage is unreasonably long"
    assert all(len(c["body"].split()) >= 20 for c in lib), "scraps (captions, title blocks) must not be passages"

    assert classify("What is the maximum number of failure points?")[0] == "FACTUAL"
    assert classify("Why is DDMS adoption in Malaysia still low?")[0] == "INTERPRETIVE"

    _, top = best_current(bm25("What are the failure points of RAG systems?", lib))
    assert "seven-failure-points" in top["id"], top["id"]  # the note or the Barnett et al. paper itself

    q = "What is the work-from-home policy?"
    assert coverage(q, best_current(bm25(q, lib))[1], lib)[0] < THRESHOLD, "common words must not pass the gate"

    t = answer("What is the maximum number of failure points?", lib, RULES)
    assert t["rule"] == {"matched": False, "topic": None, "previous": None} and t["retrieval"], \
        "with no verified rules, factual questions must fall through to document search"

    q = "What records management problems did Sarawak agencies have?"
    t = answer(q, lib, RULES)
    assert not t["refused"] and t["source"]["file"].startswith("research/"), t["source"]
    passage = next(d["body"] for d in lib if d["id"] == t["source"]["id"])
    assert all(p in passage for p in t["answer"].split("\n\n")), "a quoted answer must be verbatim from the cited passage"

    print(f"selftest OK ({len({d['file'] for d in lib})} files, {len(lib)} passages)")


def load_env(path):
    """KEY=VALUE lines from a local, git-ignored .env file. Real environment variables win."""
    if path.is_file():
        for line in path.read_text().splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key and not key.startswith("#"):
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def init():
    global DOCS, FILES
    DOCS = load_library()
    FILES = {d["file"]: ROOT.parent / d["file"] for d in DOCS}


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit()
    load_env(Path(os.environ.get("ENV_FILE", ROOT / ".env")))  # e.g. a shared workspace .env
    init()
    port = int(os.environ.get("PORT", 8000))
    llm = {"bedrock": "Amazon Bedrock", "deepseek": "DeepSeek", "groq": "Groq"}.get(llm_provider(), "none (extractive fallback)")
    print(f"WAWASAN demo: {len(FILES)} files / {len(DOCS)} passages, LLM: {llm}")
    print(f"http://localhost:{port}")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
