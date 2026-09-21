#!/usr/bin/env python3
"""promote_knowledge.py — S74 knowledge promotion workflow (taskbook §15).

Pipeline:  RAW -> CANDIDATE -> RESEARCHED -> OBSERVED -> TESTED -> VERIFIED
           (+ SUPERSEDED / REJECTED terminal states)

The tool NEVER blindly marks knowledge verified:
- promotion moves ONE status step per invocation;
- VERIFIED requires --test AND --evidence AND --source (provenance);
- every transition is appended to docs/knowledge/PROMOTION_JOURNAL.jsonl
  (append-only audit trail; raw research files are never modified or deleted,
  taskbook §16).

Usage:
  python3 tools/promote_knowledge.py list
  python3 tools/promote_knowledge.py add --id LAW-MyLaw --title "..." \
      --domain jvm --scope generic --raw-file docs/history/some_research.md \
      --statement "one-line statement of law"
  python3 tools/promote_knowledge.py promote --id LAW-MyLaw --to TESTED \
      --test "battery stage x" --evidence docs/evidence/... --source "AOSP Foo.java:123"
  python3 tools/promote_knowledge.py supersede --id LAW-Old --by LAW-New --reason "..."
  python3 tools/promote_knowledge.py reject --id LAW-X --reason "..."
"""
import argparse, json, os, sys, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LAWS_DIR = os.path.join(ROOT, "docs/knowledge/laws")
JOURNAL = os.path.join(ROOT, "docs/knowledge/PROMOTION_JOURNAL.jsonl")

ORDER = ["RAW", "CANDIDATE", "RESEARCHED", "OBSERVED", "TESTED", "VERIFIED"]


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_law(law_id):
    p = os.path.join(LAWS_DIR, f"{law_id}.json")
    if not os.path.exists(p):
        sys.exit(f"FAIL: no such knowledge record: {law_id}")
    return json.load(open(p)), p


def save_law(rec, p):
    with open(p, "w") as f:
        json.dump(rec, f, indent=1)
        f.write("\n")


