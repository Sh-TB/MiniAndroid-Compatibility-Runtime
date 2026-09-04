#!/usr/bin/env python3
"""
P1-GITHUB-MINING batch verifier (Campaign 009).

For every repo in the master list this script gathers LIVE evidence only:
  1. HEAD commit SHA via `git ls-remote https://github.com/OWNER/REPO.git HEAD`
     (no GitHub API quota consumed).
  2. License text via raw.githubusercontent.com (LICENSE, LICENSE.md, LICENSE.txt,
     COPYING, COPYING.txt, NOTICE), falling back to the repo HTML page's
     embedded spdxId (server-rendered, no JS/auth needed).
  3. Optional source-inspection: first lines of README.md for designated repos.

Results are cached in results.json keyed by repo so re-runs are incremental.
Nothing is guessed: unknown values are recorded as UNKNOWN-verify-manually.
"""
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

OUT_DIR = "/home/z/my-project/scripts/p1_mining"
RESULTS = os.path.join(OUT_DIR, "results.json")
MASTER = os.path.join(OUT_DIR, "master_repos.txt")  # one "owner/name" per line, optional trailing comment
LICENSE_NAMES = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.txt", "NOTICE"]
UA = {"User-Agent": "miniandroid-mining/009 (research cataloging)"}


def fetch_url(url, timeout=25, max_bytes=4096):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(max_bytes)
    return data.decode("utf-8", errors="replace")


