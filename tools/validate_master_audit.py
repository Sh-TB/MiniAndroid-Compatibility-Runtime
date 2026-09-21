#!/usr/bin/env python3
# S74-FINAL §27 validator — enforces ledger consistency; fails on false completions.
import json, os, re, sys

ROOT = "/home/z/my-project"
LEDGER = os.path.join(ROOT, "docs/audit/master_audit.json")
STATUSES = {"DONE","IMPLEMENTED","TESTED","OBSERVED","PARTIAL","BLOCKED","PENDING",
            "UNVERIFIED","SUPERSEDED","DUPLICATE","NOT_APPLICABLE","CONFLICT"}

fail=[]
def chk(cond, msg):
    if not cond: fail.append(msg)

d=json.load(open(LEDGER))
rows=d["rows"]; ids=[r["id"] for r in rows]

# 1. unique IDs, non-empty source/status
chk(len(ids)==len(set(ids)), "duplicate requirement IDs present")
for r in rows:
    chk(r["status"] in STATUSES, f"{r['id']}: illegal status {r['status']}")
    chk(bool(r["source"].strip()), f"{r['id']}: empty source")
    chk(bool(r["requirement"].strip()), f"{r['id']}: empty requirement")

# 2. counts
const=[r for r in rows if r["id"].startswith("CONST-")]
chk(len(const)==169, f"CONST count {len(const)} != 169")
chk(len([r for r in rows if r["id"].startswith("APP-")])==14, "app rows != 14")
chk(d["counts"]["ITEM75_CLAIMED"]==75, "ITEM75_CLAIMED must record the claimed 75")

# 3. DONE/TESTED/OBSERVED need matching evidence class
for r in rows:
    if r["status"]=="DONE":
        chk(bool(r["evidence"]) or bool(r["execution"]), f"{r['id']}: DONE without evidence")
    if r["status"]=="TESTED":
        chk(bool(r["tests"]), f"{r['id']}: TESTED without test reference")
    if r["status"]=="OBSERVED":
        chk(bool(r["execution"]) or bool(r["evidence"]), f"{r['id']}: OBSERVED without execution/evidence")

# 4. HUMAN_VISIBLE app claims need nontrivial frames
for r in rows:
    if r["id"].startswith("APP-"):
        hv=r.get("human_visible"); nt=r.get("nontrivial_frames",0)
        if hv=="HUMAN_VISIBLE":
            chk(nt>0 or "GOLDEN_FIXTURE" in r.get("scope",""),
                f"{r['id']}: HUMAN_VISIBLE without nontrivial frames (blank/missing = FALSE_HUMAN_VISIBLE)")
        if hv=="HUMAN_VISIBLE" and "GOLDEN_FIXTURE" in r.get("scope",""):
            chk("GOLDEN_FIXTURE" in (r["gap"] or ""), f"{r['id']}: fixture-scope HV must carry scope gap marker")
        chk(bool(r["issues"]), f"{r['id']}: app row not linked to its [EXEC] issue")

# 5. persistence PASS requires close/reopen
for r in rows:
    if r["id"].startswith("APP-"):
        p=(r.get("persistence") or "").upper()
        if "PASS" in p and "PROVEN" in p or p.startswith("OBSERVED"):
            chk(("reopen" in r["execution"][0] if r["execution"] else False) or
                "session.json" in (r["execution"][0] if r["execution"] else ""),
                f"{r['id']}: persistence PASS without close/reopen evidence")

# 6. TOOL USED requires consumer
for r in rows:
    if r["id"].startswith("TOOL-") and r.get("verdict")=="USED":
        chk(bool(r["consumer"]), f"{r['id']}: USED without consumer chain")

# 7. LAW VERIFIED requires source+test
for r in rows:
    if r["id"].startswith("KNOW-") and r["status"]=="OBSERVED" and r.get("verdict")=="USED_BY_EXECUTION":
        chk(bool(r["tests"]) or bool(r["evidence"]), f"{r['id']}: USED_BY_EXECUTION without test/evidence")

# 8. MD/JSON parity
md=open(os.path.join(ROOT,"docs/audit/MASTER_CHECKLIST.md")).read()
md_ids=set(re.findall(r"^\| ((?:CAM|CONST|ITEM75|REQ-HIST|APP|TOOL|KNOW|ISSUE|CRITICAL)-[A-Z0-9\-]+) \|", md, re.M))
for i in set(ids):
    if i not in md_ids: fail.append(f"MD missing row {i}")
for i in md_ids:
    if i not in set(ids): fail.append(f"MD has unknown row {i}")

if fail:
    print(f"AUDIT LEDGER VALIDATION: FAIL ({len(fail)} problems)")
    for m in fail[:40]: print(" -", m)
    sys.exit(1)
from collections import Counter
print(f"AUDIT LEDGER VALIDATION: PASS — {len(rows)} rows, statuses: {dict(Counter(r['status'] for r in rows))}")
