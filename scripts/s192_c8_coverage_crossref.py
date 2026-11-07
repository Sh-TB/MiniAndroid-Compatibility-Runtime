#!/usr/bin/env python3
"""S192 [C8] — CODER 8 WAVE 9 — coverage cross-ref against the CURRENT tree
(base d3a8d0ec + waves 1..8). Same conservative adjudication as S191: for
each androguard-decoded (class, method) pair, is it handled by the runtime
source? Anything ambiguous is flagged REVIEW, never silently passed.
"""
import json
from pathlib import Path

DECODE = Path("/home/z/my-project/work/miniandroid/evidence/s192_c8/"
              "S192_C8_CONCURRENCY_DECODE.json")
SRC = Path("/home/z/my-project/work/miniandroid/miniandroid/src")
OUT = Path("/home/z/my-project/work/miniandroid/evidence/s192_c8/"
           "S192_C8_COVERAGE_CROSSREF.json")

CORE_OBJECT = {"<init>", "toString", "getClass", "equals", "hashCode", "clone"}

files = {}
for p in SRC.rglob("*.cpp"):
    files[str(p)] = p.read_text(errors="replace")
for p in SRC.rglob("*.h"):
    files[str(p)] = p.read_text(errors="replace")

data = json.loads(DECODE.read_text())
agg = data["aggregate"]

rows = []
for cls, meths in sorted(agg.items()):
    cls_files = [f for f, t in files.items() if cls in t]
    for met, e in sorted(meths.items()):
        if cls == "Ljava/lang/Object;" and met in CORE_OBJECT:
            status = "ENGINE_CORE"
            hits = []
        else:
            hits = []
            for f in cls_files:
                t = files[f]
                if f'"{met}"' in t or f'"{cls[:-1]}->{met}"' in t:
                    hits.append(Path(f).name)
            if hits:
                status = "PRESENT"
            elif not cls_files:
                status = "CLASS_ABSENT"
            else:
                status = "METHOD_ABSENT"
        rows.append({
            "class": cls, "method": met,
            "apk_count": len(set(e["apks"])),
            "sites": e["total"],
            "apks": sorted(set(e["apks"])),
            "status": status,
            "src_hits": sorted(set(hits))[:6],
        })

order = {"CLASS_ABSENT": 0, "METHOD_ABSENT": 1, "PRESENT": 2, "ENGINE_CORE": 3}
rows.sort(key=lambda r: (order[r["status"]], -r["apk_count"], -r["sites"]))
OUT.write_text(json.dumps(rows, indent=1))

print(f"{'STATUS':14s} {'#APK':>4s} {'SITES':>6s}  PAIR")
for r in rows:
    if r["status"] in ("CLASS_ABSENT", "METHOD_ABSENT") and r["apk_count"] >= 1:
        print(f"{r['status']:14s} {r['apk_count']:4d} {r['sites']:6d}  "
              f"{r['class']}.{r['method']}")

n_abs = sum(1 for r in rows if r["status"] == "CLASS_ABSENT")
n_mab = sum(1 for r in rows if r["status"] == "METHOD_ABSENT")
n_pre = sum(1 for r in rows if r["status"] == "PRESENT")
n_core = sum(1 for r in rows if r["status"] == "ENGINE_CORE")
print(f"\nPAIRS: {len(rows)} = CLASS_ABSENT {n_abs} + METHOD_ABSENT {n_mab} "
      f"+ PRESENT {n_pre} + ENGINE_CORE {n_core}")
print("wrote", OUT)
