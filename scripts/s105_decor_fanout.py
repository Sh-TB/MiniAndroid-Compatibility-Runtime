#!/usr/bin/env python3
"""S105 R-005 DECOR-LINKAGE fan-out scan: corpus APKs whose dex carries the
WindowDecorActionBar / decor_content_parent family (the sub-decor reachability
consumers) plus the AppCompatDelegateImpl createSubDecor machinery."""
import os, zipfile

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
MARKERS = {
    "WindowDecorActionBar": "actionbar-decor-walker",
    "decor_content_parent": "sub-decor id (reachability consumer)",
    "createSubDecor": "sub-decor producer",
    "AppCompatDelegateImpl": "delegate machinery",
}

def scan(apk):
    try:
        z = zipfile.ZipFile(apk)
    except Exception:
        return None
    dexes = [n for n in z.namelist() if n.endswith(".dex")]
    if not dexes:
        return None
    hits = {m: False for m in MARKERS}
    for n in dexes:
        data = z.read(n)
        for m in MARKERS:
            if m.encode() in data:
                hits[m] = True
    return hits

def main():
    total = 0
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for f in sorted(os.listdir(root)):
            if not f.endswith(".apk"):
                continue
            total += 1
            p = os.path.join(root, f)
            h = scan(p)
            if h is None:
                continue
            if h["WindowDecorActionBar"] and h["decor_content_parent"]:
                print(f"WALKER+ID  {os.path.relpath(p, '/home/z/my-project')}"
                      f"  createSubDecor={h['createSubDecor']}"
                      f" delegate={h['AppCompatDelegateImpl']}")
    print(f"scanned {total} APKs")

if __name__ == "__main__":
    main()
