#!/usr/bin/env python3
"""Download test APKs into an EXTERNAL cache (CAMPAIGN 011 §20/§21).

ZERO-APK policy: no APK may live inside the repository, a release, or a
source ZIP. This script fetches each APK listed in tests/corpus/apks.json
into an external cache directory and verifies its SHA-256.

Usage:
    python3 scripts/download_test_apks.py [--cache-dir DIR] [--only name1,name2]

Default cache dir: $MINIANDROID_APK_CACHE or <repo-parent>/apk_cache
(the default is intentionally OUTSIDE the repository tree).
"""
import argparse
import hashlib
import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "tests" / "corpus" / "apks.json"
DEFAULT_CACHE = Path(os.environ.get("MINIANDROID_APK_CACHE", REPO.parent.parent / "apk_cache"))

# Map registry names -> cache subdir/file layout expected by u011_test_matrix.py
LAYOUT = {
    "Telegram": "exp038_telegram/Telegram.apk",
}


def cache_path(cache: Path, apk: dict) -> Path:
    name = apk["name"]
    if name in LAYOUT:
        return cache / LAYOUT[name]
    safe = name.lower().replace(" ", "").replace("(", "").replace(")", "")
    return cache / "corpus" / f"{safe}.apk"


def fetch(url: str, dest: Path, timeout: int = 300) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "miniandroid-test-fetch/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp, \
                open(dest, "wb") as out:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
        return True
    except Exception as e:
        print(f"  FETCH FAILED: {e}", file=sys.stderr)
        if dest.exists():
            dest.unlink()
        return False


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", default=str(DEFAULT_CACHE))
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    cache = Path(args.cache_dir)

    reg = json.loads(REGISTRY.read_text())
    only = {s.strip().lower() for s in args.only.split(",") if s.strip()}
    ok = missing = bad = 0
    for apk in reg["apks"]:
        name = apk["name"]
        if only and name.lower() not in only:
            continue
        dest = cache_path(cache, apk)
        print(f"{name}:")
        if dest.exists():
            actual = sha256(dest)
            if actual == apk.get("sha256"):
                print(f"  HASH MATCH (cached): {dest}")
                ok += 1
                continue
            print(f"  HASH MISMATCH cached={actual[:16]} expected={apk.get('sha256','?')[:16]} — re-fetching")
            dest.unlink()
        url = apk.get("download_url") or apk.get("source")
        if not url:
            print("  NO DOWNLOAD URL — SKIPPED")
            missing += 1
            continue
        print(f"  downloading {url}")
        if fetch(url, dest):
            actual = sha256(dest)
            if actual == apk.get("sha256"):
                print(f"  HASH MATCH: {dest} ({dest.stat().st_size} bytes)")
                ok += 1
            else:
                print(f"  HASH MISMATCH: got {actual} want {apk.get('sha256')}")
                bad += 1
        else:
            missing += 1
    print(f"\ndone: {ok} ok, {missing} missing/failed, {bad} hash-mismatch")
    print(f"cache (outside repo): {cache}")
    return 0 if (missing == 0 and bad == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
