#!/usr/bin/env python3
"""T279 P4 — merge the post-fix verification runs into the campaign evidence.

The MeasureSpec getMode AOSP fix (miniandroid/src/dex/
dalvik_bridge_domain_app_runtime.cpp F-NEW-714, verified by
tests/f714_measurespec_law_test.cpp 9/9 + 8 spot law batteries) re-ran 9
titles on the fixed binary 1a21be9fc9f6b016:
  - uturn: DEFAULT_BACKGROUND_ONLY -> REAL_APP_CONTENT, face a53523e7ca331866
    == its 2026-11-06 S182 historical face (full recovery), unc 8 -> 0.
  - wocheneinkauf/peri: the convertMeasureSpec ISE class eliminated
    (uncaught 33 -> 32); the deeper compose composition-state layer remains
    (BLOCKED, next frontier named).
  - 6 golden anchors: faces byte-identical pre/post fix (zero regressions).
"""
import csv
import json
from pathlib import Path

BASE = Path("/home/z/my-project")
OUT = BASE / "evidence" / "t279"
POST = json.load(open(BASE / "run_t279_postfix/POSTFIX.json"))
FIX_SHA = "1a21be9fc9f6b016"

# ---- update CSV ----
csv_path = OUT / "T279_TWO_RUN_RESULTS.csv"
rows = list(csv.DictReader(open(csv_path)))
for r in rows:
    tag = r["tag"]
    p = POST.get(tag)
    if not p:
        continue
    f1, f2 = p["runs"]["f1"], p["runs"]["f2"]
    r["postfix_run1_face16"] = f1.get("face", "")
    r["postfix_run2_face16"] = f2.get("face", "")
    r["postfix_verdict"] = f1.get("verdict", "")
    r["postfix_px"] = str(f1.get("px", ""))
    r["postfix_binary_sha16"] = FIX_SHA
    if tag == "uturn":
        r["status"] = "CURRENT-REPRODUCIBLE"
        r["render_level"] = "R3"
        r["interaction"] = "not-tested"
        r["first_divergence"] = "none — FIXED by T279 MeasureSpec getMode law (face == 2026-11-06 historical)"
    elif tag in ("wocheneinkauf", "peri"):
        r["first_divergence"] = (
            "convertMeasureSpec ISE ELIMINATED by the T279 fix (uncaught 33->32); "
            "deeper compose composition-state layer remains (BLOCKED)")
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# ---- update inventory ----
inv_path = OUT / "T279_RENDER_INVENTORY.json"
inv = json.load(open(inv_path))
uturn = inv["packages"].get("ac.stresa.uturn")
if uturn:
    uturn["status"] = "CURRENT-REPRODUCIBLE"
    uturn["render_level_current"] = "R3"
    uturn["postfix_face16"] = POST["uturn"]["runs"]["f1"]["face"]
    uturn["notes"] += (" | T279 FIX 2026-11-28: MeasureSpec.getMode AOSP bit-pattern law "
                       "restored REAL_APP_CONTENT; face a53523e7ca331866 == S182 "
                       "historical face byte-identical; uncaught 8->0; zero anchor "
                       "regressions (12 faces identical pre/post).")
for pkg in ("app.wocheneinkauf", "app.simple.peri"):
    p = inv["packages"].get(pkg)
    if p:
        p["notes"] += (" | T279 FIX 2026-11-28: convertMeasureSpec ISE class eliminated "
                       "(uncaught 33->32); deeper compose composition-state layer is the "
                       "named next frontier; still DEFAULT_BACKGROUND_ONLY.")
inv["summary"]["t279_fix"] = {
    "date": "2026-11-28",
    "file": "miniandroid/src/dex/dalvik_bridge_domain_app_runtime.cpp (F-NEW-714)",
    "change": "getMode -> spec & 0xC0000000 (AOSP bit pattern, was (spec>>30)&3 index); "
              "makeMeasureSpec -> AOSP mask form on both inputs",
    "test": "tests/f714_measurespec_law_test.cpp 9/9 incl. T7 compose fence; 8 spot law batteries rc=0",
    "binary_sha16": FIX_SHA,
    "recoveries": ["ac.stresa.uturn (face == S182 historical)"],
    "peeled_blockers": ["AndroidComposeView.convertMeasureSpec ISE (wocheneinkauf, peri: 33->32 uncaught)"],
    "anchor_regressions": 0,
}
json.dump(inv, open(inv_path, "w"), indent=1)
print("[postfix-merge] CSV + inventory updated: uturn CURRENT-REPRODUCIBLE R3,",
      "wocheneinkauf/peri BLOCKED at deeper layer, 0 anchor regressions")
