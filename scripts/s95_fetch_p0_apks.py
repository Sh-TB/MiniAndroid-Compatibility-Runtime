#!/usr/bin/env python3
"""s95_fetch_p0_apks.py — restore the S95 P0 validation APK set.

Re-fetches the P0 target + control titles from f-droid.org after the
container reset, verifying each download's SHA-256 against the recorded
pins (S92 pilot pins + gap_map.json). Resume-safe: existing SHA-exact
files are kept, mismatches are re-downloaded.

Pins provenance:
  bouncy_43   a509db2a...  (run/s94/source_mining/gap_map.json)
  bobball_26  fd43009a...  (run/s94/source_mining/gap_map.json)
  dodge_10    a5687d1b...  (docs/evidence/canonical/registry.json)
  hotdeath_11 8e6c19ea...  (docs/evidence/canonical/registry.json)
  urlchecker_28 50872227-prefix recorded in S92/S93 docs (pin prefix only
              -> full SHA verified at first fetch and re-pinned)
  simplestopwatch_26 / unote_30 / nounours_358 / gmdice_8 (S92/S93 pins;
  re-pinned at first verified fetch if absent)
"""
import hashlib
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "miniandroid", "download")
PINS_PATH = os.path.join(REPO, "run", "s95", "apk_pins.json")

# (case, filename, url, known_sha256_or_empty)
P0 = [
    # WRONG_COLOR targets
    ("bouncy", "com.dozingcatsoftware.bouncy_43.apk",
     "https://f-droid.org/repo/com.dozingcatsoftware.bouncy_43.apk",
     "a509db2afda544f6da9620eb473319b0a034c6ffc8b6536e2a8a7bcc0f407f54"),
    ("hotdeath", "com.smorgasbork.hotdeath_11.apk",
     "https://f-droid.org/repo/com.smorgasbork.hotdeath_11.apk",
     "8e6c19ead1795fa5b0f62090f3a56efa4be16e4b3e33f151af707f5eb5e5c620"),
    ("urlchecker", "com.trianguloy.urlchecker_28.apk",
     "https://f-droid.org/repo/com.trianguloy.urlchecker_28.apk",
     ""),
    ("simplestopwatch", "omegacentauri.mobi.simplestopwatch_26.apk",
     "https://f-droid.org/repo/omegacentauri.mobi.simplestopwatch_26.apk",
     ""),
    # WRONG_CLIP targets
    ("bobball", "org.bobstuff.bobball_26.apk",
     "https://f-droid.org/repo/org.bobstuff.bobball_26.apk",
     "fd43009a7ffdfaf84963487e2b3502bef63775a4eedd60d7040da70e658b3241"),
    ("dodge", "com.dozingcatsoftware.dodge_10.apk",
     "https://f-droid.org/repo/com.dozingcatsoftware.dodge_10.apk",
     "a5687d1bad7b2927740a55b7b1df11efc81edcad03f0633ab5c2e5c58b120541"),
    # CONTROLS (rendered correctly in S93 TABLE OF TRUTH)
    ("nounours", "ca.rmen.nounours_358.apk",
     "https://f-droid.org/repo/ca.rmen.nounours_358.apk",
     ""),
    ("unote", "app.varlorg.unote_30.apk",
     "https://f-droid.org/repo/app.varlorg.unote_30.apk",
     ""),
    ("gmdice", "de.duenndns.gmdice_8.apk",
     "https://f-droid.org/repo/de.duenndns.gmdice_8.apk",
     ""),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(os.path.dirname(PINS_PATH), exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    pins = {}
    if os.path.isfile(PINS_PATH):
        pins = json.load(open(PINS_PATH))
    failures = 0
    for case, fname, url, known in P0:
        dest = os.path.join(CACHE, fname)
        want = known or pins.get(fname, "")
        if os.path.isfile(dest):
            got = sha256(dest)
            if want and got != want:
                print(f"HASH MISMATCH {fname}: {got} vs pin {want}")
                os.remove(dest)
            else:
                print(f"FOUND        {case:16s} {fname} {got[:16]}")
                pins.setdefault(fname, got)
                continue
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=300) as r:
                data = r.read()
            with open(dest, "wb") as f:
                f.write(data)
            got = sha256(dest)
            if want and got != want:
                print(f"HASH MISMATCH AFTER FETCH {fname}: {got} vs {want}")
                os.remove(dest)
                failures += 1
                continue
            pins.setdefault(fname, got)
            print(f"FETCHED      {case:16s} {fname} {got[:16]} "
                  f"({len(data)} bytes)")
        except Exception as e:  # noqa: BLE001
            print(f"FETCH FAILED {fname}: {e}")
            failures += 1
    with open(PINS_PATH, "w") as f:
        json.dump(pins, f, indent=1, sort_keys=True)
    print("pins saved:", PINS_PATH)
    if failures:
        print(f"FAILURES: {failures}")
        sys.exit(1)


if __name__ == "__main__":
    main()
