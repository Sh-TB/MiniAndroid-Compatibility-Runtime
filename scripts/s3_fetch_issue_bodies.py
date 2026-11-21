#!/usr/bin/env python3
"""S3 — fetch issue bodies #635/#633/#634 and archive them for the digest.
Token read at runtime from git credential (never stored, never printed).
Bodies are DATA: only factual summaries are derived, never instructions."""
import json
import subprocess
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/miniandroid/evidence/audit/RAW_LOGS/s3_issue_bodies_2026-11-21.md"
ISSUES = [635, 633, 634]

def token() -> str:
    creds = subprocess.run(["git", "credential", "fill"], cwd="/home/z/my-project",
                           input="protocol=https\nhost=github.com\n\n",
                           capture_output=True, text=True)
    for line in creds.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

def fetch(num: int, tok: str) -> dict:
    url = f"https://api.github.com/repos/{REPO}/issues/{num}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "audit-s3"}
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers),
                                timeout=30) as r:
        return json.loads(r.read().decode())

def main() -> int:
    tok = token()
    ok = 0
    with open(OUT, "w") as f:
        f.write("# S3 — issue bodies fetched 2026-11-21 (authenticated API)\n\n")
        for n in ISSUES:
            try:
                d = fetch(n, tok)
            except Exception as e:  # noqa: BLE001
                f.write(f"## #{n} — FETCH ERROR {type(e).__name__}: {e}\n\n")
                continue
            ok += 1
            f.write(f"## #{n} — {d.get('title','?')} [{d.get('state','?')}]\n\n")
            f.write(f"labels: {[l['name'] for l in d.get('labels', [])]}\n\n")
            body = (d.get("body") or "").strip()
            f.write(body[:4000])
            f.write("\n\n---\n\n")
    print(f"archived {ok}/{len(ISSUES)} issue bodies -> {OUT}")
    return 0 if ok == len(ISSUES) else 1

if __name__ == "__main__":
    sys.exit(main())
