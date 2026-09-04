#!/usr/bin/env python3
"""
EXP-083 Phase 39.11 — APK corpus resolver.

Reads tests/corpus/apks.json and:
  - Verifies each APK exists locally with matching SHA256
  - Reports: APK FOUND / APK MISSING / HASH MATCH / HASH MISMATCH
  - Optionally fetches missing APKs from download_url

Usage:
    python tools/resolve_corpus.py                # check status
    python tools/resolve_corpus.py --fetch       # fetch missing APKs
    python tools/resolve_corpus.py --json         # JSON output
    python tools/resolve_corpus.py --name gmdice  # check specific APK by name
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path


def find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p.parent] + list(p.parents):
        if (parent / ".git").exists():
            return parent
    return p.parent.parent.parent

REPO_ROOT = find_repo_root()
MANIFEST_PATH = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "apks.json"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(p, "rb") as f:
            for blk in iter(lambda: f.read(1 << 20), b""):
                h.update(blk)
        return h.hexdigest()
    except OSError:
        return ""


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(2)
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def check_apk(entry: dict) -> dict:
    """Return status dict for a single APK entry."""
    local_path = REPO_ROOT / entry["local_path"]
    expected_sha = entry.get("sha256", "")
    expected_size = entry.get("expected_size_bytes", 0)

    if not local_path.exists():
        return {
            "name": entry["name"],
            "local_path": entry["local_path"],
            "status": "APK_MISSING",
            "expected_size_bytes": expected_size,
            "actual_size_bytes": 0,
            "expected_sha256": expected_sha,
            "actual_sha256": "",
            "download_url": entry.get("download_url", ""),
            "required_for": entry.get("required_for", []),
        }
    actual_size = local_path.stat().st_size
    actual_sha = sha256_file(local_path)
    if expected_sha and actual_sha != expected_sha:
        return {
            "name": entry["name"],
            "local_path": entry["local_path"],
            "status": "HASH_MISMATCH",
            "expected_size_bytes": expected_size,
            "actual_size_bytes": actual_size,
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "download_url": entry.get("download_url", ""),
            "required_for": entry.get("required_for", []),
        }
    return {
        "name": entry["name"],
        "local_path": entry["local_path"],
        "status": "APK_FOUND",
        "expected_size_bytes": expected_size,
        "actual_size_bytes": actual_size,
        "expected_sha256": expected_sha,
        "actual_sha256": actual_sha,
        "download_url": entry.get("download_url", ""),
        "required_for": entry.get("required_for", []),
    }


def fetch_apk(entry: dict) -> bool:
    """Download an APK from its download_url. Return True on success."""
    url = entry.get("download_url", "")
    if not url:
        print(f"  no download_url for {entry['name']}", file=sys.stderr)
        return False
    local_path = REPO_ROOT / entry["local_path"]
    local_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  fetching {entry['name']} from {url}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MiniAndroid-corpus-resolver/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp, open(local_path, "wb") as f:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
        print(f"  downloaded {entry['name']} ({local_path.stat().st_size} bytes)")
        return True
    except Exception as e:
        print(f"  ERROR fetching {entry['name']}: {e}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true",
                    help="Fetch APKs that are missing.")
    ap.add_argument("--json", action="store_true",
                    help="Output JSON.")
    ap.add_argument("--name", help="Check only the APK with this name.")
    args = ap.parse_args()

    manifest = load_manifest()
    results = []
    for entry in manifest.get("apks", []):
        if args.name and entry["name"] != args.name:
            continue
        status = check_apk(entry)
        results.append(status)
        if args.fetch and status["status"] == "APK_MISSING":
            if fetch_apk(entry):
                # Re-check after fetch
                status = check_apk(entry)
                results[-1] = status

    if args.json:
        print(json.dumps({"results": results, "count": len(results)}, indent=2))
    else:
        for r in results:
            print(f"[{r['status']}] {r['name']:30s} {r['local_path']}")
            if r["status"] == "APK_FOUND":
                print(f"           size={r['actual_size_bytes']:,} sha256={r['actual_sha256'][:16]}…")
            elif r["status"] == "APK_MISSING":
                print(f"           download_url={r['download_url']}")
                print(f"           required_for={r['required_for']}")
            elif r["status"] == "HASH_MISMATCH":
                print(f"           expected={r['expected_sha256'][:16]}…")
                print(f"           actual  ={r['actual_sha256'][:16]}…")

    # Exit code: 0 if all OK, 1 if any missing/mismatch
    bad = sum(1 for r in results if r["status"] != "APK_FOUND")
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
