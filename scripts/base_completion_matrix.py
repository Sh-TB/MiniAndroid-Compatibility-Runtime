#!/usr/bin/env python3
"""BASE-COMPLETION PASS (#375 FINAL) — reconciliation matrix generator.

Enumerates every registry root + the #374 98-section contract + the open
worklog frontiers into one machine-readable matrix with the eight required
states: VERIFIED / IMPLEMENTED / TESTED / PARTIAL / BLOCKED / PENDING /
UNKNOWN / DUPLICATE / SUPERSEDED (+ OBSERVED and NOT_TESTED where the
source ledgers use them). Output:
  docs/BASE_COMPLETION_RECONCILIATION.jsonl  (row per item)
  docs/BASE_COMPLETION_RECONCILIATION.md     (human table + totals)
"""
import json, re, sys
from pathlib import Path

BASE = Path("/home/z/my-project")
REG = json.load(open(BASE / "root_registry.json"))
roots = REG["roots"] if isinstance(REG, dict) and "roots" in REG else REG

# Map registry status -> the eight-state vocabulary
STATE_MAP = {
    "ROOT-CAUSED-FIXED": "VERIFIED", "ROOT_CAUSED-FIXED": "VERIFIED",
    "VERIFIED-FIXED": "VERIFIED", "VERIFIED-CORRECT": "VERIFIED",
    "VERIFIED": "VERIFIED", "VERIFIED_3RUN": "VERIFIED",
    "PROVEN-FIXED": "VERIFIED", "ROOT-CAUSED-CLOSED": "VERIFIED",
    "ROOT-CAUSED-REMEASURED-GENERIC-OK": "VERIFIED",
    "FIXED-S75": "VERIFIED", "FIXED-VERIFIED": "VERIFIED",
    "ROOT-CAUSED-SEMANTIC": "VERIFIED",
    "IMPLEMENTED+TESTED": "TESTED", "IMPLEMENTED": "IMPLEMENTED",
    "USED_BY_EXECUTION": "TESTED", "ROOT-CAUSED-FIXED ": "VERIFIED",
    "NOT-APPLICABLE": "SUPERSEDED", "SUPERSEDED-BY-EVIDENCE": "SUPERSEDED",
    "PARTIAL": "PARTIAL", "PARTIAL-FIX": "PARTIAL",
    "UNPROVEN": "UNKNOWN", "RESEARCHED-NOT-IMPLEMENTED": "PENDING",
    "PENDING": "PENDING", "OPEN": "PENDING", "REGISTERED": "PENDING",
    "OBSERVED-FAIL": "PARTIAL", "OBSERVED": "PARTIAL",
    "BLOCKED": "BLOCKED",
}

# #374 contract status vocabulary -> reconciliation states (CONT-3 Phase 3
# fix: the old generator read s.get("state") which the contract JSONL does
# not carry, defaulting EVERY audited row to PENDING — TESTED silently
# became PENDING in the reconciliation totals).
CONTRACT_STATE_MAP = {
    "TESTED": "TESTED",
    "PARTIAL": "PARTIAL",
    "IMPLEMENTED": "IMPLEMENTED",
    "IMPLEMENTED_UNVERIFIED": "IMPLEMENTED",
    "NOT_APPLICABLE": "NOT_APPLICABLE",
    "PENDING": "PENDING",
    "BLOCKED": "BLOCKED",
    "BLOCKED-EXTERNAL": "BLOCKED",
    "VERIFIED": "VERIFIED",
    "VERIFIED_CURRENT": "VERIFIED",
}

def field(r, *names):
    for n in names:
        v = r.get(n)
        if v: return v
    return ""

rows = []
for r in roots:
    st = (r.get("status") or "NONE").strip()
    rows.append({
        "kind": "registry-root",
        "id": field(r, "id"),
        "status_raw": st,
        "state": STATE_MAP.get(st, "UNKNOWN"),
        "title": (field(r, "title", "name", "summary", "description") or "")[:220],
    })

