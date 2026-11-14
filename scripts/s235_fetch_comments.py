#!/usr/bin/env python3
"""S235: fetch the runtime-lane wave comment bodies (the integration source)
and save them verbatim under scripts/s235_comments/."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "scripts" / "s235_comments"
OUT.mkdir(exist_ok=True)

CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines()
         if l.startswith("password=")][0]

COMMENT_IDS = [
    6870803490,  # Wave-5 evidence — F-NEW-630..646 push (9 blocked titles re-run)
    6871461012,  # a2048 WebView laws (webview_engine.cpp etc.)
    6872280176,  # Games-g1 — F-NEW-647..654 push (Chess + OpenSudoku)
    6872292670,  # Chess Practice item-click continuation
]
for cid in COMMENT_IDS:
    url = (f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
           f"/issues/comments/{cid}")
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "s235-fetch"})
    with urllib.request.urlopen(req, timeout=30) as r:
        c = json.loads(r.read().decode())
    body = c["body"]
    (OUT / f"{cid}.md").write_text(
        f"<!-- issue_url: {c['html_url']} | user: {c['user']['login']} | "
        f"created: {c['created_at']} -->\n{body}\n")
    print(f"{cid}: {len(body)} chars saved -> scripts/s235_comments/{cid}.md")
