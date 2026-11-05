#!/usr/bin/env python3
"""s173_sweep.py — post-verdict sweep: any coder activity after our S173
post (6669725035) on #518 / #522 / #525?"""
import json
import subprocess

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUR_POST = 6669725035


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""


def api(path):
    r = subprocess.run(
        ["curl", "-s", f"https://api.github.com/repos/{REPO}/{path}",
         "-H", f"Authorization: token {token()}"],
        capture_output=True, text=True)
    return json.loads(r.stdout)


def main():
    newest = 0
    for num in (518, 522, 525):
        cs = api(f"issues/{num}/comments?per_page=100")
        if not isinstance(cs, list):
            print(num, "ERR", str(cs)[:120])
            continue
        for c in cs:
            cid = c["id"]
            if cid > OUR_POST and cid != OUR_POST:
                print(f"#{num} NEW {cid} {c['created_at']} "
                      f"{c['user']['login']}: "
                      f"{c['body'][:100]!r}")
            newest = max(newest, cid)
        print(f"#{num}: {len(cs)} comments, newest {newest}")
    il = api("issues?state=all&sort=created&direction=desc&per_page=5")
    print("newest issues:", [(i["number"], i["created_at"])
                              for i in il][:5])


if __name__ == '__main__':
    main()
