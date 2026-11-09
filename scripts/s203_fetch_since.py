#!/usr/bin/env python3
"""S203 — fetch coder comments posted AFTER our last verdict (6740374540 wave)
so the next move reviews their newest achievements before touching the wall."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s203')
OUT.mkdir(parents=True, exist_ok=True)

ISSUES = [450, 492, 505, 515, 519, 520, 521, 533, 536, 557, 564, 565, 566]
SINCE = "2026-11-09T04:00:00Z"  # our S203 verdict window; anything later is fresh


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""


TOK = token()
if not TOK:
    sys.exit("NO TOKEN")

HDRS = ["-H", f"Authorization: token {TOK}",
        "-H", "Accept: application/vnd.github+json"]
BASE = f"https://api.github.com/repos/{REPO}"


def gh(url):
    r = subprocess.run(["curl", "-sS", "--max-time", "30"] + HDRS + [url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return []


summary = {}
for num in ISSUES:
    cs = gh(f"{BASE}/issues/{num}/comments?per_page=100")
    if not isinstance(cs, list):
        summary[num] = f"ERR {str(cs)[:80]}"
        continue
    fresh = [c for c in cs if (c.get("created_at") or "") > SINCE]
    rows = []
    for c in fresh:
        body = c.get("body") or ""
        p = OUT / f"issue_{num}_c{c['id']}.md"
        p.write_text(body)
        rows.append({"id": c["id"], "user": (c.get("user") or {}).get("login"),
                     "at": c.get("created_at"), "len": len(body), "file": str(p)})
    summary[num] = rows

print(json.dumps(summary, indent=1, ensure_ascii=False))
(OUT / "FETCH_INDEX.json").write_text(json.dumps(summary, indent=1))