def journal(entry):
    os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
    with open(JOURNAL, "a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def cmd_list(_):
    laws = []
    for fn in sorted(os.listdir(LAWS_DIR)):
        if fn.endswith(".json"):
            r = json.load(open(os.path.join(LAWS_DIR, fn)))
            laws.append((r["knowledge_id"], r["status"], r.get("scope", "?"), r.get("title", "")[:70]))
    w = max(len(x[0]) for x in laws)
    try:
        for lid, st, sc, title in laws:
            print(f"{lid:<{w}}  {st:<11} {sc:<8} {title}")
        print(f"\n{len(laws)} records; canonical = VERIFIED only")
    except BrokenPipeError:
        pass


def cmd_add(a):
    p = os.path.join(LAWS_DIR, f"{a.id}.json")
    if os.path.exists(p):
        sys.exit(f"FAIL: {a.id} already exists")
    raw_ref = a.raw_file
    if raw_ref and not os.path.exists(os.path.join(ROOT, raw_ref)):
        sys.exit(f"FAIL: raw file not found: {raw_ref}")
    rec = {
        "record_type": "knowledge_record", "schema_version": 1,
        "knowledge_id": a.id, "title": a.title, "domain": a.domain,
        "scope": a.scope or "generic",
        "statement": a.statement or "",
        "status": "CANDIDATE",
        "source": {"origin": None, "file": raw_ref, "raw_preserved": True},
        "test": None, "consumers": [], "issues": [], "capabilities": [],
        "first_discovered": now()[:10], "last_verified": None,
        "promotion": {"pipeline": "RAW->CANDIDATE (add)", "note": "raw research file preserved in place; canonical record links back (taskbook §16)"},
    }
    save_law(rec, p)
    journal({"ts": now(), "id": a.id, "action": "add", "from": None, "to": "CANDIDATE", "raw_file": raw_ref})
    print(f"ADDED {a.id} as CANDIDATE (raw provenance: {raw_ref or 'none — REQUIRED before VERIFIED'})")


def cmd_promote(a):
    rec, p = load_law(a.id)
    cur = rec["status"]
    if cur not in ORDER:
        sys.exit(f"FAIL: {a.id} is terminal ({cur}); use supersede/reject")
    if a.to not in ORDER:
        sys.exit(f"FAIL: target {a.to} is not a pipeline state")
    if ORDER.index(a.to) != ORDER.index(cur) + 1:
        sys.exit(f"FAIL: single-step law violated: {cur} -> {a.to} (pipeline: {' -> '.join(ORDER)})")
    if a.to == "VERIFIED":
        missing = [n for n, v in (("--test", a.test), ("--evidence", a.evidence), ("--source", a.source)) if not v]
        if missing:
            sys.exit(f"FAIL: VERIFIED requires {', '.join(missing)} (never blindly verified, taskbook §15)")
        for v, label in ((a.evidence, "evidence"), (a.source, "source")):
            if label == "evidence" and not os.path.exists(os.path.join(ROOT, v.split(" ")[0])):
                sys.exit(f"FAIL: evidence path does not exist: {v}")
        rec["source"]["origin"] = a.source
        rec["test"] = a.test
        rec["status"] = "VERIFIED"
        rec["last_verified"] = now()[:10]
    else:
        if a.test: rec["test"] = a.test
        if a.evidence: rec.setdefault("evidence_refs", []).append(a.evidence)
        if a.source: rec["source"]["origin"] = a.source
        rec["status"] = a.to
    journal({"ts": now(), "id": a.id, "action": "promote", "from": cur, "to": a.to,
             "test": a.test, "evidence": a.evidence, "source": a.source})
    save_law(rec, p)
    print(f"PROMOTED {a.id}: {cur} -> {a.to}")


def cmd_supersede(a):
    rec, p = load_law(a.id)
    if not os.path.exists(os.path.join(LAWS_DIR, f"{a.by}.json")):
        sys.exit(f"FAIL: superseding record {a.by} does not exist")
    cur = rec["status"]
    rec["status"] = "SUPERSEDED"
    rec["superseded_by"] = a.by
    rec["superseded_reason"] = a.reason
    journal({"ts": now(), "id": a.id, "action": "supersede", "from": cur, "to": "SUPERSEDED", "by": a.by, "reason": a.reason})
    save_law(rec, p)
    print(f"SUPERSEDED {a.id} -> by {a.by} (history preserved, taskbook §68)")


def cmd_reject(a):
    rec, p = load_law(a.id)
    cur = rec["status"]
    rec["status"] = "REJECTED"
    rec["rejection_reason"] = a.reason
    journal({"ts": now(), "id": a.id, "action": "reject", "from": cur, "to": "REJECTED", "reason": a.reason})
    save_law(rec, p)
    print(f"REJECTED {a.id} (reason preserved)")


def main():
    ap = argparse.ArgumentParser(description="S74 knowledge promotion (never blindly verifies)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    pa = sub.add_parser("add")
    pa.add_argument("--id", required=True); pa.add_argument("--title", required=True)
    pa.add_argument("--domain", required=True); pa.add_argument("--scope", default="generic")
    pa.add_argument("--raw-file", default=None); pa.add_argument("--statement", default=None)
    pp = sub.add_parser("promote")
    pp.add_argument("--id", required=True); pp.add_argument("--to", required=True)
    pp.add_argument("--test", default=None); pp.add_argument("--evidence", default=None)
    pp.add_argument("--source", default=None)
    ps = sub.add_parser("supersede")
    ps.add_argument("--id", required=True); ps.add_argument("--by", required=True); ps.add_argument("--reason", required=True)
    pr = sub.add_parser("reject")
    pr.add_argument("--id", required=True); pr.add_argument("--reason", required=True)
    a = ap.parse_args()
    {"list": cmd_list, "add": cmd_add, "promote": cmd_promote,
     "supersede": cmd_supersede, "reject": cmd_reject}[a.cmd](a)


if __name__ == "__main__":
    main()
