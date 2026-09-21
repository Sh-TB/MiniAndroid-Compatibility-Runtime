#!/usr/bin/env python3
"""s77_false_completion_scan.py — S77 §17: false-completion scanner (report mode).

Scans canonical reports for STRONG CLAIM tokens. A claim line passes only if
the same line (or the immediately adjacent lines) contains an evidence pointer:
a repo path (docs/evidence/..., run/..., upload/..., docs/audit/...), a sha-like
hex token, an issue reference (#NN), or a registry id (F-NNN / R-NEW-NNN /
KNOW- / SBX- / ERR-). Claims with no adjacent evidence are FLAGGED for manual
downgrade review — the scanner never edits files.

Constitution mapping: agent claim ≠ evidence; exit 0 ≠ evidence; file
existence ≠ proof. This scanner surfaces violations for human adjudication.
"""
import os, re, sys

ROOT = "/home/z/my-project"
TARGETS = [
    "docs/evidence/S73/S73_REPORT.md",
    "docs/evidence/S74/S74_REPORT.md",
    "docs/evidence/s74_ops/S74_FOLLOWUP_REPORT.md",
    "docs/evidence/s74_ops/AUDIT_TABLE.md",
    "docs/foundation/s75/S75_REPORT.md",
    "docs/foundation/s76/S76_REPORT.md",
    "docs/ACHIEVEMENTS.md",
    "docs/ROADMAP_STATUS.md",
    "docs/audit/RUNTIME_FAILURE_REGISTRY.md",
    "docs/audit/CRASH_HANG_ANR_REGISTRY.md",
    "docs/audit/SANDBOX_ERROR_REPORT.md",
    "docs/audit/SESSION_EVIDENCE_CHAIN.md",
    "docs/audit/PROGRESS_REPORT.md",
    "docs/audit/EVIDENCE_LINEAGE.md",
    "docs/audit/APP_MATRIX.md",
]

CLAIM_WORDS = re.compile(
    r"\b(DONE|COMPLETE|COMPLETED|PASS(?:ED)?|PROVEN|VERIFIED|HUMAN_VISIBLE|"
    r"PERSISTENCE_PASS|SECURITY_PASS|SANDBOX_PASS|USED)\b|"
    r"\b(all apps|fully playable|real APK|persistent|secure)\b", re.I)

EVIDENCE = re.compile(
    r"(docs/evidence/|docs/audit/|docs/foundation/|docs/compatibility/|run/|upload/|"
    r"\b[0-9a-f]{16}\b|\b[0-9a-f]{8}\b|#\d+|\bF-\d+|\bR-NEW-\d+|\bKNOW-|\bSBX-|\bERR-|"
    r"SHA256|sha256_16|NOT_RECORDED|NOT_OBSERVED|UNVERIFIED|PARTIAL|BLOCKED|PENDING|"
    r"PUBLISH_BLOCKED|OPEN)", re.I)

def scan():
    flagged = 0; total_claims = 0; clean = 0
    detail = []
    for t in TARGETS:
        p = os.path.join(ROOT, t)
        if not os.path.exists(p):
            detail.append(f"MISSING TARGET: {t}")
            continue
        lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
        for i, ln in enumerate(lines):
            if ln.lstrip().startswith((">", "#", "|---")):
                continue
            m = CLAIM_WORDS.search(ln)
            if not m:
                continue
            # skip table headers and self-referential scanner lines
            if "CLAIM" in ln and "SOURCE" in ln:
                continue
            total_claims += 1
            ctx = "\n".join(lines[max(0, i-1):i+2])
            if EVIDENCE.search(ctx):
                clean += 1
            else:
                flagged += 1
                detail.append(f"FLAG {t}:{i+1}: {ln.strip()[:150]}")
    print(f"SCANNER RESULT: {total_claims} claim lines, {clean} with adjacent evidence, {flagged} FLAGGED")
    for d in detail[:60]:
        print(d)
    if len(detail) > 60:
        print(f"... ({len(detail)-60} more)")
    return 0

if __name__ == "__main__":
    sys.exit(scan())
