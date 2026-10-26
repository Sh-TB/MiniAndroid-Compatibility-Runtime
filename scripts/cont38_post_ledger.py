#!/usr/bin/env python3
"""CONT-38 — post the wave ledger comment to issue #387 (rate-limit retry helper).
Run when the API quota resets (or with an authenticated token)."""
import json, urllib.request
comment = open('/home/z/my-project/evidence/cont38/LEDGER_COMMENT_387.md').read()
body = {"body": comment}
req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/387/comments",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json", "User-Agent": "miniandroid-bot"})
try:
    r = urllib.request.urlopen(req)
    print("comment posted:", json.load(r)["id"])
except Exception as e:
    print("comment FAILED:", e)
