#!/usr/bin/env python3
"""cont81_repeat_battery.py — 3-run repeatability over CONT-78 claimed
successes (REAL_APP_CONTENT / INTERACTIVE_CONTENT_VERIFIED rows).
Writes evidence/cont81/repeatability.json. Does NOT overwrite batch rows.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cont81_corpus_runner import (run_repeat, classify_v2, ROOT)

OUT = f"{ROOT}/run/cont81/corpus_cont81_batch1"
BATCH = json.load(open(f"{OUT}/result.json"))
CLAIMED = [r for r in BATCH["rows"]
           if r.get("verdict_v2") in ("REAL_APP_CONTENT",
                                      "INTERACTIVE_CONTENT_VERIFIED")]

store = f"{ROOT}/run/cont81/repeat_store"
os.makedirs(store, exist_ok=True)
rows = []
for r in CLAIMED:
    apk = r["apk_path"]
    pkg = r["package"]
    rr = run_repeat(apk, f"{ROOT}/run/cont81/repeat_out", 5, 90, store,
                    3)
    row = {"package": pkg, "verdict_v2": rr["verdict_v2"],
           "repeat_runs": rr["repeat_runs"],
           "repeat_face_stable": rr["repeat_face_stable"],
           "repeat_all_same_verdict": rr["repeat_all_same_verdict"],
           "repeat_verdicts": rr["repeat_verdicts"],
           "faces": sorted({rr.get("screenshot_sha256", "")[:16]})}
    rows.append(row)
    print(f"  {pkg}: {row['verdict_v2']} stable={row['repeat_face_stable']} "
          f"faces={row['faces']}")

n_stable = sum(1 for r in rows if r["repeat_face_stable"])
out = {"claimed": len(rows), "face_stable_3run": n_stable, "rows": rows}
os.makedirs(f"{ROOT}/evidence/cont81", exist_ok=True)
json.dump(out, open(f"{ROOT}/evidence/cont81/repeatability.json", "w"),
          indent=1)
print(f"REPEATABILITY: {n_stable}/{len(rows)} 3-run face-stable")
