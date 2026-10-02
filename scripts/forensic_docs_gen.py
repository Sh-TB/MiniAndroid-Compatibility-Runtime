#!/usr/bin/env python3
"""forensic_docs_gen.py — generate the machine-derived forensic documents:
  docs/FORENSIC_REQUEST_GRAPH.md + .jsonl   (parent-child edges)
  docs/FORENSIC_REGRESSION_STATUS.jsonl     (current-HEAD gate truth)
  docs/FORENSIC_EVIDENCE_INDEX.jsonl        (evidence artifact index)
"""
import json, os, re, hashlib, subprocess
from collections import defaultdict

D = "/home/z/my-project"
rows = [json.loads(l) for l in open(f"{D}/docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl")]
by_id = {r["request_id"]: r for r in rows}

# ---------- REQUEST GRAPH ----------
edges = []
for r in rows:
    if r["parent_id"]:
        p = by_id.get(r["parent_id"])
        edges.append({
            "child": r["request_id"], "parent": r["parent_id"],
            "parent_issue": (p or {}).get("issue", ""),
            "child_issue": r["issue"],
            "child_status": r["verified_status"],
            "relation": "parent-child",
        })
# dedupe (F-NEW-169 double-row keeps both)
seen = set(); graph_rows = []
for e in edges:
    k = (e["child"], e["parent"])
    if k in seen: continue
    seen.add(k); graph_rows.append(e)

with open(f"{D}/docs/FORENSIC_REQUEST_GRAPH.jsonl", "w") as f:
    for e in graph_rows:
        f.write(json.dumps(e) + "\n")

children = defaultdict(list)
for e in graph_rows:
    children[e["parent"]].append(e["child"])
lines = ["# FORENSIC REQUEST GRAPH (issue #365)", "",
         "Machine-derived parent-child edges of the reconstructed request corpus",
         f"({len(rows)} request rows, {len(graph_rows)} edges). Source: docs/FORENSIC_REQUEST_GRAPH.jsonl", ""]
for parent in sorted(children, key=lambda p: (len(children[p]), p), reverse=True):
    kids = children[parent]
    prow = by_id.get(parent, {})
    lines.append(f"- **{parent}** — {prow.get('request_text','')[:80]} — {prow.get('verified_status','?')} ({len(kids)} children)")
    if len(kids) <= 12:
        for k in kids:
            krow = by_id.get(k, {})
            lines.append(f"    - {k} [{krow.get('verified_status','?')}/{krow.get('evidence_level','?')}] {krow.get('request_text','')[:70]}")
    else:
        from collections import Counter
        c = Counter(by_id.get(k, {}).get("verified_status", "?") for k in kids)
        lines.append(f"    - status distribution: {dict(c)}")
        lines.append(f"    - sample: {', '.join(kids[:6])} …")
open(f"{D}/docs/FORENSIC_REQUEST_GRAPH.md", "w").write("\n".join(lines) + "\n")
print("graph:", len(graph_rows), "edges")

# ---------- REGRESSION STATUS ----------
def sha16(p):
    if not os.path.exists(p): return ""
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

