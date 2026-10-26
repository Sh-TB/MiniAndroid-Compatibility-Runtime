#!/usr/bin/env python3
"""CONT-41 train — re-diagnose all 37 blank faces at the CONT-40 binary
(post R-NEW-549 RAF-streaming law). Extract deepest-unwind signatures from
crash.log, cluster into failure families (ریشه مشترک), rank by count.
Output: evidence/cont41/blank_diagnosis.json"""
import json, os, re, collections
from pathlib import Path

ROOT = "/home/z/my-project"
CENSUS = json.load(open(f"{ROOT}/evidence/cont40/batch50_census.json"))
OUT = Path(f"{ROOT}/evidence/cont41")
OUT.mkdir(parents=True, exist_ok=True)

blank = [r for r in CENSUS if (r.get("png") or {}).get("content_px", 0) < 1000]

def deep_unwinds(crash_path):
    """Return list of (exception, site, depth) keeping only the DEEPEST unwind
    per exception-type: the deepest frame in the stack is closest to the root."""
    txt = open(crash_path, errors="replace").read()
    hits = []
    for m in re.finditer(r"\[EXC-UNWIND\] (\S+?) unwound (\S+) (?:invoke_pc|pc)=(0x[0-9a-f]+) depth=(\d+)", txt):
        hits.append((m.group(1), m.group(2), m.group(3), int(m.group(4))))
    # deepest = max depth per exception class
    deepest = {}
    for exc, site, pc, d in hits:
        if exc not in deepest or d > deepest[exc][3]:
            deepest[exc] = (exc, site, pc, d)
    return hits, deepest

def first_status(report_path):
    try:
        txt = open(report_path, errors="replace").read()
    except Exception:
        return None
    m = re.search(r"\*\*Status:\*\* \*\*(\w+)\*\*", txt)
    return m.group(1) if m else None

rows = []
fam = collections.Counter()
for r in blank:
    run_dir = Path(f"{ROOT}/run/cont40_batch50/r_{r['label']}")
    crash = run_dir / "crash.log"
    hits, deepest = deep_unwinds(crash) if crash.exists() else ([], {})
    status = first_status(run_dir / "report.md")
    # family key: exception class + top site
    keys = tuple(sorted((d[0], d[1]) for d in deepest.values()))
    fam[keys] += 1
    rows.append({"label": r["label"], "status": status,
                 "n_unwind": len(hits),
                 "deepest": {k: f"{v[1]} pc={v[2]} d={v[3]}" for k, v in deepest.items()},
                 "family": str(keys[:2])})

out = {"binary": "CONT-40 5e18eb19 post-R-NEW-549",
       "n_blank": len(blank), "rows": rows,
       "families": {str(k): v for k, v in fam.most_common()}}
json.dump(out, open(OUT / "blank_diagnosis.json", "w"), indent=1)

print(f"BLANKS: {len(blank)}")
print("\n=== FAMILIES (exception+site clusters) ===")
for k, v in fam.most_common():
    print(f"  x{v:2d}  {k}")
print("\n=== PER-TITLE deepest ===")
for r in rows:
    print(f"{r['label']:20s} {r['status'] or '?':8s} n={r['n_unwind']:3d} {r['deepest']}")
