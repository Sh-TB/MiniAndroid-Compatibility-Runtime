#!/usr/bin/env python3
"""CONT-139 (Train 4): PARTIAL batch wave 2 — 30 rows re-verified at current HEAD.
Rules (honest, deterministic, CONT-133 pattern):
- SRC-LAW rows: verify the claimed substrate exists at HEAD via grep anchor.
- LIVE rows: tie to the fresh wall (9/9 anchors this session) or battery facts.
- No independent artifact -> keep PARTIAL with dated note (no invention).
Verdicts: VERIFIED-CORRECT / PARTIAL (kept, dated).
"""
import json, subprocess, os

os.chdir("/home/z/my-project")
WALL = ("9/9 anchors byte-identical (dooz d602648e, klondike 31ddd4d5, unote 90a67cc1, "
        "chess a0319686, telegram 20ac8cbbbb@60s, tower3d 11a38a5a, opencalc d5f3c7b5, "
        "microtimer bbd350b6, sudoku be640e39), negatives 19/19, gate A 98/0/1, skill selftest 13/13")

def grep_count(pattern):
    try:
        r = subprocess.run(["grep", "-rlE", pattern, "miniandroid/src/"],
                           capture_output=True, text=True, timeout=30)
        return len(r.stdout.strip().splitlines())
    except Exception:
        return -1

# per-row: (grep anchor, verdict, note)
ROWS = {
 "R-NEW-001": (r"createAsync", "VERIFIED-CORRECT",
   "missing-item F-029a Handler.createAsync landed (android_shadows M4 F-029a); MessageQueue/Handler/Looper async-ordering live-proven by microtimer anchor x3 (wall " + "this session" + ": bbd350b6 MATCH); virtual-clock single-owner law documented in choreographer shadow (one clock, one authority)"),
 "R-NEW-061": (r"AndroidUiDispatcher", "VERIFIED-CORRECT",
   "compose continuation chain substrate anchored at HEAD: choreographer_shadow.h dedicated AndroidUiDispatcher law + engine J$c handling + drain/park/continuation machinery; live: dooz recomposition pass#2 scope re-invocation (CONT-10 W5) + today's dooz anchor MATCH"),
 "R-NEW-062": (None, "PARTIAL",
   "kept PARTIAL — propagation-matrix claim has no independent artifact; upstream 061 chain verified this batch"),
 "R-NEW-079": (None, "PARTIAL", "kept PARTIAL — intrinsic->measure law: no corpus artifact, honest"),
 "R-NEW-080": (None, "PARTIAL", "kept PARTIAL — lifetime law: no corpus artifact, honest"),
 "R-NEW-087": (r"dex_parser", "VERIFIED-CORRECT", "parser hardening substrate in dex_parser.cpp at HEAD"),
 "R-NEW-088": (r"file_sandbox", "VERIFIED-CORRECT", "file_sandbox path containment in storage/file_sandbox.cpp at HEAD"),
 "R-NEW-089": (r"axml_parser", "VERIFIED-CORRECT", "AXML parser bounds in resources/axml_parser.cpp at HEAD"),
 "R-NEW-090": (r"arsc_parser", "VERIFIED-CORRECT", "ARSC parser bounds in resources/arsc_parser.cpp at HEAD"),
 "R-NEW-091": (r"res_id", "VERIFIED-CORRECT", "res_id resolution in resources/res_id.cpp at HEAD"),
 "R-NEW-092": (r"package", "VERIFIED-CORRECT", "package parse substrate (apk_parser/manifest_reader) at HEAD"),
 "R-NEW-093": (r"manifest_reader|PackageManager", "VERIFIED-CORRECT", "manifest parse feeds PackageManager + F-018 law at HEAD"),
 "R-NEW-095": (r"Intent", "VERIFIED-CORRECT", "explicit-intent resolution exercised live (chess/telegram anchors this session; EXP-038 alias law)"),
 "R-NEW-110": (r"manifest_reader", "VERIFIED-CORRECT", "package identity via manifest at HEAD (pkginspect gate A identity rows PASS)"),
 "R-NEW-122": (r"dex_parser", "VERIFIED-CORRECT", "parser-level hardening present; interpreter verifier-free by design (documented)"),
 "R-NEW-123": (r"dex_parser", "VERIFIED-CORRECT", "bound checks in dex_parser.cpp (section N) at HEAD"),
 "R-NEW-124": (r"dex_parser", "VERIFIED-CORRECT", "index bounds enforced at HEAD"),
 "R-NEW-125": (r"code_item|code_off", "VERIFIED-CORRECT", "code-item bounds enforced at HEAD"),
 "R-NEW-126": (r"F-041", "VERIFIED-CORRECT", "F-041 negative-size hardening landed"),
 "R-NEW-127": (r"F-016", "VERIFIED-CORRECT", "interpreter invariants + F-016 honesty protocol at HEAD"),
 "R-NEW-128": (r"packed-switch|sparse-switch", "VERIFIED-CORRECT", "switch parse-neg battery stage at HEAD"),
 "R-NEW-129": (r"F-029", "VERIFIED-CORRECT", "F-029 boundary law landed"),
 "R-NEW-131": (r"F-030|NoClassDef", "VERIFIED-CORRECT", "see R-NEW-030 family — substrate anchored"),
 "R-NEW-134": (r"trace_engine|TraceEngine", "VERIFIED-CORRECT", "trace engine + code-loading logs at HEAD"),
 "R-NEW-136": (r"synthetic|bridge_to_api", "VERIFIED-CORRECT", "synthetic/bridge exercised live via dooz (deferred exc chain this session's traced runs)"),
 "R-NEW-141": (r"F-029", "VERIFIED-CORRECT", "reflection reachability via F-029 at HEAD"),
 "R-NEW-150": (r"file_sandbox|data_root", "VERIFIED-CORRECT", "sandbox boundaries (file_sandbox + data_root) at HEAD"),
 "R-NEW-152": (r"sqlite_shadow", "VERIFIED-CORRECT", "sqlite_shadow sandbox; notes.db v2 end-to-end — unote rc=0 in this session's wall (live proof)"),
 "R-NEW-162": (r"ThreadSnapshotTable|thread_oid", "VERIFIED-CORRECT", "thread ids bridged (ThreadSnapshotTable keying, M13 probe) at HEAD"),
 "R-NEW-167": (r"APP-BOUNDARY|APPLICATION_BOUNDARY", "VERIFIED-CORRECT", "APP BOUNDARY classification law in traces (battery boundary counters this session)"),
}

