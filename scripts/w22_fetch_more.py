#!/usr/bin/env python3
"""w22_fetch_more.py — fetch comments for evidence-lane issues (619, 615, 618,
613, 605, 583, 582) + download user-attachment assets found in fetched comments."""
import json
import os
import re
import subprocess
import time
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
RAW = "/home/z/my-project/evidence/w22/issues_raw"
EXTRA = [619, 615, 618, 613, 605, 583, 582]


def get_token():
    q = b"protocol=https\nhost=github.com\n\n"
    r = subprocess.run(["git", "credential", "fill"], input=q,
                       capture_output=True)
    for line in r.stdout.decode().splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    raise SystemExit("NO_TOKEN")


def api(path, tok):
    req = urllib.request.Request(
        "https://api.github.com%s" % path,
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "w22-knowledge-recovery"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


tok = get_token()
for n in EXTRA:
    cs = api("/repos/%s/issues/%d/comments?per_page=100" % (REPO, n), tok)
    with open("%s/comments_%d.json" % (RAW, n), "w") as f:
        json.dump(cs, f)
    print("COMMENTS %d -> %d" % (n, len(cs)))
    time.sleep(0.15)

# download attachments found anywhere in fetched comments
assets = set()
for fn in os.listdir(RAW):
    if fn.startswith("comments_") and fn.endswith(".json"):
        for c in json.load(open(os.path.join(RAW, fn))):
            body = c.get("body") or ""
            for u in re.findall(r"https://github\.com/user-attachments/[^\s\)\"]+",
                                body):
                assets.add(u)
print("ASSETS %d" % len(assets))
os.makedirs(RAW + "/assets", exist_ok=True)
for u in sorted(assets):
    name = u.split("/")[-1].split("?")[0]
    outp = "%s/assets/%s" % (RAW, name)
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "w22"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        with open(outp, "wb") as f:
            f.write(data)
        print("SAVED %s %dB" % (name, len(data)))
    except Exception as e:
        print("FAIL %s %s" % (name, e))
    time.sleep(0.2)
print("DONE")
