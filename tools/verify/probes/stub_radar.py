"""Stub Radar (brief §17): inventory POTENTIAL GAPS in the runtime source.
Output = DISCOVERY hints, never BUG verdicts; every hit needs context review."""
import json, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))               # <repo>/tools/verify/probes
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # repo root
SRC = os.path.join(REPO, "miniandroid", "src")
PATTERNS = [
    ("TODO", r"//\s*TODO"), ("FIXME", r"//\s*FIXME"),
    ("UNIMPLEMENTED", r"UNIMPLEMENTED"),
    ("UnsupportedOperationException", r"UnsupportedOperationException"),
    ("return null", r"return\s+nullptr\s*;"),
    ("return false fallback", r"return\s+false\s*;\s*(//.*)?$"),
    ("return 0 fallback", r"return\s+0\s*;\s*(//.*)?$"),
    ("REC-MISS site", r"REC-MISS"),
    ("fail-soft", r"fail-soft"),
]
def run():
    hits = {}
    for root, _, files in os.walk(SRC):
        for fn in files:
            if not fn.endswith((".cpp", ".h")):
                continue
            p = os.path.join(root, fn)
            try:
                text = open(p, errors="replace").read()
            except OSError:
                continue
            for name, pat in PATTERNS:
                for m in re.finditer(pat, text):
                    line = text[:m.start()].count("\n") + 1
                    hits.setdefault(name, []).append(
                        {"file": os.path.relpath(p, SRC), "line": line})
    return {"total_hits": sum(len(v) for v in hits.values()),
            "by_pattern": {k: len(v) for k, v in hits.items()},
            "verdict_law": "POTENTIAL GAP (needs context) — not BUG",
            "detail_top": {k: v[:5] for k, v in hits.items()}}
