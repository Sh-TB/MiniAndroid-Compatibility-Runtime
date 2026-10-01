#!/usr/bin/env python3
"""s131_close_input_frontier.py — close the INPUT-audit registry outcomes.

Evidence-based registry updates per docs/REUSE_AUDIT_INPUT.md:
  R-NEW-251 (hit-test law)      -> SUPERSEDED-BY-R-NEW-424 (the S128 reverse
                                   draw-order walk IS the AOSP hit-test law;
                                   battery 124-stage + calc chain evidence)
  R-NEW-252 (ordering matrix)   -> SUPERSEDED-BY-R-NEW-424 (same walk; ttt
                                   byte-identical b5a7a35d + calc taps x3)
  R-NEW-191/253                 -> remain PARTIAL (on-demand AOSP-anchored
                                   laws; no measured APK case yet)
Idempotent: safe to re-run.
"""
import json

P = "/home/z/my-project/root_registry.json"
doc = json.load(open(P))
roots = doc["roots"] if isinstance(doc, dict) and "roots" in doc else doc

UPD = {
    "R-NEW-251": {
        "status": "SUPERSEDED-BY-EVIDENCE",
        "evidence": ("R-NEW-424 reverse draw-order walk implements the AOSP "
                     "isTransformedTouchPointInView hit-test law (S128 chain "
                     "max=5 + S131 audit); battery 124-stage ALL PASS"),
        "next": "superseded by R-NEW-424",
    },
    "R-NEW-252": {
        "status": "SUPERSEDED-BY-EVIDENCE",
        "evidence": ("ordering matrix = R-NEW-424 walk law; ttt byte-identical "
                     "b5a7a35d, calc goldens a169346e x3, battery 124-stage "
                     "ALL PASS (S131 audit)"),
        "next": "superseded by R-NEW-424",
    },
}
n = 0
for r in roots:
    u = UPD.get(r.get("id"))
    if u and r.get("status") != u["status"]:
        r.update(u)
        n += 1
json.dump(doc, open(P, "w"), indent=1)
print(f"updated {n} roots: R-NEW-251/252 -> SUPERSEDED-BY-EVIDENCE (R-NEW-424)")
