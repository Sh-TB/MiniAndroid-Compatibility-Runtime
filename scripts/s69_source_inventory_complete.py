#!/usr/bin/env python3
"""S69 — complete the source inventory: retry transient 403s, accept tag-name
commit refs (fdroiddata allows non-hex commits), and pin the three S65
source-first apps from the session ledger (VelbazhdSoftwareLLC TriPeaks/
FishRings, 20Nick/OPMT) whose evidence chain is docs/corpus/SEARCH_LEDGER.md
+ docs/ROADMAP_STATUS.md. Dedupes by package (dooz ×2 APKs)."""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, "/home/z/my-project/scripts")
from s69_source_inventory import (fdroid_meta, github_repo_slug, download_tarball,
                                  fetch, sha256_file, OUT, ROOT, CODELOAD, FD_DATA)

INV = ROOT / "docs" / "foundation" / "source_inventory.json"

# S65/S66 session ledger pins (SHA-verified clones then; ledger-cited now).
LEDGER_PINS = {
    "eu.veldsoft.tri.peaks": ("VelbazhdSoftwareLLC/TriPeaksSolitaireForAndroid",
                              "62f3609", "docs/corpus/SEARCH_LEDGER.md S66 S3"),
    "eu.veldsoft.fish.rings": ("VelbazhdSoftwareLLC/FishRingsForAndroid",
                               "dc3807e", "docs/ROADMAP_STATUS.md (S65 S10)"),
    "one.scarecrow.games.OPMT": ("20Nick/OPMT", "3240c4cf",
                                 "worklog S65 (OPMT @3240c4cf)"),
}

data = json.loads(INV.read_text())
apks = data["apks"]


def robust_meta(pkg: str, tries: int = 4) -> dict:
    for i in range(tries):
        m = fdroid_meta(pkg)
        if m:
            return m
        time.sleep(2.0 * (i + 1))
    return {}


def any_slug(url: str) -> str | None:
    """github.com/o/r | gitlab.com/o/r → normalized host-prefixed slug."""
    if not url:
        return None
    m = re.search(r"https://(github\.com|gitlab\.com)/([^/]+/[^/]+?)(\.git)?/?$", url)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return None


def pin_slug_commit(entry: dict, slug: str, commit: str, origin: str) -> bool:
    slug = slug.rstrip("/").removesuffix(".git")
    pkg = entry["package"]
    tdir = OUT / pkg
    tdir.mkdir(exist_ok=True)
    tgz = tdir / f"source_{commit}.tar.gz"
    if not tgz.exists() or tgz.stat().st_size == 0:
        # GitHub codeload vs GitLab archive endpoint (no API quota on either)
        if slug.startswith("gitlab.com/"):
            project = slug.removeprefix("gitlab.com/")
            gl = f"https://gitlab.com/{project}/-/archive/{commit}/" \
                 f"{project.split('/')[-1]}-{commit}.tar.gz"
            raw = fetch(gl, timeout=180)
            if not raw:
                entry["pin_error"] = f"tarball fetch failed {slug}@{commit}"
                return False
            tgz.write_bytes(raw)
        else:
            bare = slug.removeprefix("github.com/")
            if not download_tarball(bare, commit, tgz):
                entry["pin_error"] = f"tarball fetch failed {slug}@{commit}"
                return False
    marker = tdir / f".extracted_{commit}"
    if not marker.exists():
        import tarfile
        try:
            with tarfile.open(tgz, "r:gz") as tf:
                tf.extractall(tdir / "src")
            marker.touch()
        except Exception as e:
            print(f"    extract failed: {e}", file=sys.stderr)
    prov = {
        "apk": entry["apk"], "package": pkg, "versionCode": entry["versionCode"],
        "source_repo": slug, "source_commit": commit,
        "tarball_sha256": sha256_file(tgz), "tarball_bytes": tgz.stat().st_size,
        "extracted": (tdir / "src").exists(),
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "metadata_origin": origin, "codeload_origin": CODELOAD.format(slug, commit),
    }
    (tdir / "PROVENANCE.json").write_text(json.dumps(prov, indent=1))
    entry["pinned"] = True
    entry["provenance"] = prov
    entry.pop("pin_error", None)
    return True


for e in apks:
    if e.get("pinned"):
        continue
    pkg = e["package"]
    print(f"[retry] {e['apk']} {pkg}")
    if pkg in LEDGER_PINS:
        slug, commit, origin = LEDGER_PINS[pkg]
        ok = pin_slug_commit(e, slug, commit, f"session-ledger:{origin}")
        print(f"    ledger-pin {'OK' if ok else 'FAIL'} {slug}@{commit}")
        continue
    meta = robust_meta(pkg)
    if not meta:
        e["pin_error"] = "fdroiddata metadata fetch failed after retries"
        print("    still no metadata")
        continue
    e["fdroid"] = {k: meta.get(k) for k in ("source_code", "repo")}
    vc = int(e["versionCode"] or 0)
    build = next((b for b in meta.get("builds", []) if b.get("versionCode") == vc), None)
    e["fdroid_build_pin"] = build or None
    if not build:
        e["pin_error"] = f"no fdroid build for versionCode {vc}"
        print(f"    no build for vc={vc}")
        continue
    slug = any_slug(meta.get("repo") or meta.get("source_code") or "")
    commit = build.get("commit")
    if not (slug and commit):
        e["pin_error"] = "no slug/commit in metadata"
        print("    no slug/commit")
        continue
    ok = pin_slug_commit(e, slug, commit, FD_DATA.format(pkg))
    print(f"    {'OK' if ok else 'FAIL'} {slug}@{commit}")

# dedupe: map dooz_23_toplevel → same provenance as the pinned dooz APK
by_pkg = {}
for e in apks:
    if e.get("pinned"):
        by_pkg.setdefault(e["package"], e)
for e in apks:
    if not e.get("pinned") and e["package"] in by_pkg and "fetch failed" in e.get("pin_error", ""):
        src = dict(by_pkg[e["package"]]["provenance"])
        src["apk"] = e["apk"]
        src["note"] = "provenance shared with sibling APK of same package"
        e["pinned"] = True
        e["provenance"] = src
        e.pop("pin_error", None)
        print(f"[dedup] {e['apk']} → {src['source_repo']}@{src['source_commit'][:10]}")

data["apks"] = apks
INV.write_text(json.dumps(data, indent=1))
pinned = sum(1 for e in apks if e.get("pinned"))
print(f"\nSUMMARY: {pinned}/{len(apks)} pinned")
