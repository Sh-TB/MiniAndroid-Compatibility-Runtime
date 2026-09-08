#!/usr/bin/env python3
"""Minimal GitHub API helper for the M3 reconciliation pass."""
import json, os, sys, urllib.request

TOKEN = open("/home/z/.gh_token").read().strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
BASE = f"https://api.github.com/repos/{REPO}"


def api(path, method="GET", body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data) as r:
        return json.loads(r.read().decode() or "{}")


def graphql(query, variables=None):
    req = urllib.request.Request("https://api.github.com/graphql", method="POST")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    with urllib.request.urlopen(req, payload) as r:
        return json.loads(r.read().decode())


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "issue":
        iss = api("/issues/9")
        print(f"TITLE: {iss['title']}\nSTATE: {iss['state']}\nCOMMENTS: {iss['comments']}")
        print(f"BODY_LEN: {len(iss['body'] or '')}")
    elif cmd == "comments":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        cs = api(f"/issues/9/comments?per_page={min(n,100)}")
        for c in cs:
            head = (c["body"] or "").strip().splitlines()
            first = head[0][:110] if head else ""
            print(f"--- id={c['id']} {c['created_at']} len={len(c['body'] or '')} :: {first}")
    elif cmd == "body":
        iss = api("/issues/9")
        with open(sys.argv[2], "w") as f:
            f.write(iss["body"] or "")
        print(f"saved {len(iss['body'] or '')} chars")
    elif cmd == "comment_body":
        c = api(f"/issues/comments/{sys.argv[2]}")
        with open(sys.argv[3], "w") as f:
            f.write(c["body"] or "")
        print(f"saved {len(c['body'] or '')} chars")
    elif cmd == "edit_body":
        body = open(sys.argv[2]).read()
        api("/issues/9", "PATCH", {"body": body})
        print(f"issue #9 body updated ({len(body)} chars)")
    elif cmd == "comment":
        body = open(sys.argv[2]).read()
        r = api("/issues/9/comments", "POST", {"body": body})
        print(f"COMMENT_URL: {r['html_url']}")
    elif cmd == "edit_comment":
        body = open(sys.argv[3]).read()
        r = api(f"/issues/comments/{sys.argv[2]}", "PATCH", {"body": body})
        print(f"UPDATED: {r['html_url']}")