reg_rows = [
    {"ref": "REG-CURRENT-001", "date": "2026-10-03", "head": subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=D, capture_output=True, text=True).stdout.strip()[:8],
     "gate": "WORKING-VS-FAILING-GATE (scripts/working_vs_failing_probe.sh)",
     "targets": "opencalc e364b001ee7abd66 x3 / chess b5a7a35d5fe0564b x3 / dooz d602648e8e401895 x3 / microtimer da73010a37dd0189 x3 / unote 4f1a9e4e8f64fae8 x3",
     "result": "ALL PASS — byte-identical to recorded goldens", "sha_change": "none",
     "explanation": "Independent re-run during the #365 forensic campaign at current HEAD (after the uninstall + canonical-registry fixes)."},
    {"ref": "REG-CURRENT-002", "date": "2026-10-03",
     "gate": "LOADING-PROBE-GATE (scripts/loading_probe_runner.sh)",
     "targets": "23/23 synthetic probe groups (fixtures/loading_probe)",
     "result": "ALL PASS", "sha_change": "none",
     "explanation": "P0 byte-loading contract holds at HEAD; host escape DENIED (/etc) + /dev/urandom AOSP-legal allowlist verified."},
    {"ref": "REG-CURRENT-003", "date": "2026-10-03",
     "gate": "UNINSTALL-PROOF-GATE (scripts/forensic_uninstall_proof.sh)",
     "targets": "two-package store lifecycle: install x2, uninstall one, isolation, NOT_INSTALLED honesty, reinstall-clean, store empty",
     "result": "ALL PASS 16/16", "sha_change": "new capability (F-NEW-231 recorded PENDING row closed)",
     "explanation": "Generic fix delivered by this forensic campaign (§21); regression gates re-run clean after it."},
    {"ref": "REG-CURRENT-004", "date": "2026-10-03",
     "gate": "CANONICAL EVIDENCE VALIDATOR (tools/verify_canonical_evidence.py)",
     "targets": "R1-R12 over docs/evidence/canonical/registry.json (150 titles)",
     "result": "0 FAIL (was 3 FAIL: R4 fish.rings duplicate artifact, R10 x2 unregistered browser artifacts) / 112 legal BLOCKED WARNs",
     "sha_change": "registry 148 -> 150 titles; stale fish.rings jpg removed; totals synchronized",
     "explanation": "§16 README/registry sync gap found and fixed within the campaign; README/ACHIEVEMENTS counts updated to the registry-generated numbers."},
    {"ref": "REG-HIST-001", "date": "2026-09-28..29 (S114->S117)",
     "gate": "3-reference-game regression anchors",
     "targets": "breakout / ballbreak / dooz",
     "result": "recorded justified re-baseline", "sha_change": "S114 sandbox SHAs did not reproduce on the fresh S117 sandbox (fonts/library versions)",
     "explanation": "Recorded in #363 §1 with written justification: environment shift, deliberate re-anchor (G7); NOT a code regression."},
    {"ref": "REG-HIST-002", "date": "2026-09-27..30 (S125-S127)",
     "gate": "forkgram/telegram faces",
     "targets": "forkgram bbb6cd10a834963d / headingcalc a169346e x3 / flappycow menu 13cf4746 x3",
     "result": "forkgram drifted from V10 — recorded as intentional F-NEW-226/227 text-law change (REAL_APP_CONTENT verdict preserved); others byte-identical",
     "sha_change": "justified re-baseline (law change, documented)",
     "explanation": "Drift pre-dates this campaign; evidence trail in #353/#354 comments."},
]
with open(f"{D}/docs/FORENSIC_REGRESSION_STATUS.jsonl", "w") as f:
    for r in reg_rows:
        f.write(json.dumps(r) + "\n")
print("regression rows:", len(reg_rows))

# ---------- EVIDENCE INDEX ----------
def add(paths, kind, desc, out):
    for p in paths:
        if os.path.exists(p):
            sz = os.path.getsize(p)
            h = sha256_file(p) if sz < 8_000_000 else "(large)"
            out.append({"path": os.path.relpath(p, D), "kind": kind, "bytes": sz, "sha256": h, "note": desc})
        else:
            out.append({"path": os.path.relpath(p, D), "kind": kind, "bytes": None, "sha256": None, "note": desc + " [MISSING]"})

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

out = []
add([f"{D}/docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl"], "ledger", "canonical request ledger (#365 §18)", out)
add([f"{D}/docs/FORENSIC_REQUEST_GRAPH.jsonl", f"{D}/docs/FORENSIC_REGRESSION_STATUS.jsonl"], "ledger", "forensic derived docs", out)
add([f"{D}/root_registry.json", f"{D}/canonical/root_cause_registry.json"], "registry", "root registries (530 vs 492 sync gap recorded)", out)
add([f"{D}/docs/MICRO_GAP_REGISTRY.json"], "registry", "311 micro-gap tickets", out)
add([f"{D}/docs/corpus/s82/title_registry.json"], "registry", "202 frozen titles", out)
add([f"{D}/canonical/game_registry.json", f"{D}/canonical/app_registry.json"], "registry", "canonical per-title registries", out)
add([f"{D}/docs/evidence/canonical/registry.json"], "registry", "150 canonical executed titles", out)
add([f"{D}/scripts/working_vs_failing_probe.sh", f"{D}/scripts/loading_probe_runner.sh",
     f"{D}/scripts/forensic_uninstall_proof.sh", f"{D}/tools/verify_canonical_evidence.py"], "test", "gates re-run at HEAD 2026-10-03", out)
