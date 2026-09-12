#!/usr/bin/env python3
"""
scripts/test/fetch_master_campaign.py — AE gate: restore the 7 wave-2 master_campaign APKs
from docs/evidence/master_campaign/registry_additions.json (frozen sources +
SHA-256). Idempotent, hash-verified, zero-skip-law companion to
scripts/test/fetch_corpus.py (which covers tests/corpus/apks.json only).
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REG = REPO / "docs" / "evidence" / "master_campaign" / "registry_additions.json"
CACHE = REPO / "miniandroid" / "download" / "master_campaign"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    reg = json.loads(REG.read_text())
    entries = reg.get("frozen_on_fetch", [])
    want = [w.lower() for w in sys.argv[1:]] or None
    failures = 0
    for e in entries:
        name = e.get("name", "?")
        if want and not any(w in name.lower() for w in want):
            continue
        url = e.get("source", "")
        digest = e.get("sha256", "")
        pkg = e.get("package", "unknown")
        # local filename = <package>_<vc>.apk convention recorded in phase0 rels
        vc = e.get("version_code", 0)
        dest = CACHE / f"{pkg}_{vc}.apk"
        if dest.exists() and sha256(dest) == digest:
            print(f"FOUND    {name}: {dest} (hash OK)")
            continue
        if dest.exists():
            print(f"MISMATCH {name}: {dest} — refetching")
            dest.unlink()
        if not url:
            print(f"MISSING  {name}: no source URL in registry")
            failures += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            print(f"DOWNLOAD {name}: {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                dest.write_bytes(resp.read())
            actual = sha256(dest)
            if actual == digest:
                print(f"OK       {name} sha256={actual[:16]}…")
            else:
                print(f"HASH MISMATCH {name}: expected {digest[:16]}… got {actual[:16]}…")
                failures += 1
        except Exception as exc:  # noqa: BLE001 — report, never swallow
            print(f"MISSING  {name}: download failed ({exc})")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
