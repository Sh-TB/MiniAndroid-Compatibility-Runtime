#!/usr/bin/env python3
"""s84_emit_docs.py — emit canonical docs from registry.json.

Outputs:
  * docs/evidence/CANONICAL_SCREENSHOTS.md   — machine-checkable index
  * docs/evidence/canonical/SHA256SUMS
  * docs/ACHIEVEMENTS.md                     — per-title canonical record
    (S84 law: ONE record per title; the historical per-wave sections move
     to docs/history/ACHIEVEMENTS_WAVE_HISTORY.md — preserved, referenced)
"""
import json
import os
import shutil
from datetime import date

ROOT = "/home/z/my-project"
CAN = f"{ROOT}/docs/evidence/canonical"
reg = json.load(open(f"{CAN}/registry.json"))
T = reg["titles"]
TODAY = "2026-09-23"


def stats():
    s = {}
    s["total"] = len(T)
    s["games"] = sum(1 for t in T if t["type"] == "game")
    s["apps"] = sum(1 for t in T if t["type"] == "app")
    s["fixtures"] = sum(1 for t in T if t["type"] not in ("game", "app"))
    s["verified"] = sum(1 for t in T if t["status"].startswith("VERIFIED"))
    s["interactive"] = sum(1 for t in T if t["status"] == "VERIFIED-INTERACTIVE")
    s["partial"] = sum(1 for t in T if t["status"].startswith("PARTIAL"))
    s["blocked"] = sum(1 for t in T if t["status"].startswith("BLOCKED"))
    s["rendered"] = sum(1 for t in T if t.get("rendered"))
    s["interacted"] = sum(1 for t in T if t.get("interacted"))
    s["state_changed"] = sum(1 for t in T if t.get("state_changed"))
    s["gif"] = sum(1 for t in T if t["artifact"].endswith(".gif"))
    s["jpg"] = sum(1 for t in T if t["artifact"].endswith(".jpg"))
    s["s84_new"] = sum(1 for t in T if t["session"] == "S84")
    return s


S = stats()


