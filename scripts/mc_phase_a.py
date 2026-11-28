#!/usr/bin/env python3
"""Main Coder — Phase A: full repository inventory via GitHub API.
Token derived at runtime from git credential fill; never printed/stored."""
import json
import subprocess
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "docs/project-intelligence/raw"


def get_token():
    p = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise RuntimeError("no token")


TOKEN = get_token()


def api(path, params=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "main-coder-agent"})
    return json.load(urllib.request.urlopen(req))


def paginate(path, params=None, max_pages=30):
    params = dict(params or {})
    params["per_page"] = 100
    out = []
    for page in range(1, max_pages + 1):
        params["page"] = page
        chunk = api(path, params)
        if not chunk:
            break
        out.extend(chunk)
        if len(chunk) < 100:
            break
    return out


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    # 1. all issues (issues API includes PRs — filter later by pull_request key)
    issues = paginate("issues", {"state": "all", "sort": "created", "direction": "asc"})
    real_issues = [i for i in issues if "pull_request" not in i]
    slim = [{
        "n": i["number"], "state": i["state"], "title": i["title"],
        "author": i["user"]["login"], "created": i["created_at"][:10],
        "updated": i["updated_at"][:10], "comments": i["comments"],
        "labels": [l["name"] for l in i["labels"]],
        "body_head": (i.get("body") or "")[:400],
        "url": i["html_url"],
    } for i in real_issues]
    json.dump(slim, open(f"{OUT}/issues_all.json", "w"), indent=0)
    print(f"issues: {len(real_issues)}  (open {sum(1 for i in slim if i['state']=='open')}, "
          f"closed {sum(1 for i in slim if i['state']=='closed')})")
    # 2. PRs (pulls API gives head/base/merged properly)
    prs = paginate("pulls", {"state": "all", "sort": "created", "direction": "asc"})
    pr_slim = [{
        "n": p["number"], "state": p["state"], "title": p["title"],
        "author": p["user"]["login"], "created": p["created_at"][:10],
        "merged": bool(p.get("merged_at")), "merged_at": (p.get("merged_at") or "")[:10],
        "head": p["head"]["ref"], "base": p["base"]["ref"],
        "url": p["html_url"],
    } for p in prs]
    json.dump(pr_slim, open(f"{OUT}/prs_all.json", "w"), indent=0)
    print(f"prs: {len(pr_slim)} (merged {sum(1 for p in pr_slim if p['merged'])})")
    # 3. branches
    branches = api("branches", {"per_page": 100})
    json.dump([{"name": b["name"], "sha": b["commit"]["sha"][:9]} for b in branches],
              open(f"{OUT}/branches.json", "w"), indent=0)
    print(f"branches: {len(branches)}")
    # 4. repo meta via git (API meta endpoint not token-accessible)
    head = subprocess.run(["git", "rev-parse", "--short=9", "origin/main"],
                          capture_output=True, text=True).stdout.strip()
    print(f"main: {head}")


if __name__ == "__main__":
    main()
