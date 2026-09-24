#!/usr/bin/env python3
"""S94 Phase A fixup: record verified migrations/alternates for 404'd identities.

Policy: never silently substitute. Each substitution is recorded with
`identity_history` preserving the seed directive's original identity.
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("/home/z/my-project/run/s94/source_mining")


def ls_remote(repo: str):
    url = f"https://github.com/{repo}.git"
    for attempt in range(2):
        try:
            r = subprocess.run(["git", "ls-remote", "--symref", url, "HEAD"],
                               capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                raise RuntimeError("not found / unreachable")
            branch, sha = "unknown", None
            for line in r.stdout.splitlines():
                if line.startswith("ref:") and line.rstrip().endswith("HEAD"):
                    branch = line[len("ref:"):].split("\t")[0].strip()
                elif "\tHEAD" in line:
                    sha = line.split("\t")[0].strip()
            return branch, sha
        except Exception:
            if attempt:
                raise
            time.sleep(1.5)


now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
doc = json.loads((OUT / "repositories.json").read_text())
by_repo = {r["repository"]: r for r in doc["repositories"]}


def refresh(rec):
    branch, sha = ls_remote(rec["repository"])
    rec.update({"status": "VERIFIED", "default_branch": branch, "head_sha": sha,
                "verified_via": "git ls-remote --symref", "last_verified": now})


# 1. MIGRATIONS with identity history preserved
mig = {
    "notofonts/noto-emoji": "googlefonts/noto-emoji",
    "facebookarchive/screenshot-tests-for-android": "facebook/screenshot-tests-for-android",
    "renderdoc/renderdoc": "baldurk/renderdoc",
}
for old, new in mig.items():
    rec = by_repo[old]
    rec["identity_history"] = [{
        "identity": old,
        "finding": "git ls-remote 404 (GitHub prompts for credentials => repo absent/renamed)",
        "date": now}]
    rec["repository"] = new
    rec["url"] = f"https://github.com/{new}"
    rec["directive_note"] += f" | S94 directive listed '{old}'; live canonical location verified as '{new}'"
    refresh(rec)

# 2. OFF-GITHUB canonicals: keep as reference entries, NOT counted as GitHub-verified
for repo, upstream in [("mesa3d/mesa", "https://gitlab.freedesktop.org/mesa/mesa"),
                       ("cairo/cairo", "https://gitlab.freedesktop.org/cairo/cairo"),
                       ("google/minikin", "https://android.googlesource.com/platform/frameworks/minikin")]:
    rec = by_repo[repo]
    rec["status"] = "OFF_GITHUB"
    rec["upstream_url"] = upstream
    rec["error"] = "no GitHub repository at this identity; upstream hosted off-GitHub"
    rec["last_verified"] = now

# 3. aosp-mirror/platform_frameworks_native absent from aosp-mirror ->
#    verified distro fork recorded as separate distinct evidence source
rec = by_repo["aosp-mirror/platform_frameworks_native"]
rec["status"] = "OFF_GITHUB"
rec["upstream_url"] = "https://android.googlesource.com/platform/frameworks/native"
rec["error"] = "aosp-mirror does not carry platform_frameworks_native; upstream is googlesource"
rec["last_verified"] = now
fork = {
    "id": "GFX-SRC-900",
    "repository": "LineageOS/android_frameworks_native",
    "url": "https://github.com/LineageOS/android_frameworks_native",
    "families": ["android-framework", "surfaceflinger", "surface"],
    "priority": "P2",
    "relationship": "FORK_OF:AOSP platform_frameworks_native (LineageOS distro patches)",
    "seed_entry": False,
    "directive_note": "Verified stand-in evidence source for AOSP native surface/libgui laws; upstream canonical is googlesource",
}
branch, sha = ls_remote(fork["repository"])
fork.update({"status": "VERIFIED", "default_branch": branch, "head_sha": sha,
             "verified_via": "git ls-remote --symref", "last_verified": now})
doc["repositories"].append(fork)

# renumber cleanly and recompute
doc["repositories"].sort(key=lambda r: r["id"])
doc["candidates"] = len(doc["repositories"])
ok = [r for r in doc["repositories"] if r["status"] == "VERIFIED"]
doc["verified"] = len(ok)
doc["off_github"] = sum(1 for r in doc["repositories"] if r["status"] == "OFF_GITHUB")
doc["not_verified"] = sum(1 for r in doc["repositories"] if r["status"] not in ("VERIFIED", "OFF_GITHUB"))
doc["distinct_verified_repositories"] = len(ok)
(OUT / "repositories.json").write_text(json.dumps(doc, indent=1))

log = []
for r in doc["repositories"]:
    if r["status"] == "VERIFIED":
        log.append(f"{r['id']} {r['repository']:52s} {r['default_branch']:10s} {r['head_sha'][:12]} [{r['relationship'][:52]}]")
    else:
        log.append(f"{r['id']} {r['repository']:52s} {r['status']:12s} {r.get('error', '')[:80]}")
(OUT / "phase_a_log.txt").write_text("\n".join(log) + "\n")
print(f"FINAL: verified={doc['verified']} off_github={doc['off_github']} not_verified={doc['not_verified']} total={doc['candidates']}")
