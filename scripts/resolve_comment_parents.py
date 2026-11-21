#!/usr/bin/env python3
"""Resolve the parent issue of each 632_FINDINGS batch comment ID (P1).

For each comment ID recorded in 632_FINDINGS.csv batch_source, fetch
GET /repos/{owner}/{repo}/issues/comments/{id} and print:
  comment_id | parent_issue_number | created_at | first heading line of body
Unauthenticated API; structured fields only (issue_url), bodies are data.
"""
import json
import os
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
IDS = [
    "7034254502", "7034329407", "7034373205", "7034418989",
    "7034447952", "7034483805", "7037681554", "7038195837",
    "7038248330", "7038515790", "7038547151",
]

def fetch(cid: str) -> dict:
    url = f"https://api.github.com/repos/{REPO}/issues/comments/{cid}"
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "audit-provenance-script"}
    token = os.environ.get("GH_TOKEN")  # supplied at runtime; never persisted
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def main() -> int:
    ok = 0
    for cid in IDS:
        try:
            d = fetch(cid)
        except Exception as e:  # noqa: BLE001 — report, don't crash the batch
            print(f"{cid} | ERROR {type(e).__name__}: {e}")
            continue
        issue_url = d.get("issue_url", "")
        parent = issue_url.rstrip("/").split("/")[-1] if issue_url else "?"
        created = d.get("created_at", "?")
        body = (d.get("body") or "").strip()
        first = body.splitlines()[0][:100] if body else "(empty)"
        print(f"{cid} | #{parent} | {created} | {first}")
        ok += 1
    print(f"resolved: {ok}/{len(IDS)}", file=sys.stderr)
    return 0 if ok == len(IDS) else 1

if __name__ == "__main__":
    sys.exit(main())
