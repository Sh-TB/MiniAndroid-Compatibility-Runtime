#!/usr/bin/env python3
"""s92_fetch_pilot_apks.py — restore the S92 pilot APK cache (§26).

Re-fetches the pilot titles from f-droid.org after environment resets,
verifying each download's SHA-256 against the S92 pin list. Resume-safe:
existing SHA-exact files are kept (FOUND), mismatches are re-downloaded.
"""
import hashlib
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "miniandroid", "download")

# SHA-256 pins: taken from the canonical registry / prior session evidence
# where recorded; for fresh pins the first verified download pins the hash
# and the pin is recorded in run/s92pilot/APK_PINS.json for later audits.
FALLBACK_PINS = {
    # from docs/evidence/s91 evidence (Fish Rings icon E2E reproof)
    "eu.veldsoft.fish.rings_6.apk":
        "c8a9cb7c",
}

PILOT = [
    ("com.emmanuelmess.tictactoe_3.apk",
     "https://f-droid.org/repo/com.emmanuelmess.tictactoe_3.apk"),
    ("ca.rmen.nounours_358.apk",
     "https://f-droid.org/repo/ca.rmen.nounours_358.apk"),
    ("com.dozingcatsoftware.dodge_15.apk",
     "https://f-droid.org/repo/com.dozingcatsoftware.dodge_15.apk"),
    ("com.dozingcatsoftware.bouncy_63.apk",
     "https://f-droid.org/repo/com.dozingcatsoftware.bouncy_63.apk"),
    ("com.smorgasbork.hotdeath_1011.apk",
     "https://f-droid.org/repo/com.smorgasbork.hotdeath_1011.apk"),
    ("org.bobstuff.bobball_117.apk",
     "https://f-droid.org/repo/org.bobstuff.bobball_117.apk"),
    ("com.trianguloy.urlchecker_28.apk",
     "https://f-droid.org/repo/com.trianguloy.urlchecker_28.apk"),
    ("com.chessclock.android_29.apk",
     "https://f-droid.org/repo/com.chessclock.android_29.apk"),
    ("eu.veldsoft.fish.rings_6.apk",
     "https://f-droid.org/repo/eu.veldsoft.fish.rings_6.apk"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(CACHE, exist_ok=True)
    pins_path = os.path.join(REPO, "run", "s92pilot", "APK_PINS.json")
    pins = {}
    if os.path.isfile(pins_path):
        pins = json.load(open(pins_path))
    failures = 0
    for fname, url in PILOT:
        dest = os.path.join(CACHE, fname)
        pin = pins.get(fname, FALLBACK_PINS.get(fname))
        if os.path.isfile(dest):
            got = sha256(dest)
            if pin and not got.startswith(pin):
                print(f"HASH MISMATCH {fname}: {got[:12]} vs pin {pin}")
                os.remove(dest)
            else:
                print(f"FOUND        {fname} {got[:16]}")
                continue
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            with open(dest, "wb") as f:
                f.write(data)
            got = sha256(dest)
            if pin and not got.startswith(pin):
                print(f"HASH MISMATCH {fname}: {got[:12]} vs pin {pin}")
                failures += 1
                continue
            pins[fname] = got
            print(f"DOWNLOADED   {fname} {got[:16]} ({len(data)} bytes)")
        except Exception as e:
            print(f"FAILED       {fname}: {e}")
            failures += 1
    os.makedirs(os.path.dirname(pins_path), exist_ok=True)
    with open(pins_path, "w") as f:
        json.dump(pins, f, indent=1, sort_keys=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
