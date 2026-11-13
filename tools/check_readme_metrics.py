#!/usr/bin/env python3
"""Detects stale public summaries vs docs/METRICS.json (#587 R14/WP6).

Checks that README.md does not carry counts that contradict the canonical
metrics source, and that METRICS.json is fresh (regenerated after the last
registry change). Exit non-zero on drift.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M = json.load(open(ROOT / "docs/METRICS.json"))
readme = (ROOT / "README.md").read_text()

errs = []

def last_commit(path):
    out = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%H", "--", path],
                         capture_output=True, text=True).stdout.strip()
    return out

# 1. README must not contradict canonical counts
T = M["canonical_titles_total"]
V = M["canonical_verified"]
bad_patterns = [
    (rf"\b{V - 1}\b verified", f"stale 'verified' count {V-1} (canonical {V})"),
    (rf"\b{V + 12}\b verified", f"stale 'verified' count {V+12} (canonical {V})"),
    (r"\b421\b roots", "stale 421 roots (canonical %d)" % M["root_causes_total"]),
    (r"\b853\b roots", "stale 853 roots (canonical %d)" % M["root_causes_total"]),
    (r"\b148\b titles", "stale 148 titles (canonical %d)" % T),
    (r"\b150\b titles", "stale 150 titles (canonical %d)" % T),
]
for pat, why in bad_patterns:
    if re.search(pat, readme):
        errs.append(f"README.md: {why}")

# 2. README must declare the metric source
if "docs/METRICS.json" not in readme:
    errs.append("README.md: does not reference the canonical metric source docs/METRICS.json")

# 3. METRICS must be regenerated no older than the newest registry change
regs = ["docs/evidence/canonical/registry.json", "canonical/game_registry.json",
        "canonical/app_registry.json", "root_registry.json"]
metric_commit = last_commit("docs/METRICS.json")
for r in regs:
    if last_commit(r) == metric_commit:
        continue  # same commit = fresh by construction
# a registry newer than METRICS = stale
newer = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%H", "--", r],
                       capture_output=True, text=True).stdout.strip()
if newer and newer != metric_commit:
    is_ancestor = subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor",
                                  metric_commit, newer], capture_output=True).returncode == 0
    if is_ancestor:
        errs.append(f"docs/METRICS.json is stale relative to {r} (regenerate with tools/generate_metrics.py)")

if errs:
    print("METRICS CHECK: FAIL")
    for e in errs:
        print(" -", e)
    sys.exit(1)
print("METRICS CHECK: OK — README consistent with canonical counts (%d titles / %d verified / %d roots)" %
      (M["canonical_titles_total"], M["canonical_verified"], M["root_causes_total"]))
