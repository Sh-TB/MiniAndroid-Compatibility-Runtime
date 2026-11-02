#!/usr/bin/env python3
"""s150: publish (or idempotently refresh) a GitHub Release for an existing tag.

Token resolution: `git credential fill` (never printed, never stored).
Body source: --body-file, or extracted from miniandroid/CHANGELOG.md section
`## [<tag>]` via --from-changelog.
"""
import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
CHANGELOG = "miniandroid/CHANGELOG.md"
CHANGELOG_URL = (
    "https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/"
    "blob/main/miniandroid/CHANGELOG.md"
)


def resolve_token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    sys.exit("ERROR: no github.com credential available via git credential fill")


def api(method, path, tok, payload=None):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{path}",
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "miniandroid-release-script",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def changelog_section(tag):
    text = open(CHANGELOG, encoding="utf-8").read()
    marker = f"## [{tag}]"
    start = text.index(marker)
    nxt = text.find("\n## [", start + 1)
    section = text[start : nxt if nxt != -1 else None].rstrip()
    return section + "\n"


def build_header():
    return (
        "> **Full standard changelog:** "
        f"[`miniandroid/CHANGELOG.md`]({CHANGELOG_URL}) · "
        "**Artifacts:** none packaged for this point release (source tag; "
        "build from source) · **Evidence:** "
        "`docs/releases/RELEASE_MANIFEST.json`\n\n---\n\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file")
    ap.add_argument("--from-changelog", action="store_true")
    ap.add_argument("--prerelease", action="store_true")
    args = ap.parse_args()

    if args.from_changelog:
        body = changelog_section(args.tag)
    elif args.body_file:
        body = open(args.body_file, encoding="utf-8").read()
    else:
        sys.exit("ERROR: need --body-file or --from-changelog")

    payload = {
        "tag_name": args.tag,
        "name": args.title,
        "body": build_header() + body,
        "draft": False,
        "prerelease": args.prerelease,
    }
    tok = resolve_token()

    status, rel = api("GET", f"releases/tags/{args.tag}", tok)
    if status == 200:
        status, rel = api("PATCH", f"releases/{rel['id']}", tok, payload)
        action = "REFRESHED"
    else:
        status, rel = api("POST", "releases", tok, payload)
        action = "CREATED"

    if status in (200, 201):
        print(f"{action} release for {args.tag} (http {status})")
        print(f"  name: {rel.get('name')}")
        print(f"  url:  {rel.get('html_url')}")
        print(f"  body: {len(rel.get('body') or '')} chars")
    else:
        print(f"FAILED (http {status}): {json.dumps(rel)[:400]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
