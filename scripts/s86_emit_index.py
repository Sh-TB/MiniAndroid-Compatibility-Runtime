#!/usr/bin/env python3
"""s86_emit_index.py — regenerate docs/evidence/CANONICAL_SCREENSHOTS.md from
registry.json (single source of truth). Keeps the established table schema;
adds a State-Change glyph column sourced from the state flags."""
import json
import os

ROOT = "/home/z/my-project"
REG = json.load(open(f"{ROOT}/docs/evidence/canonical/registry.json"))

out = []
out.append("# Canonical Screenshot Index (machine-checkable)\n")
out.append("S84/S85 law: **ONE title → ONE canonical screenshot** (interactive "
           "titles →\nONE gameplay GIF). Generated from `registry.json` — the "
           "single source of\ntruth. Validate with "
           "`python3 tools/verify_canonical_evidence.py`.\n")
out.append("- Rows with a screenshot: canonical artifact on disk, SHA256-pinned in")
out.append("  [canonical/SHA256SUMS](canonical/SHA256SUMS).")
out.append("- Rows with \"—\": honest text-only records (the near-blank engine-default")
out.append("  shell class is never shipped as visual evidence — S54 gate law, S85")
out.append("  hardening). Evidence lives in the session logs referenced from")
out.append("  [docs/ACHIEVEMENTS.md](../ACHIEVEMENTS.md).\n")

out.append("| Title | Type | Package | Source | APK SHA256 (16) | Screenshot | "
           "Screenshot SHA256 (16) | Level | State Change | Issue/Root cause |")
out.append("|---|---|---|---|---|---|---|---|---|---|")


def apk16(t):
    s = t.get("apk_sha256", "") or ""
    return s[:16] if s else "—"


def src(t):
    s = t.get("source", "") or ""
    if s.startswith("http"):
        return f"[F-Droid]({s})"
    if s:
        return s
    return "—"


def shot(t):
    a = t.get("artifact", "") or ""
    if not a:
        return "— (text record, S54 gate)"
    name = os.path.basename(a)
    return f"[{name}](canonical/{name})"


def sha16(t):
    s = t.get("artifact_sha256", "") or ""
    return s[:16] if s else "—"


def lvl(t):
    l = t.get("level", "")
    return f"L{l}" if l != "" else "—"


def state(t):
    parts = []
    if t.get("launched"):
        parts.append("LAUNCHED")
    if t.get("rendered"):
        parts.append("RENDERED")
    if t.get("interacted"):
        parts.append("INTERACTED")
    if t.get("state_changed"):
        parts.append("STATE_CHANGED")
    return "→".join(parts) if parts else "—"


def rc(t):
    r = (t.get("root_cause", "") or "").strip()
    if not r:
        return "—"
    if r.startswith("F-NEW-"):
        return r.split(" ", 1)[0].split(":", 1)[0]
    for k in ("F-", "R-NEW-", "S83", "S84", "S85", "S86"):
        if r.startswith(k):
            return r.split(" ", 1)[0]
    return r.split(" ", 1)[0][:28]


T = sorted(REG["titles"], key=lambda t: (t.get("type", ""), t["title"].lower()))
for t in T:
    out.append(
        f"| {t['title']} | {t.get('type','')} | `{t['package']}` | {src(t)} | "
        f"{apk16(t)} | {shot(t)} | {sha16(t)} | {lvl(t)} | {state(t)} | "
        f"{rc(t)} |")

out.append("")
out.append(f"_Rows: {len(T)} (regenerated S86 from registry.json "
           f"count {REG.get('count')})._")

open(f"{ROOT}/docs/evidence/CANONICAL_SCREENSHOTS.md", "w").write(
    "\n".join(out) + "\n")
print("index regenerated:", len(T), "rows")
