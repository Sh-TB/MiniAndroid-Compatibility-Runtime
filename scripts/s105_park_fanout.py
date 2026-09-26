#!/usr/bin/env python3
"""S105 ROOT-010 fan-out scan: which corpus APKs carry the worker park/loop
semantic pattern (LockSupport.park*, parkNanos/parkUntil) vs which EXECUTE it
(observed in engine runs). Presence != fan-out; execution evidence is the
honest measure."""
import os, sys, zipfile

ROOTS = [
    "/home/z/my-project/upload/canonical_apks",
    "/home/z/my-project/upload/foundation_apks",
    "/home/z/my-project/upload/s65_apks",
    "/home/z/my-project/upload/s72_w4_apks",
    "/home/z/my-project/upload/s80_games",
    "/home/z/my-project/upload/s83_games",
    "/home/z/my-project/upload/s86_games",
    "/home/z/my-project/upload/s98_games",
]
MARKERS = ["LockSupport", "parkNanos", "parkUntil"]

def scan(apk):
    try:
        z = zipfile.ZipFile(apk)
    except Exception:
        return None
    hits = {m: False for m in MARKERS}
    dexes = [n for n in z.namelist() if n.endswith(".dex")]
    if not dexes:
        return None
    for n in dexes:
        data = z.read(n)
        for m in MARKERS:
            if m.encode() in data:
                hits[m] = True
    return hits

def main():
    rows = []
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for f in sorted(os.listdir(root)):
            if not f.endswith(".apk"):
                continue
            p = os.path.join(root, f)
            h = scan(p)
            if h is None:
                continue
            ls = any(h[m] for m in ("parkNanos", "parkUntil"))
            rows.append((os.path.relpath(p, "/home/z/my-project"),
                         h["LockSupport"], ls))
    n = len(rows)
    with_ls = sum(1 for _, a, _ in rows if a)
    with_timed = sum(1 for _, _, b in rows if b)
    print(f"corpus APKs scanned: {n}")
    print(f"LockSupport refs:    {with_ls}")
    print(f"timed park (parkNanos/parkUntil): {with_timed}")
    for p, a, b in rows:
        if a:
            print(f"  {'LS ' if a else '   '}{'TIMED' if b else '     '}  {p}")

if __name__ == "__main__":
    main()
