#!/usr/bin/env python3
"""s99_refetch_broken.py — re-download truncated APKs (curl partial kills).

S99 fetch produced files without an EOCD marker (server/proxy closed the
stream early; curl -s swallowed rc=18). This script finds every APK in
run/s99/apks that is not a valid ZIP, deletes it, and re-downloads with
resume + retry + size/EOCD verification loop (max 4 attempts).
"""
import hashlib
import json
import os
import struct
import subprocess
import sys

ROOT = "/home/z/my-project"
APKS = f"{ROOT}/run/s99/apks"
UA = "Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-S99-fullload/1.0"
MANIFEST = f"{ROOT}/run/s99/apk_manifest.json"


def valid_zip(p):
    try:
        data = open(p, "rb").read()
        return data.rfind(b"PK\x05\x06") != -1 and data.rfind(b"PK\x01\x02") != -1
    except Exception:
        return False


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    man = json.load(open(MANIFEST))
    by_pkg = {r["package"]: r for r in man}
    broken = []
    for fn in sorted(os.listdir(APKS)):
        if not fn.endswith(".apk"):
            continue
        p = os.path.join(APKS, fn)
        if not valid_zip(p):
            broken.append(fn[:-4])
    print(f"broken APKs: {len(broken)}: {broken}")
    fixed, still = [], []
    for pkg in broken:
        rec = by_pkg.get(pkg, {})
        vc = rec.get("versionCode")
        if not vc:
            still.append((pkg, "NO_VERSIONCODE"))
            continue
        url = f"https://f-droid.org/repo/{pkg}_{vc}.apk"
        dest = f"{APKS}/{pkg}.apk"
        ok = False
        for attempt in range(1, 5):
            if os.path.exists(dest):
                os.remove(dest)
            r = subprocess.run(
                ["curl", "-sS", "-L", "--retry", "2", "-C", "-", "-m", "500",
                 "-A", UA, "-o", dest, url], capture_output=True)
            if r.returncode == 0 and os.path.exists(dest) and valid_zip(dest):
                ok = True
                break
            print(f"  [{pkg}] attempt {attempt} failed rc={r.returncode} "
                  f"size={os.path.getsize(dest) if os.path.exists(dest) else 0}",
                  flush=True)
        if ok:
            size = os.path.getsize(dest)
            rec.update({"status": "SOURCED", "sha256": sha256(dest),
                        "size": size, "url": url, "refetched": True})
            fixed.append(pkg)
            print(f"  [FIXED] {pkg} ({size//1024}KB)", flush=True)
        else:
            still.append((pkg, "RETRY_EXHAUSTED"))
    json.dump(list(by_pkg.values()), open(MANIFEST, "w"), indent=1)
    print(f"\nfixed: {len(fixed)}  still-broken: {still}")


if __name__ == "__main__":
    main()