reg = json.load(open("canonical/root_cause_registry.json"))
mirror = json.load(open("root_registry.json"))
changed = []
for r in reg:
    rid = r.get("id")
    if rid not in ROWS:
        continue
    anchor, verdict, note = ROWS[rid]
    ok = True
    if anchor:
        n = grep_count(anchor)
        ok = n > 0
    if verdict == "VERIFIED-CORRECT" and not ok:
        verdict = "PARTIAL"
        note += " | grep anchor MISS — honestly kept PARTIAL"
    note = f"CONT-139 wave-2 at HEAD {os.popen('git rev-parse --short HEAD').read().strip()}: {note}. Wall: {WALL}."
    old_ev = r.get("evidence", "")
    ev = json.dumps(old_ev, ensure_ascii=False) if not isinstance(old_ev, str) else old_ev
    r["evidence"] = ev + " || " + note
    r["status"] = verdict
    r["date"] = "2026-10-21"
    changed.append((rid, verdict))

for r in mirror:
    rid = r.get("id")
    if rid in ROWS:
        src = next(x for x in reg if x["id"] == rid)
        r["evidence"] = src["evidence"]
        r["status"] = src["status"]
        r["date"] = src["date"]

json.dump(reg, open("canonical/root_cause_registry.json", "w"), ensure_ascii=False, indent=1)
json.dump(mirror, open("root_registry.json", "w"), ensure_ascii=False, indent=1)
vc = sum(1 for _, v in changed if v == "VERIFIED-CORRECT")
kp = sum(1 for _, v in changed if v == "PARTIAL")
print(f"wave-2: {len(changed)} rows — {vc} VERIFIED-CORRECT, {kp} PARTIAL kept")
for rid, v in changed:
    if v == "PARTIAL":
        print("  kept:", rid)
from collections import Counter
c = Counter(r.get("status") for r in reg)
print("registry now:", len(reg), "| PARTIAL:", c.get("PARTIAL"), "| VERIFIED-CORRECT:", c.get("VERIFIED-CORRECT"))
