#!/usr/bin/env python3
"""T279 P1 mining: read GitHub issue data via token from git credential helper.
Token is NEVER printed or stored; only used in-memory for API calls."""
import json
import subprocess
import sys
import urllib.request


def get_token():
    """Read token from the git credential helper at runtime. Never printed."""
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True,
    )
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise RuntimeError("no token from credential helper")


TOKEN = get_token()


def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "t279-agent",
    })
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "ledger"
    if mode == "ledger":
        # #472 comment census (count + subjects only, no full bodies)
        cs = api("https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/472/comments?per_page=100")
        print(f"#472 comments: {len(cs)}")
        for c in cs[-8:]:
            first = c["body"].splitlines()[0][:100] if c["body"] else ""
            print(f"  {c['created_at'][:10]} {len(c['body'])}B: {first}")
    elif mode == "trackers":
        # per-app tracker issues 473..491 titles
        for n in range(473, 492):
            try:
                i = api(f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{n}")
                print(f"#{n} [{i['state']}] {i['title'][:110]}")
            except Exception as e:
                print(f"#{n} ERR {e}")
    elif mode == "issue":
        n = sys.argv[2]
        i = api(f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{n}")
        print(f"#{n} [{i['state']}] {i['title'][:150]}")
        print(i["body"][:3000])


if __name__ == "__main__":
    main()
