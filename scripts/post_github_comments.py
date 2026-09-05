#!/usr/bin/env python3
"""Post the 11 prepared campaign-evidence comments to GitHub.

Security: the token is read from /home/z/.gh_token (mode 600, outside the git
worktree). It is never printed, never embedded in this file, never sent
anywhere except api.github.com via the Authorization header.
"""
import json
import ssl
import sys
import urllib.request
import urllib.error

sys.path.insert(0, "/home/z/my-project/scripts")
from github_comment_texts import ISSUE_TITLE, ISSUE_BODY, COMMENTS

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"
TOKEN_PATH = "/home/z/.gh_token"
RESULTS_PATH = "/home/z/my-project/scripts/comment_urls.json"


def api_request(url, method="GET", payload=None):
    with open(TOKEN_PATH, "r", encoding="utf-8") as fh:
        token = fh.read().strip()
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "miniandroid-campaign-evidence")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        # Defensive: make sure a token never leaks into an error message.
        detail = detail.replace(token, "<token>")
        return e.code, {"error": detail}
    except Exception as e:  # network-level failure
        return 0, {"error": f"{type(e).__name__}: {e}"}


def main():
    # --- authenticated verification (re-check inside the poster) ---
    status, me = api_request("https://api.github.com/user")
    if status != 200:
        print(f"AUTH_VERIFY_FAILED: HTTP {status}: {me.get('error', '')[:300]}")
        sys.exit(2)
    print(f"AUTH_OK as user: {me.get('login')}")

    status, repo = api_request(API)
    if status != 200:
        print(f"REPO_ACCESS_FAILED: HTTP {status}")
        sys.exit(2)
    perms = repo.get("permissions", {})
    print(f"REPO_OK: {repo.get('full_name')} push={perms.get('push')} admin={perms.get('admin')}")
    if not perms.get("push"):
        print("WRITE_CAPABILITY_ABSENT — aborting before any write.")
        sys.exit(3)

    # --- find suitable existing issue, else create the evidence anchor ---
    status, issues = api_request(f"{API}/issues?state=all&per_page=100")
    if status != 200:
        print(f"ISSUE_LIST_FAILED: HTTP {status}")
        sys.exit(2)
    target = None
    for it in issues:
        if "pull_request" not in it and "campaign evidence" in it.get("title", "").lower():
            target = it
            break
    if target:
        print(f"USING_EXISTING_ISSUE: #{target['number']} {target['title']}")
    else:
        status, target = api_request(f"{API}/issues", "POST", {
            "title": ISSUE_TITLE, "body": ISSUE_BODY,
            "labels": ["documentation", "evidence"],
        })
        if status not in (200, 201):
            print(f"ISSUE_CREATE_FAILED: HTTP {status}: {target.get('error', '')[:300]}")
            sys.exit(2)
        print(f"ISSUE_CREATED: #{target['number']} -> {target['html_url']}")

    issue_no = target["number"]

    # --- guard against double-posting on rerun ---
    status, existing = api_request(f"{API}/issues/{issue_no}/comments?per_page=100")
    existing_first_lines = set()
    if status == 200:
        for c in existing:
            lines = c.get("body", "").lstrip().splitlines()
            if lines:
                existing_first_lines.add(lines[0][:120])

    # --- post the 11 comments ---
    results = []
    for title, body in COMMENTS:
        first_line = body.lstrip().splitlines()[0][:120]
        if first_line in existing_first_lines:
            print(f"SKIP (already posted): {title}")
            results.append({"n": title, "status": "SKIPPED_ALREADY_POSTED", "url": None})
            continue
        status, resp = api_request(f"{API}/issues/{issue_no}/comments", "POST", {"body": body})
        if status == 201:
            url = resp.get("html_url")
            print(f"POSTED: {title} -> {url}")
            results.append({"n": title, "status": "POSTED", "url": url})
        else:
            print(f"FAILED: {title} | HTTP {status} | {resp.get('error', '')[:300]}")
            results.append({"n": title, "status": f"FAILED_HTTP_{status}", "url": None,
                            "error": resp.get("error", "")[:300]})

    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump({"issue": target.get("html_url"), "issue_number": issue_no,
                   "results": results}, fh, ensure_ascii=False, indent=2)

    ok = sum(1 for r in results if r["status"] in ("POSTED", "SKIPPED_ALREADY_POSTED"))
    print(f"SUMMARY: {ok}/{len(results)} comments present on GitHub; issue #{issue_no}")


if __name__ == "__main__":
    main()
