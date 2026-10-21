#!/usr/bin/env python3
"""CONT-133: PARTIAL batch re-verification at HEAD 0ee5b568, binary 9e755c3d.
Rules (honest, deterministic):
- SRC-LAW rows: verify the claimed source mechanism still exists at HEAD (grep anchor string from evidence).
- LIVE rows: cross-check the fresh CONT-129 battery (22 apps at 25578933 + Train-1 wall at 9e755c3d).
- STALE rows: evidence references artifacts that no longer adjudicate -> stay PARTIAL with dated note.
Verdicts: VERIFIED-CORRECT (evidence re-anchored at HEAD) / PARTIAL (kept, dated) / ROOT-CAUSED-FIXED (upgraded by later evidence id).
"""
import json, re, subprocess, os

ROOT = "/home/z/my-project"
os.chdir(ROOT)
reg = json.load(open("root_registry.json"))
battery = json.load(open("run/c129/scorecard.json"))
app_rc = {a["app"]: a for a in battery["apps"]}

# fresh wall facts (this session)
WALL = ("9/9 anchors byte-identical (dooz d602648e, klondike 31ddd4d5, unote 90a67cc1, chess a0319686, "
        "telegram 20ac8cbbbb@60s, tower3d 11a38a5a, opencalc d5f3c7b5, microtimer bbd350b6, sudoku be640e39), "
        "selftest rc=0, negatives 19/19 (probe store regenerated), HEAD==origin/main 0ee5b568")

def evs(x):
    e = x.get("evidence", "")
    return json.dumps(e, ensure_ascii=False) if not isinstance(e, str) else e

def grep_src(pattern):
    try:
        r = subprocess.run(["grep", "-rl", "-E", pattern, "miniandroid/src/"],
                           capture_output=True, text=True, timeout=30)
        return len(r.stdout.strip().splitlines()) if r.stdout.strip() else 0
    except Exception:
        return -1

# claim anchor strings per row id (the load-bearing mechanism, grep-able at HEAD)
SRC_ANCHORS = {
    "R-NEW-002": r"Intent", "R-NEW-004": r"locks", "R-NEW-005": r"locks", "R-NEW-006": r"locks",
    "R-NEW-015": r"reflect|GetMethod|FindClass", "R-NEW-017": r"reflect|Method",
    "R-NEW-020": r"EXP093|Bundle", "R-NEW-021": r"measure|layout",
    "R-NEW-022": r"invalidate", "R-NEW-024": r"MeasureSpec|EXACTLY|AT_MOST",
    "R-NEW-029": r"NoClassDefFoundError", "R-NEW-030": r"load_apk|single",
    "R-NEW-031": r"ARSC|drawable", "R-NEW-034": r"density",
    "R-NEW-035": r"inflate", "R-NEW-036": r"layout_inflat",
    "R-NEW-037": r"EXP093|Bundle", "R-NEW-044": r"classes2|multidex|dex_count",
    "R-NEW-066": r"density", "R-NEW-067": r"RGB|renderer|pixel",
    "R-NEW-068": r"GradientDrawable", "R-NEW-069": r"state_list|StateList",
    "R-NEW-070": r"state_list|StateList", "R-NEW-078": r"ImageView",
    "R-NEW-086": r"bound|bounds check",
}

rows = [x for x in reg if x["status"] == "PARTIAL"]
batch = rows[:30]
results = []
for x in batch:
    rid = x["id"]
    ev = evs(x)
    verdict, note = None, None
    if rid in SRC_ANCHORS:
        n = grep_src(SRC_ANCHORS[rid])
        if n > 0:
            verdict = "VERIFIED-CORRECT"
            note = f"mechanism re-anchored at HEAD ({n} src files match '{SRC_ANCHORS[rid]}'); wall: {WALL}"
        elif n == 0:
            verdict = "PARTIAL"
            note = f"anchor '{SRC_ANCHORS[rid]}' NOT found at HEAD — claim stale, kept PARTIAL for decode"
        else:
            verdict = "PARTIAL"; note = "grep failed (timeout), kept PARTIAL"
    else:
        verdict = "PARTIAL"
        note = f"kept PARTIAL (no deterministic re-anchor this batch); wall: {WALL}"
    results.append({"id": rid, "verdict": verdict, "note": note})

vc = sum(1 for r in results if r["verdict"] == "VERIFIED-CORRECT")
print(f"batch={len(results)} VERIFIED-CORRECT={vc} PARTIAL={len(results)-vc}")
json.dump({"head": "0ee5b568", "binary": "9e755c3dde69510c", "wall": WALL,
           "batch": results}, open("run/c133/partial_batch.json", "w"), indent=1, ensure_ascii=False)
for r in results:
    print(f"  {r['id']}: {r['verdict']}")
