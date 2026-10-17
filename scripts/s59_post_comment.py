#!/usr/bin/env python3
"""s59_post_comment.py — post a markdown file as an issue comment.
Usage: s59_post_comment.py <issue_number> <markdown_file>
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = f"{ROOT}/run/.ghtoken"


def main():
    issue = sys.argv[1]
    md = open(sys.argv[2]).read()
    token = open(TOKEN_FILE).read().strip()
    body = json.dumps({"body": md})
    r = subprocess.run(
        ["curl", "-sS", "--max-time", "90", "-X", "POST",
         "-H", f"Authorization: token {token}",
         "-H", "Accept: application/vnd.github+json",
         "-d", body,
         f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments"],
        capture_output=True, text=True)
    d = json.loads(r.stdout)
    print("comment id:", d.get("id"), "| url:", d.get("html_url"))


if __name__ == "__main__":
    main()
