#!/usr/bin/env python3
"""S186c: fetch the one UNRESOLVED stuck APK (com.vovagorodok.blichess, issue #49)
from its GitHub Releases (F-Droid 404s it — repo archived from F-Droid but the
upstream release exists). Authenticated GitHub API via the project's own git
credential helper (same pattern as s185_post_sqlite_rule.py).
"""
import subprocess, json, urllib.request, sys
from pathlib import Path

DEST = Path('/home/z/my-project/upload/stuck_apks')
PKG = 'com.vovagorodok.blichess'

out = subprocess.run(["git", "credential", "fill"],
                     input="protocol=https\nhost=github.com\n\n",
                     capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
token = None
for line in out.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    sys.exit("NO TOKEN")
HDRS = {"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "s186c-stuck-battery"}

req = urllib.request.Request(
    "https://api.github.com/repos/vovagorodok/blichess/releases?per_page=5",
    headers=HDRS)
with urllib.request.urlopen(req, timeout=30) as r:
    rels = json.load(r)
print("releases:", [rel.get("tag_name") for rel in rels])
apk = None
for rel in rels:
    for a in rel.get("assets", []):
        if a["name"].endswith(".apk"):
            apk = a
            break
    if apk:
        break
if not apk:
    sys.exit("NO APK ASSET")
url = apk["browser_download_url"]
print("fetching", apk["name"], apk["size"], url)
dst = DEST / f"{PKG}.apk"
rr = subprocess.run(["curl", "-fL", "--max-time", "300", "-o", str(dst), url],
                    capture_output=True, timeout=320)
ok = rr.returncode == 0 and dst.exists() and dst.stat().st_size > 10000
print("OK" if ok else "FAIL", dst.stat().st_size if dst.exists() else 0)
# update the manifest so the battery picks it up
manp = Path('/home/z/my-project/evidence/s186_s107/S186C_STUCK_APK_MANIFEST.json')
man = json.load(open(manp))
for res_ in man["results"]:
    if res_["pkg"] == PKG:
        if ok:
            res_.update(status="OK", url=url, path=str(dst),
                        size=dst.stat().st_size,
                        note="GitHub Releases (F-Droid 404); authenticated API")
        else:
            res_["reason"] = "github-release download failed"
man["ok"] = sum(1 for r_ in man["results"] if r_["status"] in ("OK", "CACHED"))
man["unresolved"] = sum(1 for r_ in man["results"] if r_["status"] == "UNRESOLVED")
manp.write_text(json.dumps(man, indent=1))
print("manifest ok/unresolved:", man["ok"], man["unresolved"])
