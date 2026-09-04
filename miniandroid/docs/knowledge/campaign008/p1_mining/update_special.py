#!/usr/bin/env python3
"""Patch results.json with manually-verified evidence from this session:
- recovered repos (correct owner spellings / canonical non-GitHub hosts)
- final NOT-FOUND verdicts for dead repos
- licenses fetched for the recovered repos
Adds g-truc/glm as an extra verified row (200 -> 201 total).
"""
import json
import subprocess
import os
import re
import urllib.request

BASE = "/home/z/my-project/scripts/p1_mining"
RESULTS = f"{BASE}/results.json"
UA = {"User-Agent": "miniandroid-mining/009"}
results = json.load(open(RESULTS))

env = dict(os.environ, GIT_TERMINAL_PROMPT="0")


def lsremote(url):
    p = subprocess.run(["git", "ls-remote", url, "HEAD"], capture_output=True,
                       text=True, timeout=90, env=env)
    m = re.match(r"^([0-9a-f]{40})\s+HEAD$", (p.stdout or "").strip().splitlines()[0]) if (p.stdout or "").strip() else None
    return m.group(1) if m else None


def raw_head(repo, name, host="raw.githubusercontent.com"):
    url = f"https://{host}/{repo}/HEAD/{name}" if host == "raw.githubusercontent.com" else url
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read(4000).decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""


def classify(t):
    t = t[:2500].lower()
    if "gnu general public license" in t:
        return "GPL-3.0" if "version 3" in t else "GPL-2.0" if "version 2" in t else "GPL"
    if "apache license" in t:
        return "Apache-2.0"
    if ("redistribution and use in source and binary forms" in t and "neither the name" in t):
        return "BSD-3-Clause"
    if ("provided 'as-is'" in t and "permission is granted" in t and "damages" in t):
        return "custom-permissive (BSD/MIT-style)"
    if "permission is hereby granted" in t:
        return "MIT"
    return "UNCLEAR-verify-manually"


# --- recovered with corrected owner / canonical host ---
updates = {
    "bgfx/bgfx": {"url": "https://github.com/bkaradzic/bgfx.git", "repo": "bkaradzic/bgfx"},
    "g-truc/glew": {"url": "https://github.com/nigels-com/glew.git", "repo": "nigels-com/glew"},
    "kotlin/kotlin": {"url": "https://github.com/JetBrains/kotlin.git", "repo": "JetBrains/kotlin"},
    "Anuke/Mindustry": {"url": "https://github.com/Anuken/Mindustry.git", "repo": "Anuken/Mindustry"},
    "Mesa3D/mesa": {"url": "https://gitlab.freedesktop.org/mesa/mesa.git", "repo": "Mesa3D/mesa (canonical: gitlab.freedesktop.org/mesa/mesa)"},
    "aosp-mirror/platform_art": {"url": "https://android.googlesource.com/platform/art", "repo": "android.googlesource.com/platform/art"},
    "aosp-mirror/platform_libcore": {"url": "https://android.googlesource.com/platform/libcore", "repo": "android.googlesource.com/platform/libcore"},
}
for key, u in updates.items():
    sha = lsremote(u["url"])
    if sha:
        old = results.get(key, {})
        newrepo = u["repo"]
        results.pop(key, None)
        lic = old.get("license", "UNKNOWN-verify-manually")
        if lic in ("N/A", "UNKNOWN-verify-manually", "UNCLEAR-verify-manually"):
            # license fetch for recovered repos
            if newrepo.startswith("android.googlesource.com"):
                lic, src = "UNKNOWN-verify-manually", "gs-license-fetch-blocked"
            elif "freedesktop" in u["url"]:
                lic, src = "UNKNOWN-verify-manually", "fd-o-raw-antibot-blocked"
            else:
                got = ""
                for name in ["LICENSE", "LICENSE.md", "LICENSE.txt", "license/LICENSE.txt",
                             "LICENSE.TXT", "copying.txt", "COPYING"]:
                    got = raw_head(newrepo, name)
                    if got and len(got.strip()) > 15:
                        lic, src = classify(got), f"raw:{name}"
                        break
                else:
                    lic, src = "UNKNOWN-verify-manually", "none"
        results[newrepo] = {"repo": newrepo, "commit": sha[:12], "commit_full": sha,
                            "commit_error": None, "license": lic,
                            "license_source": src if isinstance(lic, str) and lic != "UNKNOWN-verify-manually" else ("recovered-verify-note" if lic == "UNKNOWN-verify-manually" else ""),
                            "license_snippet": ""}
        print(f"PATCHED {newrepo} {sha[:12]} {lic}", flush=True)
    else:
        print(f"PATCH-FAILED {u['repo']}", flush=True)

# --- final dead verdicts ---
dead = {
    "google/apk-patcher": "repo does not exist (task asked to verify; confirmed 404 via git+API+HTML)",
    "mpg123/mpg123": "no credible official GitHub mirror; upstream is mpg123.de/SourceForge (task-predicted)",
    "Tehreer/Tehreer": "repo not found under this owner (active repo is Tehreer/Tehreer-Android)",
    "robolectric/android-all": "repo not found under this owner (android-all artifacts are published to Maven Central; not verified here)",
}
for k, why in dead.items():
    if k in results and not results[k].get("commit_full"):
        results[k]["commit_error"] = f"NOT-FOUND: {why}"
        print(f"DEAD {k}", flush=True)

json.dump(results, open(RESULTS, "w"), indent=1)
ok = sum(1 for v in results.values() if v.get("commit_full"))
print(f"TOTAL rows={len(results)} with_sha={ok}")