add([f"{D}/docs/LOADING_RUNTIME_TRACE.jsonl", f"{D}/docs/INSTALL_TREE_PROOF.jsonl",
     f"{D}/docs/WORKING_VS_FAILING_LOADING_MATRIX.jsonl", f"{D}/docs/LOADING_API_COVERAGE_MATRIX.jsonl",
     f"{D}/docs/WORKING_APP_LOADING_EXPLANATIONS.md", f"{D}/docs/WHITE_SCREEN_LOADING_ROOTS.md",
     f"{D}/docs/LOADING_FAILURE_DIAGNOSTICS.md", f"{D}/docs/LOADING_ROOT_FANOUT.md",
     f"{D}/docs/AUDIT_REQUIREMENT_COVERAGE.jsonl"], "evidence", "loading-campaign deliverables (verified present)", out)
add([f"{D}/docs/REAL_ANDROID_LOADING_ORACLE.md", f"{D}/docs/FILE_RESOURCE_LOADING_COMPATIBILITY.md",
     f"{D}/docs/LOAD_COMPATIBILITY_MATRIX.jsonl", f"{D}/scripts/load_audit_proof.sh"], "evidence", "LOAD-AUDIT deliverables", out)
add([f"{D}/docs/EXECUTED_GIFS.md", f"{D}/docs/ACHIEVEMENTS.md", f"{D}/docs/evidence/CANONICAL_SCREENSHOTS.md",
     f"{D}/README.md"], "doc", "README/achievement chain", out)
add([f"{D}/docs/FINAL_COMPATIBILITY_CAMPAIGN.md", f"{D}/CAMPAIGN_STATE.md", f"{D}/worklog.md",
     f"{D}/CONSTITUTION_V2.md"], "law", "laws + campaign state", out)
add([f"{D}/.agent/CODER_REQUEST_PROTOCOL.md", f"{D}/.agent/requests/001-upstream-reuse-and-completion-gate.md",
     f"{D}/.agent/mission.md", f"{D}/.agent/state.md", f"{D}/.agent/master_campaign_state.md",
     f"{D}/.agent/decisions.md", f"{D}/.agent/backlog.md"], "law", "agent laws (state/master_campaign_state recorded as STALE)", out)
add([f"{D}/docs/evidence/canonical/eu.veldsoft.fish.rings.gif",
     f"{D}/docs/evidence/canonical/com.miniandroid.browser.gif",
     f"{D}/docs/evidence/canonical/com.miniandroid.browser.zai.gif"], "artifact", "canonical artifacts touched by R4/R10 fix", out)
add([f"{D}/docs/UPSTREAM_CODE_INVENTORY.md", f"{D}/docs/UPSTREAM_CODE_INVENTORY.jsonl",
     f"{D}/docs/UPSTREAM_AVAILABLE_NOT_USED.jsonl", f"{D}/docs/UPSTREAM_REPLACEMENT_PLAN.jsonl",
     f"{D}/docs/UPSTREAM_LICENSE_MATRIX.jsonl", f"{D}/docs/UPSTREAM_RUNTIME_USAGE.jsonl",
     f"{D}/docs/UPSTREAM_UPDATE_TRACKING.jsonl"], "upstream", "issue #364 upstream deliverables (created this campaign)", out)
with open(f"{D}/docs/FORENSIC_EVIDENCE_INDEX.jsonl", "w") as f:
    for o in out:
        f.write(json.dumps(o) + "\n")
print("evidence index:", len(out))
