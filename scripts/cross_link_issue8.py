#!/usr/bin/env python3
"""cross_link_issue8.py — leave a pointer on Issue #8 that the campaign anchor moved to #9."""
import json, urllib.request

TOKEN = open("/home/z/.gh_token").read().strip()
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"

body = """## Continuation pointer — MASTER-ROADMAP v3 now anchors at Issue #9

Per the new **MASTER-ROADMAP v3 — 100% Base Execution Closure System** (§102: the roadmap issue is a living document), the campaign anchor moved to:

**https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/9**

Retroactively published there (previously `PUBLISH BLOCKED — TOKEN ABSENT` in [FINDINGS_REGISTRY.md](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/docs/evidence/m3_campaign/FINDINGS_REGISTRY.md)):

- **Sessions 6–7 record** — [comment](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/9#issuecomment-5580799755): reproducibility (F-001/002/003), F-ROOM-CHAIN token law (F-004), Math surface (F-007), GATE F **FULLY CLOSED** (F-008/009/010, 3-run byte-identical agg SHA 2a425979ef7d32bf2acf), View keyed-tag law (F-011).
- **Session-8 record** — [comment](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/9#issuecomment-5580800193): app-data-root law (F-012), clinit provenance law (F-013), Class.getName (F-014), receiver-domain guard (F-015); GATE H **FULLY CLOSED** (real-APK image golden IoU 0.959/0.997).
- **FORGOTTEN-001..020 + restart baseline** — [comment](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/9#issuecomment-5580800520): F-016 registered; restart baseline HEAD `eadaf695` with **11 previously unpushed commits now pushed** and **battery 61/61 ALL PASS**.

This issue stays open as the historical evidence archive (50 comments, EXP-064 → MASTER-3 cluster 5). No history rewritten."""

req = urllib.request.Request(f"{BASE}/issues/8/comments",
    data=json.dumps({"body": body}).encode(), method="POST", headers={
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
    "User-Agent": "miniandroid-campaign"})
with urllib.request.urlopen(req) as r:
    out = json.loads(r.read().decode())
    print(f"comment posted: {out['html_url']}")
