#!/usr/bin/env python3
"""Post a user-approved comment from scripts/pending_comment.md.

Design (S235 turn): the comment text + target arrive from the user; this
script fires the post ONLY when the file exists and passes every guard:
  line 1:  <!-- target: issues/<N>            (issue number in this repo)
           <!-- target: <owner>/<repo>#<N>    (other repo)
           <!-- target: <full comments URL>
  rest:    the verbatim body.
Guards: file missing / no target header / empty body / placeholder markers
(【】, TODO, XXX, <text>, YOUR_) -> refuse, post nothing, exit 1.
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DRAFT = BASE / "scripts" / "pending_comment.md"
DEFAULT_REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

PLACEHOLDERS = re.compile(r"【|TODO|XXX|<text>|YOUR_|\[insert|PLACEHOLDER")

def die(msg: str) -> "NoReturn":
    print(f"REFUSED: {msg}")
    sys.exit(1)

def main() -> None:
    if not DRAFT.exists():
        die(f"{DRAFT.name} does not exist — nothing to post. Write the "
            "comment body + the target header first.")
    lines = DRAFT.read_text(encoding="utf-8").splitlines()
    m = re.match(r"<!--\s*target:\s*(.+?)\s*-->\s*$", lines[0] if lines else "")
    if not m:
        die("line 1 is not a target header "
            "(<!-- target: issues/<N> --> or owner/repo#N or a full URL)")
    target = m.group(1)
    body = "\n".join(lines[1:]).strip()
    if not body:
        die("empty body after the target header")
    if PLACEHOLDERS.search(body):
        die("the body still contains placeholder markers — fill it first")

    repo = DEFAULT_REPO
    mm = re.match(r"([\w.-]+/[\w.-]+)#(\d+)$", target)
    if target.startswith("http"):
        url = target
    elif mm:
        repo, num = mm.group(1), mm.group(2)
        url = f"https://api.github.com/repos/{repo}/issues/{num}/comments"
    else:
        m2 = re.match(r"(?:issues/)?(\d+)$", target)
        if not m2:
            die(f"unrecognized target: {target!r}")
        url = f"https://api.github.com/repos/{repo}/issues/{m2.group(1)}/comments"

    cred = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, cwd=str(BASE)).stdout
    tok = [l.split("=", 1)[1] for l in cred.splitlines()
           if l.startswith("password=")][0]
    req = urllib.request.Request(
        url, data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"token {tok}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "pending-comment-poster"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        c = json.loads(r.read().decode())
    print(f"POSTED comment {c['id']} -> {c['html_url']}")
    DRAFT.rename(DRAFT.with_suffix(".posted"))  # prevent double-posting

if __name__ == "__main__":
    main()
