#!/usr/bin/env python3
"""S20 — fresh fetch of #635 (body + ALL comments), #633, #634 (body + comments).
Auth: token read at runtime from git credential (never stored, never printed)."""
import subprocess
import json
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/miniandroid/evidence/audit/RAW_LOGS/s20_issues_2026-11-21.md"


def token() -> str:
    creds = subprocess.run(["git", "credential", "fill"], cwd="/home/z/my-project",
                           input="protocol=https\nhost=github.com\n\n",
                           capture_output=True, text=True).stdout
    for line in creds.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")


def api(path: str):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token()}", "Accept": "application/vnd.github+json",
        "User-Agent": "miniandroid-audit"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main() -> None:
    parts = []
    for num in (635, 633, 634):
        issue = api(f"issues/{num}")
        parts.append(f"## #{num} {issue['title']} (state={issue['state']})\n")
        parts.append(issue["body"] or "(empty body)")
        parts.append("\n### comments:\n")
        comments = api(f"issues/{num}/comments?per_page=100")
        for c in comments:
            parts.append(f"--- [{c['user']['login']} at {c['created_at']}] "
                         f"(comment id {c['id']})\n{c['body']}\n")
        parts.append(f"\n({len(comments)} comments total)\n\n")
    text = "\n".join(parts)
    with open(OUT, "w") as f:
        f.write(text)
    print(f"written {len(text)} chars -> {OUT}")
    print(f"comment counts: " + ", ".join(
        f"#{n}={text.count(f'--- [')}" for n in (635,)) if False else "")


if __name__ == "__main__":
    main()
