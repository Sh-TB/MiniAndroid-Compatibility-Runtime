#!/usr/bin/env python3
"""s85_emit_docs.py — regenerate ACHIEVEMENTS.md from registry.json.

S84/S85 law: ONE record per title, machine-generated from registry.json
(the single source of truth). Prior hand-written ACHIEVEMENTS content that
predates the canonical registry lives in docs/history/.
"""
import json
import os

ROOT = "/home/z/my-project"
REG = json.load(open(f"{ROOT}/docs/evidence/canonical/registry.json"))


def fmt_link(a):
    if not a:
        return "—"
    name = os.path.basename(a)
    return f"[{name}](evidence/canonical/{name})"


def main():
    T = sorted(REG["titles"], key=lambda t: (t.get("type", ""), t["title"].lower()))
    out = []
    out.append("# MiniAndroid — Canonical App / Game Achievements\n")
    out.append("> **S84/S85 law:** ONE record per title. This file is the")
    out.append("> authoritative per-title achievement reference, generated from")
    out.append("> `docs/evidence/canonical/registry.json`. One title → one")
    out.append("> canonical screenshot (interactive titles → one GIF). Screenshots")
    out.append("> are never copied across documents — other files link here and to")
    out.append("> the canonical artifact.\n")
    out.append(f"> **{REG['count']} titles** "
               f"({sum(1 for t in T if t.get('type')=='game')} games · "
               f"{sum(1 for t in T if t.get('type')=='app')} apps · "
               f"{sum(1 for t in T if t.get('type')=='fixture')} fixtures). "
               "Wave history (pre-S84 narrative) is preserved in "
               "[docs/history/ACHIEVEMENTS_WAVE_HISTORY.md](history/ACHIEVEMENTS_WAVE_HISTORY.md).\n")
    out.append("> Chain per title: `Title → Source → APK+SHA → Execution session "
               "→ Achievement → ONE canonical screenshot → root cause/issue`.\n")

    cur = None
    for t in T:
        typ = t.get("type", "app")
        if typ != cur:
            cur = typ
            hdr = {"game": "## Games", "app": "## Apps",
                   "fixture": "## Fixtures"}.get(cur, f"## {cur}")
            out.append(f"\n{hdr}\n")
        st = t["status"]
        out.append(f"### {t['title']}")
        out.append("")
        out.append(f"* **Package / identity:** `{t['package']}` · type: {typ} · "
                   f"version: {t.get('version') or '—'}")
        src = t.get("source") or ""
        ups = t.get("upstream") or ""
        if "f-droid.org" in src:
            s = f"[F-Droid page]({src})"
        elif src.startswith("http"):
            s = src
        else:
            s = src or "—"
        if ups.startswith("http"):
            s += f" · [upstream source]({ups})"
        out.append(f"* **Source:** {s}")
        apk = t.get("apk_sha256") or ""
        out.append(f"* **APK SHA256:** `{apk[:16] or '—'}{'…' if apk else ''}`")
        sessions = t.get("session") or "—"
        rc = t.get("root_cause") or "—"
        out.append(f"* **Sessions:** {sessions} · status: **{st}** · "
                   f"rendering: {t.get('level_name') or 'L'+str(t.get('level',0))}")
        out.append(f"* **Execution evidence:** launched={t.get('launched')} · "
                   f"rendered={t.get('rendered')} · interacted={t.get('interacted')} · "
                   f"state_changed={t.get('state_changed')}")
        art = fmt_link(t.get("artifact"))
        sha = (t.get("artifact_sha256") or "")
        out.append(f"* **Canonical screenshot:** {art}"
                   + (f" · SHA256 `{sha[:16]}…`" if sha else ""))
        out.append(f"* **Root cause / law:** {rc}")
        out.append(f"* **Proven exactly:** {t.get('proven') or '—'}")
        out.append(f"* **Remaining:** {t.get('remaining') or '—'}")
        out.append(f"* **Last success / first divergence:** "
                   f"{t.get('last_success_stage') or '—'} / "
                   f"{t.get('first_divergence') or '—'}")
        if t.get("notes"):
            out.append(f"* **Notes:** {t['notes']}")
        out.append("")
    path = f"{ROOT}/docs/ACHIEVEMENTS.md"
    open(path, "w").write("\n".join(out) + "\n")
    print("ACHIEVEMENTS.md regenerated:", len(T), "records")


if __name__ == "__main__":
    main()