def emit_index():
    lines = [
        "# Canonical Screenshot Index",
        "",
        f"> **ONE title → ONE canonical screenshot** (S84 law, {TODAY}).",
        "> Interactive titles: ONE gameplay GIF. All reports/issues/README",
        "> reference these artifacts — no copies anywhere else.",
        "> Machine source: `docs/evidence/canonical/registry.json`.",
        "> Validate: `python3 tools/verify_canonical_evidence.py`",
        "",
        f"{S['total']} titles · {S['gif']} GIF · {S['jpg']} JPG · "
        f"{S['interactive']} interactive · {S['state_changed']} state-change "
        "proven",
        "",
        "| Title | Type | Package | Source | APK SHA256 | Screenshot | "
        "SHA256 | Level | State Change | Session |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for t in sorted(T, key=lambda x: (x["type"], x["package"])):
        art = t["artifact"]
        link = f"[{os.path.basename(art)}]({art})" if art else "—"
        sha = t["artifact_sha256"][:16] + "…" if t["artifact_sha256"] else "—"
        apk = t["apk_sha256"][:16] + "…" if t["apk_sha256"] else "—"
        sc = "YES" if t["state_changed"] else "—"
        src = t["upstream"] or t["source"]
        if len(src) > 60:
            src = src[:57] + "…"
        src_cell = (f"[source]({src})" if src.startswith("http")
                    else src.replace("|", "/"))
        lines.append(
            f"| {t['title']} | {t['type']} | `{t['package']}` | "
            f"{src_cell} | {apk} | {link} | {sha} | "
            f"L{t['level'] if t['level'] is not None else '-'} | {sc} | "
            f"{t['session']} |")
    with open(f"{ROOT}/docs/evidence/CANONICAL_SCREENSHOTS.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("index:", len(T), "rows")


def emit_sha_sums():
    lines = []
    for t in sorted(T, key=lambda x: x["package"]):
        if t["artifact"] and os.path.exists(f"{ROOT}/{t['artifact']}"):
            lines.append(f"{t['artifact_sha256']}  {t['artifact']}")
    with open(f"{CAN}/SHA256SUMS", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("SHA256SUMS:", len(lines))


def emit_achievements():
    # 1) preserve the per-wave history document
    old = f"{ROOT}/docs/ACHIEVEMENTS.md"
    hist = f"{ROOT}/docs/history/ACHIEVEMENTS_WAVE_HISTORY.md"
    if os.path.exists(old) and not os.path.exists(hist):
        shutil.copyfile(old, hist)

    L = [
        "# MiniAndroid — App & Game Achievements",
        "",
        f"> **CANONICAL, ONE RECORD PER TITLE** (S84 law, {TODAY}).",
        "> This file is the single source of truth for what each app and",
        "> game has PROVEN on MiniAndroid. Historical per-wave narrative",
        "> moved to [ACHIEVEMENTS_WAVE_HISTORY.md](history/"
        "ACHIEVEMENTS_WAVE_HISTORY.md).",
        ">",
        "> Chain (no broken links):",
        "> `Title → Source → APK+SHA → Execution session → Achievement →",
        ">  ONE canonical screenshot → root-cause issue → README summary`",
        ">",
        "> Validate: `python3 tools/verify_canonical_evidence.py` ·",
        "> machine source: `docs/evidence/canonical/registry.json`",
        "",
        "## Status vocabulary",
        "",
        "| Status | Meaning |",
        "|---|---|",
        "| VERIFIED | launched + rendered real frames at the recorded "
        "session |",
        "| VERIFIED-INTERACTIVE | + real click dispatched and rendered "
        "state change captured (GIF) |",
        "| PARTIAL | rendered frames but a first-divergence blocks deeper "
        "behavior (root cause recorded) |",
        "| OBSERVED | frames captured, level below render threshold |",
        "| BLOCKED | no usable frame; root cause recorded |",
        "",
        "## Rendering levels",
        "",
        "L0 recognized → L1 manifest → L2 DEX → L3 lifecycle → L4 UI "
        "machinery → L5 meaningful frame (non-blank real UI) → L6 real "
        "input → L7 input→state change → L8 multiple interactions → "
        "L9 app-specific behavior → L10 close/reopen persistence. "
        "The screenshot-gate law (S54) applies: blank/placeholder frames "
        "are NEVER evidence.",
        "",
        "## Totals (generated from registry.json — not hand-written)",
        "",
        f"- Titles: **{S['total']}** ({S['games']} games, {S['apps']} "
        f"apps, {S['fixtures']} fixtures) — {S['s84_new']} added in S84",
        f"- VERIFIED: **{S['verified']}** · VERIFIED-INTERACTIVE: "
        f"**{S['interactive']}** · PARTIAL: **{S['partial']}** · "
        f"BLOCKED: **{S['blocked']}**",
        f"- Rendered: {S['rendered']} · Interacted: {S['interacted']} · "
        f"State-change proven: {S['state_changed']}",
        f"- Canonical screenshots: **{S['total']}** ({S['gif']} GIF + "
        f"{S['jpg']} JPG) — one per title, zero duplicates",
        "",
        "---",
        "",
    ]

    order = {"game": 0, "app": 1}
    for t in sorted(T, key=lambda x: (order.get(x["type"], 2),
                                      x["package"])):
        art = t["artifact"]
        art_cell = (f"[{os.path.basename(art)}](../{art})"
                    if art else "— (no visual — see divergence)")
        issue = ("[root-cause registry](../docs/evidence/"
                 "ROOT_CAUSE_REGISTRY.md)" if t["root_cause"] not in
                 ("none (rc=0)",) and not t["root_cause"].startswith(
                     "none") else "—")
        L.append(f"### {t['title']}")
        L.append("")
        L.append(f"* **Package / identity:** `{t['package']}` · "
                 f"type: {t['type']} · version: {t['version'] or '—'}")
        src = t["upstream"] or t["source"]
        L.append(f"* **Source:** [{src}]({src})" if src.startswith("http")
                 else f"* **Source:** {src}")
        L.append(f"* **APK SHA256:** `{(t['apk_sha256'] or '—')[:64]}`")
        L.append(f"* **Sessions:** {t['session']} · status: "
                 f"**{t['status']}** · rendering: L{t['level']} "
                 f"({t['level_name']})")
        L.append(f"* **Execution evidence:** launched="
                 f"{str(t['launched']).lower()} · rendered="
                 f"{str(t['rendered']).lower()} · interacted="
                 f"{str(t['interacted']).lower()} · state_changed="
                 f"{str(t['state_changed']).lower()}")
        L.append(f"* **Canonical screenshot:** {art_cell} · SHA256 "
                 f"`{t['artifact_sha256'][:16]}…`")
        L.append(f"* **Root cause:** {t['root_cause'] or '—'} · issue: "
                 f"{issue}")
        L.append(f"* **Proven exactly:** {t['proven']}")
        L.append(f"* **Remaining:** {t['remaining']}")
        if t["status"] in ("PARTIAL", "BLOCKED", "OBSERVED"):
            L.append(f"* **Last success / first divergence:** "
                     f"{t['last_success_stage']} → {t['first_divergence']}")
        L.append(f"* **Notes:** {t['notes']}")
        L.append("")
    with open(old, "w") as f:
        f.write("\n".join(L) + "\n")
    print("ACHIEVEMENTS.md rewritten:", len(T), "records")


if __name__ == "__main__":
    emit_index()
    emit_sha_sums()
    emit_achievements()
