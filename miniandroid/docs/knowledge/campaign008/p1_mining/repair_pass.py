#!/usr/bin/env python3
"""Repair pass for P1 mining results:
1. Sequentially retry repos that failed with transient 'Authentication failed'.
2. Refetch fuller license text for UNCLEAR/UNKNOWN licenses and re-classify
   with an extended pattern set (AGPL, OFL, CC0, EPL, LGPL-2-library,
   PNG-Ref, canonical-Zlib, custom-permissive detection).
Updates results.json in place.
"""
import json
import os
import re
import subprocess
import time
import urllib.request

BASE = "/home/z/my-project/scripts/p1_mining"
RESULTS = f"{BASE}/results.json"
UA = {"User-Agent": "miniandroid-mining/009"}
LICENSE_NAMES = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.txt", "NOTICE",
                 "LICENSE.TXT", "LICENSE.GPL", "LICENSE.LGPL", "COPYING.LESSER", "COPYRIGHT",
                 "docs/license.rst"]

results = json.load(open(RESULTS))


def ls_remote_plain(repo, tries=3):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    for i in range(tries):
        p = subprocess.run(["git", "ls-remote", f"https://github.com/{repo}.git", "HEAD"],
                           capture_output=True, text=True, timeout=90, env=env)
        out = (p.stdout or "").strip()
        m = re.match(r"^([0-9a-f]{40})\s+HEAD$", out.splitlines()[0]) if out else None
        if m:
            return m.group(1), None
        err = ((p.stderr or "").strip().splitlines() or ["empty"])[-1]
        time.sleep(2.5)
    return None, err


def fetch(url, timeout=30, max_bytes=5000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(max_bytes).decode("utf-8", errors="replace")


def classify2(t):
    t = t[:2500].lower()
    if "gnu affero general public license" in t:
        return "AGPL-3.0"
    if "gnu library general public license" in t:
        return "LGPL-2.0"
    if "gnu lesser general public license" in t:
        return "LGPL-2.1" if "version 2" in t else "LGPL-3.0" if "version 3" in t else "LGPL"
    if "gnu general public license" in t:
        return "GPL-3.0" if "version 3" in t else "GPL-2.0" if "version 2" in t else "GPL"
    if "sil open font license" in t:
        return "OFL-1.1"
    if "cc0 1.0 universal" in t:
        return "CC0-1.0"
    if "eclipse public license" in t:
        return "EPL-2.0" if "2.0" in t else "EPL"
    if "png reference library license" in t:
        return "PNG-Reference-2"
    if "mozilla public license" in t:
        return "MPL-2.0" if "2.0" in t else "MPL"
    if "apache license" in t or ("version 2.0, january 2004" in t):
        return "Apache-2.0"
    if "zlib/libpng license" in t or ("provided 'as-is', without any express or implied warranty" in t
                                      and "acknowledge" in t and "altered versions" in t):
        return "Zlib"
    if "permission is hereby granted, free of charge" in t:
        return "MIT"
    if "old mit" in t:
        return "MIT-Old"
    if "source code license agreement" in t or "proprietary" in t:
        return "PROPRIETARY-source-available"
    if "boost software license" in t:
        return "BSL-1.0"
    if "the_unlicense" in t or "this is free and unencumbered software" in t:
        return "Unlicense"
    if ("redistribution and use in source and binary forms" in t and "all rights reserved" in t
            and "neither the name" in t):
        return "BSD-3-Clause"
    if "redistribution and use in source and binary forms" in t and "all rights reserved" in t:
        return "BSD-2/3-Clause"
    if "provided 'as-is', without any express or implied warranty" in t:
        return "custom-permissive (Zlib/MIT-style)"
    if "public domain" in t:
        return "PublicDomain"
    return "UNCLEAR-verify-manually"


def refetch_license(repo):
    for name in LICENSE_NAMES:
        try:
            text = fetch(f"https://raw.githubusercontent.com/{repo}/HEAD/{name}")
            if text and len(text.strip()) > 15:
                return classify2(text), f"raw:{name}", text[:220].replace("\n", " ")
        except Exception:  # noqa: BLE001
            continue
    try:
        html = fetch(f"https://github.com/{repo}", max_bytes=900000)
        m = re.search(r'"spdxId":"([^"]+)"', html)
        if m and m.group(1) not in ("NOASSERTION", "Other"):
            return m.group(1), "html:spdxId", ""
        if m:
            return "custom/other (html:NOASSERTION)", "html:spdxId", ""
    except Exception:  # noqa: BLE001
        pass
    return "UNKNOWN-verify-manually", "none", ""


def main():
    # 1) retry commit verification failures
    retried = 0
    for repo, v in list(results.items()):
        if v.get("commit_full"):
            continue
        err = v.get("commit_error", "")
        sha, nerr = ls_remote_plain(repo)
        retried += 1
        if sha:
            v.update(commit=sha[:12], commit_full=sha, commit_error=None)
            lic, src, snip = refetch_license(repo)
            v.update(license=lic, license_source=src, license_snippet=snip)
            print(f"RECOVERED {repo} {sha[:12]} {lic}", flush=True)
        else:
            v["commit_error"] = f"RETRY-FAILED: {nerr}"
            print(f"STILL-DEAD  {repo} | {nerr[:70]}", flush=True)
        time.sleep(1)

    # 2) re-classify unclear/unknown licenses
    for repo, v in results.items():
        if not v.get("commit_full"):
            continue
        if v.get("license") in ("UNCLEAR-verify-manually", "UNKNOWN-verify-manually", "N/A"):
            lic, src, snip = refetch_license(repo)
            v.update(license=lic, license_source=src, license_snippet=snip)
            print(f"RELIC {repo} -> {lic} [{src}]", flush=True)
            time.sleep(0.4)

    json.dump(results, open(RESULTS, "w"), indent=1)
    ok = sum(1 for v in results.values() if v.get("commit_full"))
    bad = [k for k, v in results.items() if not v.get("commit_full")]
    lic_ok = sum(1 for v in results.values() if v.get("commit_full") and
                 v.get("license") not in ("UNKNOWN-verify-manually", "N/A"))
    print(f"TOTAL sha={ok}/{len(results)} license_verified={lic_ok}")
    print("still dead:", bad)


if __name__ == "__main__":
    main()
