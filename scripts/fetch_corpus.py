#!/usr/bin/env python3
"""
fetch_corpus.py — restore the external APK cache from tests/corpus/apks.json.

Zero-skip law (§39) companion: the EXP-085/073/074 suites silently reported
"PASS: 0" after environment resets because miniandroid/download/ vanished.
This script restores the cache with SHA-256 verification and reports
APK FOUND / DOWNLOADED / HASH MISMATCH / MISSING per entry.
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]  # scripts/fetch_corpus.py -> repo root
MANIFEST = REPO / "miniandroid" / "tests" / "corpus" / "apks.json"
CACHE = REPO / "miniandroid" / "download"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    want = sys.argv[1:] or None  # optional name filters
    failures = 0
    fetched = 0
    for entry in manifest["apks"]:
        name = entry["name"]
        if want and not any(w.lower() in name.lower() for w in want):
            continue
        url = entry.get("download_url", "")
        rel = entry.get("local_path", "")
        if not url or not rel:
            print(f"SKIP-ENTRY {name}: no url/local_path")
            continue
        # local_path in the manifest is repo-root-relative already
        dest = REPO / rel
        if dest.exists():
            actual = sha256(dest)
            if actual == entry["sha256"]:
                print(f"FOUND       {name}: {dest} (hash OK)")
            else:
                print(f"HASH MISMATCH {name}: {dest}")
                print(f"  expected {entry['sha256']}")
                print(f"  actual   {actual}")
                failures += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            print(f"DOWNLOAD    {name}: {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                dest.write_bytes(resp.read())
        except Exception as e:
            print(f"MISSING     {name}: download failed ({e})")
            failures += 1
            continue
        actual = sha256(dest)
        if actual == entry["sha256"]:
            print(f"OK          {name}: hash match ({actual[:16]}…)")
            fetched += 1
        else:
            print(f"HASH MISMATCH {name}: expected {entry['sha256']}, got {actual}")
            failures += 1
    print(f"\nsummary: fetched={fetched} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
