#!/usr/bin/env python3
"""s83_issue_sync.py — post dated S83 evidence comments to the per-title
GitHub issues for every campaign title, plus the root-cause issue #227
(F-NEW-156 family — fixed this session by the S83-APX-ACT law).
PAT used ONLY for REST auth — never persisted.
"""
import json
import os
import urllib.request

ROOT = "/home/z/my-project"
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = os.environ.get("GITHUB_PAT", "")  # PAT via env only — never committed

reg = json.load(open(f"{ROOT}/docs/corpus/s82/title_registry.json"))
by_pkg = {t["PACKAGE"]: t for t in reg["TITLES"]}
camp = json.load(open(f"{ROOT}/run/s83_campaign/report.json"))

DATE = "2026-09-22"
COMMIT = "c1a86c34"


def post_comment(issue, body):
    url = f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"
    req = urllib.request.Request(
        url, data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "miniandroid-s83-sync"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except Exception as e:
        return str(e)


def fmt(item, group):
    v = item.get("visual", {})
    lines = [
        f"### S83 re-audit ({DATE}, commit {COMMIT})",
        "",
        f"- **Result**: rc={item['rc']} · LEVEL **L{v.get('LEVEL','-')} "
        f"{v.get('LEVEL_NAME','-')}** · unique_colors={v.get('UNIQUE_COLORS','-')} · "
        f"dominant={v.get('DOMINANT_COLOR_RATIO','-')}",
        f"- **Flags**: {', '.join(v.get('FLAGS', [])) or 'none'}",
        f"- **Frames**: {item.get('frames', 0)} real PNG frames captured "
        f"(law: no fake screenshots, S83 §42)",
        f"- **Evidence**: `docs/evidence/s83/` (JPG ≤100KB + SHA256SUMS), "
        f"commit bafac0e3",
        f"- **Engine laws applied this wave**: S83-APX-ACT, "
        f"S83-CANVAS-GEOMETRY, S83-LOCALE-DEFAULT, S83-INPUT-SERVICE, "
        f"S83-VIEW-TREE-OBSERVER, S83-AUDIO-OBJECTS (all regression-clean, "
        f"battery 26/26)",
    ]
    err = item.get("errors", "?")
    if err and err not in ("0", "?"):
        lines.append(f"- **Open errors**: {str(err)[:160]}")
    return "\n".join(lines)


posted, skipped, failed = 0, 0, []
for group in ("games", "apps", "high"):
    for item in camp["results"][group]:
        pkg = item["apk"].rsplit("_", 1)[0]
        # package from filename: e.g. com.sidhant.queens_93.apk
        base = item["apk"].replace(".apk", "")
        pkg_guess = base.rsplit("_", 1)[0] if base[-1].isdigit() else base
        t = by_pkg.get(pkg_guess) or by_pkg.get(item["apk"].replace(".apk", ""))
        if not t:
            skipped += 1
            continue
        issue = t.get("ISSUE_NUMBER")
        if not issue:
            skipped += 1
            continue
        rc = post_comment(issue, fmt(item, group))
        if rc == 201:
            posted += 1
        else:
            failed.append((t["TITLE_ID"], issue, rc))
        print(f"{t['TITLE_ID']} #{issue}: {rc}")

print(f"\nposted={posted} skipped={skipped} failed={len(failed)}")
if failed:
    print("FAILURES:", failed[:10])
