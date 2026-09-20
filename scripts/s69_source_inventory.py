#!/usr/bin/env python3
"""S69 SOURCE-LINKED CAMPAIGN — source inventory builder.

§1 SOURCE-FIRST: for every canonical corpus APK:
  1. extract packageName + versionCode (androguard, authoritative from DEX/manifest)
  2. fetch fdroiddata build metadata (authoritative upstream: SourceCode + per-
     versionCode commit pins — exactly what F-Droid built the APK from)
  3. download the source tarball at the pinned commit (codeload; no API quota)
  4. record PROVENANCE.json (url, commit, sha256, fetched_at) + inventory.json

Nothing here guesses: if metadata lacks the versionCode, the entry is recorded
as UNPINNED with the metadata facts present. No fake evidence.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

ROOT = Path("/home/z/my-project")
CORPUS = ROOT / "upload" / "canonical_apks"
OUT = ROOT / "upstream" / "corpus"
FD_DATA = "https://gitlab.com/fdroid/fdroiddata/-/raw/master/metadata/{}.yml"
CODELOAD = "https://codeload.github.com/{}/tar.gz/{}"

APKS = sorted(p for p in CORPUS.glob("*.apk"))

os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def apk_identity(apk: Path) -> dict:
    """packageName + versionCode straight from the APK via androguard."""
    from androguard.core.apk import APK
    a = APK(str(apk))
    return {
        "apk": apk.name,
        "apk_sha256": sha256_file(apk),
        "package": a.get_package(),
        "versionCode": a.get_androidversion_code(),
        "versionName": a.get_androidversion_name(),
        "minSdk": a.get_min_sdk_version(),
        "targetSdk": a.get_target_sdk_version(),
    }


def fetch(url: str, timeout: int = 60) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": "miniandroid-s69/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f"    fetch failed: {url}: {e}", file=sys.stderr)
        return None


def fdroid_meta(pkg: str) -> dict:
    """Parse the small subset of fdroiddata YAML we need (SourceCode/Repo/Builds)."""
    raw = fetch(FD_DATA.format(pkg))
    if not raw:
        return {}
    text = raw.decode("utf-8", "replace")
    meta: dict = {}
    m = re.search(r"^SourceCode:\s*(\S+)", text, re.M)
    if m:
        meta["source_code"] = m.group(1)
    m = re.search(r"^Repo:\s*(\S+)", text, re.M)
    if m:
        meta["repo"] = m.group(1)
    builds = []
    # crude but robust block split: top-level "  - versionName:" entries
    for block in re.split(r"\n  - versionName:", text)[1:]:
        b = {"versionName": block.split("\n")[0].strip().strip("'\"")}
        m = re.search(r"^\s+versionCode:\s*'?\"?(\d+)", block, re.M)
        if m:
            b["versionCode"] = int(m.group(1))
        # commit may be a hex SHA *or* a tag name (e.g. "v1.0.0", "1")
        m = re.search(r"^\s+commit:\s*'?\"?([^\s'\"]+)", block, re.M)
        if m:
            b["commit"] = m.group(1)
        m = re.search(r"^\s+subdir:\s*(\S+)", block, re.M)
        if m:
            b["subdir"] = m.group(1)
        builds.append(b)
    meta["builds"] = builds
    return meta


def github_repo_slug(url: str) -> str | None:
    m = re.search(r"https://(github\.com)/([^/]+/[^/]+?)(\.git)?/?$", url)
    if m:
        return m.group(2)
    return None


def download_tarball(slug: str, commit: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    data = fetch(CODELOAD.format(slug, commit), timeout=180)
    if not data:
        return False
    dest.write_bytes(data)
    return True


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = []
    for apk in APKS:
        ident = apk_identity(apk)
        pkg = ident["package"]
        vc = int(ident["versionCode"] or 0)
        print(f"[{apk.name}] {pkg} vc={vc}")
        entry = dict(ident)
        entry["fdroid"] = {}
        meta = fdroid_meta(pkg)
        time.sleep(0.3)
        if meta:
            entry["fdroid"] = {k: meta.get(k) for k in ("source_code", "repo")}
            build = next((b for b in meta.get("builds", []) if b.get("versionCode") == vc), None)
            entry["fdroid_build_pin"] = build or None
            slug = github_repo_slug(build and meta.get("repo") or meta.get("source_code") or "")
            commit = build and build.get("commit")
            if slug and commit:
                slug = slug.rstrip("/").removesuffix(".git")
                tdir = OUT / pkg
                tdir.mkdir(exist_ok=True)
                tgz = tdir / f"source_{commit}.tar.gz"
                ok = download_tarball(slug, commit, tgz)
                if ok:
                    # extract once (idempotent)
                    marker = tdir / f".extracted_{commit}"
                    if not marker.exists():
                        try:
                            with tarfile.open(tgz, "r:gz") as tf:
                                tf.extractall(tdir / "src")
                            marker.touch()
                        except Exception as e:
                            print(f"    extract failed: {e}", file=sys.stderr)
                    prov = {
                        "apk": apk.name,
                        "package": pkg,
                        "versionCode": vc,
                        "source_repo": slug,
                        "source_commit": commit,
                        "tarball_sha256": sha256_file(tgz),
                        "tarball_bytes": tgz.stat().st_size,
                        "extracted": (tdir / "src").exists(),
                        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "metadata_origin": FD_DATA.format(pkg),
                        "codeload_origin": CODELOAD.format(slug, commit),
                    }
                    (tdir / "PROVENANCE.json").write_text(json.dumps(prov, indent=1))
                    entry["pinned"] = True
                    entry["provenance"] = prov
                    print(f"    PINNED {slug}@{commit} ({prov['tarball_bytes']} B)")
                else:
                    entry["pinned"] = False
                    entry["pin_error"] = f"tarball fetch failed for {slug}@{commit}"
                    print("    UNPINNED (tarball fetch failed)")
            else:
                entry["pinned"] = False
                entry["pin_error"] = "no slug/commit resolved from fdroid metadata"
                print("    UNPINNED (no slug/commit)")
        else:
            entry["pinned"] = False
            entry["pin_error"] = "fdroiddata metadata fetch failed"
            print("    UNPINNED (no metadata)")
        inventory.append(entry)

    out_json = ROOT / "docs" / "foundation" / "source_inventory.json"
    out_json.write_text(json.dumps({"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                    "apks": inventory}, indent=1))
    pinned = sum(1 for e in inventory if e.get("pinned"))
    print(f"\nSUMMARY: {pinned}/{len(inventory)} APKs pinned → {out_json}")


if __name__ == "__main__":
    main()