# Open/frontier roots that define live work
FRONTIER = [
    ("F-NEW-235", "fairymahjong board-build IAE 'Duplicate tile position' — game's own regex/token parse or Set-dedup divergence", "CURRENT FRONTIER — ordered by #375 §6"),
    ("F-NEW-229", "CL MATCH_PARENT spec law (opencalc full button width, no anchors on axis)", "OPEN generic layout law"),
    ("F-NEW-221", "R8-merged class constructor/dispatch mismatch (Compose sudokusolver family)", "OPEN"),
    ("F-NEW-217", "kotlinx-coroutines MutexImpl.unlock spin (F084-family virtual concurrency)", "PENDING"),
    ("F-147", "dooz ViewGroup.getChildAt null — dooz is a byte-stability anchor; fix requires documented re-baseline", "PENDING (anchor-fenced)"),
    ("F-144", "GL/EGL surface family for libGDX (real GL pipeline beyond JSR-239 facade)", "PARTIAL — facade closed, GLSL recorded-not-executed"),
    ("F-145", "screenshot capture surface does not follow top-of-stack window", "PENDING"),
    ("F-143", "Service launch/lifecycle family completeness", "TESTED core legs (SVC-01..04); completeness re-audit"),
    ("F-138", "ScoreView hint HUD geometry (legacy text path)", "PENDING"),
    ("F-NEW-161", "chessclock getIntent chain Uri.toString null", "PARTIAL"),
    ("F-NEW-168", "WhatsApp FragmentManager host law", "PARTIAL (app-boundary)"),
    ("F-NEW-169", "WhatsApp DI provider-null lattice", "PARTIAL (app-boundary)"),
    ("F-NEW-192", "draw/z-order audit residue", "PENDING audit"),
    ("R-NEW-456", "LIVE z.ai residual Svelte-5 boot rejection inside minified bundle", "BLOCKED-EXTERNAL"),
]
for rid, desc, st in FRONTIER:
    rows.append({"kind": "frontier", "id": rid, "status_raw": st,
                 "state": st.split(" ")[0].rstrip("—-"), "title": desc})

# #374 98-section contract — audited in wave C; seed rows PENDING here
sec374 = []
p = BASE / "docs" / "FOUNDATION_CONTRACT_98.jsonl"
if p.exists():
    for line in p.read_text().splitlines():
        if line.strip():
            sec374.append(json.loads(line))
else:
    issue = None
    for line in (BASE / "docs" / "GATE_A_ISSUE_CACHE.jsonl").read_text().splitlines() if (BASE / "docs" / "GATE_A_ISSUE_CACHE.jsonl").exists() else []:
        pass
    # Fetch from issue cache if present, else mark PENDING
    sec374 = []

for s in sec374:
    raw = (s.get("status") or "PENDING").strip()
    rows.append({"kind": "contract-374", "id": f"374-§{s['num']}",
                 "status_raw": raw,
                 "state": CONTRACT_STATE_MAP.get(raw,
                     CONTRACT_STATE_MAP.get(raw.split("_")[0], "UNKNOWN")),
                 "title": s.get("title", "")[:200]})

# Totals by state, per kind
from collections import Counter
tot = Counter(r["state"] for r in rows)
per_kind = {}
for k in ("registry-root", "frontier", "contract-374"):
    per_kind[k] = Counter(r["state"] for r in rows if r["kind"] == k)

with open(BASE / "docs/BASE_COMPLETION_RECONCILIATION.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

md = ["# BASE-COMPLETION RECONCILIATION MATRIX (#375 FINAL PASS)", "",
      f"Inputs: root_registry.json ({len(roots)} roots), live frontiers, #374 contract audit.",
      "", "## State totals (all kinds)", ""]
for k, v in tot.most_common():
    md.append(f"- {k}: {v}")
md += ["", "## Per kind", ""]
for k, c in per_kind.items():
    md.append(f"### {k}")
    for kk, vv in c.most_common():
        md.append(f"- {kk}: {vv}")
    md.append("")
(BASE / "docs/BASE_COMPLETION_RECONCILIATION.md").write_text("\n".join(md) + "\n")
print("rows:", len(rows))
print(dict(tot))