def ls_remote_head(repo):
    """Return (sha, error). Retry once on failure."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/bin/true")
    for attempt in (1, 2):
        try:
            p = subprocess.run(
                ["git", "ls-remote", f"https://github.com/{repo}.git", "HEAD"],
                capture_output=True, text=True, timeout=60, env=env)
            out = (p.stdout or "").strip()
            m = re.match(r"^([0-9a-f]{40})\s+HEAD$", out.splitlines()[0]) if out else None
            if m:
                return m.group(1), None
            err = (p.stderr or "").strip().splitlines()
            errtxt = err[-1] if err else f"empty output rc={p.returncode}"
        except subprocess.TimeoutExpired:
            errtxt = "TIMEOUT"
        except Exception as e:  # noqa: BLE001
            errtxt = f"{type(e).__name__}: {e}"
        if attempt == 1:
            time.sleep(1.5)
    kind = "NOT-FOUND" if ("Username" in errtxt or "Repository not found" in errtxt
                           or "not found" in errtxt.lower()) else "ERROR"
    return None, f"{kind}: {errtxt}"


def classify_license(text):
    if not text:
        return None
    t = text[:1500].lower()
    if "gnu lesser general public license" in t:
        v = "3.0" if "version 3" in t or "gpl-3" in t else ("2.1" if "version 2" in t else "")
        return f"LGPL-{v}" if v else "LGPL"
    if "gnu general public license" in t:
        v = "3" if ("version 3" in t or "gpl-3" in t) else ("2" if "version 2" in t else "")
        return f"GPL-{v}.0" if v else "GPL"
    if "apache license" in t or "apache software foundation" in t:
        return "Apache-2.0" if ("version 2" in t or "2.0" in t) else "Apache"
    if "mozilla public license" in t:
        return "MPL-2.0" if "2.0" in t else "MPL"
    if "permission is hereby granted, free of charge" in t:
        return "MIT"
    if "the_unlicense" in t or "this is free and unencumbered software released into the public domain" in t:
        return "Unlicense"
    if "creative commons" in t:
        return "CC-BY/CC0-check"
    if "zlib" in t and "acknowledge" in t:
        return "Zlib"
    if "boost software license" in t:
        return "BSL-1.0"
    if "isc license" in t or "permission to use, copy, modify, and/or distribute this software" in t:
        return "ISC"
    if "bsd" in t:
        if "3-clause" in t or "redistribution and use in source and binary forms" in t and "neither the name" in t:
            return "BSD-3-Clause"
        if "redistribution and use in source and binary forms" in t:
            return "BSD-2/3-Clause"
        return "BSD"
    if "public domain" in t:
        return "PublicDomain"
    return "UNCLEAR-verify-manually"


def fetch_license(repo):
    """Return (license_label, evidence_source, head_snippet)."""
    for name in LICENSE_NAMES:
        try:
            text = fetch_url(f"https://raw.githubusercontent.com/{repo}/HEAD/{name}")
            if text and len(text.strip()) > 15 and "404" not in text[:40]:
                guess = classify_license(text)
                return (guess or "UNCLEAR-verify-manually"), f"raw:{name}", text[:220].replace("\n", " ")
        except Exception:  # noqa: BLE001
            continue
    # HTML fallback: spdxId embedded in the server-rendered page
    try:
        html = fetch_url(f"https://github.com/{repo}", timeout=30, max_bytes=900000)
        m = re.search(r'"spdxId":"([^"]+)"', html)
        stars = re.search(r'aria-label="([\d.,kK]+) users starred this repository"', html)
        desc = re.search(r'"description":"(.*?)"(?:,|})', html)
        if m and m.group(1) != "NOASSERTION":
            return m.group(1), "html:spdxId", ""
        if "NOASSERTION" in (m.group(1) if m else "") or html:
            extra = ""
            if stars:
                extra += f" stars~{stars.group(1)}"
            return "UNKNOWN-verify-manually", f"html-page{extra}", (desc.group(1)[:160] if desc else "")
    except Exception:  # noqa: BLE001
        pass
    return "UNKNOWN-verify-manually", "none", ""


def fetch_readme(repo, max_bytes=1800):
    for name in ["README.md", "readme.md", "README.rst", "README"]:
        try:
            return fetch_url(f"https://raw.githubusercontent.com/{repo}/HEAD/{name}", max_bytes=max_bytes)
        except Exception:  # noqa: BLE001
            continue
    return ""


def verify_one(repo, want_readme=False):
    entry = {"repo": repo}
    sha, err = ls_remote_head(repo)
    entry["commit"] = sha[:12] if sha else "NOT-FOUND"
    entry["commit_full"] = sha
    entry["commit_error"] = err
    if sha:
        lic, src, snip = fetch_license(repo)
        entry["license"] = lic
        entry["license_source"] = src
        entry["license_snippet"] = snip
        if want_readme:
            entry["readme_head"] = fetch_readme(repo)[:1200].replace("\n", " ¶ ")
    else:
        entry["license"] = "N/A"
        entry["license_source"] = "none"
        entry["license_snippet"] = ""
    return entry


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    repos, flags = [], {}
    with open(MASTER) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            repo = parts[0]
            if repo not in repos:
                repos.append(repo)
            if len(parts) > 1 and parts[1] == "inspect":
                flags[repo] = True

    try:
        results = json.load(open(RESULTS))
    except Exception:  # noqa: BLE001
        results = {}

    todo = [r for r in repos if r not in results or (flags.get(r) and "readme_head" not in results[r])]
    print(f"master={len(repos)} cached={len(results)} todo={len(todo)}", flush=True)

    lock_free = cf.ThreadPoolExecutor(max_workers=12)
    futures = {lock_free.submit(verify_one, r, flags.get(r, False)): r for r in todo}
    done = 0
    for fut in cf.as_completed(futures):
        r = futures[fut]
        try:
            results[r] = fut.result()
        except Exception as e:  # noqa: BLE001
            results[r] = {"repo": r, "commit": "NOT-FOUND", "commit_error": f"script-error: {e}",
                          "license": "UNKNOWN-verify-manually", "license_source": "none"}
        done += 1
        if done % 20 == 0 or done == len(todo):
            print(f"  verified {done}/{len(todo)}", flush=True)
            json.dump(results, open(RESULTS, "w"), indent=1)

    json.dump(results, open(RESULTS, "w"), indent=1)
    ok = sum(1 for v in results.values() if v.get("commit_full"))
    lic = sum(1 for v in results.values() if v.get("license") not in ("N/A", "UNKNOWN-verify-manually"))
    print(f"DONE master={len(repos)} with_sha={ok} with_license={lic}")


if __name__ == "__main__":
    main()
