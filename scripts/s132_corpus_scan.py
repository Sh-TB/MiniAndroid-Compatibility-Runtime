#!/usr/bin/env python3
"""s132_corpus_scan.py — S132 Wave-1 CORPUS FAN-OUT scanner.
ROOT FIX → FAN-OUT: after the TableLayout/TableRow/weight + 0dp law fixes,
find every corpus APK whose layouts exercise the same capability family
(TableLayout/TableRow/GridLayout/SlidingUpPanel/layout_weight/0dp) so the
fix's fan-out can be batch-tested, not just the original opencalculator.
"""
import os
import zipfile

ROOTS = [
    "/home/z/my-project/upload/canonical_apks",
    "/home/z/my-project/upload",
]

def scan(apk):
    try:
        z = zipfile.ZipFile(apk)
    except Exception:
        return set()
    found = set()
    for n in z.namelist():
        if n.endswith(".xml"):
            try:
                d = z.read(n)
            except Exception:
                continue
            if len(d) < 8 or d[:4] != bytes([3, 0, 8, 0]):
                continue
            if b"TableLayout" in d or b"TableRow" in d:
                found.add("table")
            if b"GridLayout" in d:
                found.add("grid")
            if b"SlidingUpPanel" in d:
                found.add("slidingup")
            if b"layout_weight" in d:
                found.add("weight")
    return found


seen = set()
for root in ROOTS:
    if not os.path.isdir(root):
        continue
    for f in sorted(os.listdir(root)):
        if not f.endswith(".apk") or f in seen:
            continue
        seen.add(f)
        hits = scan(os.path.join(root, f))
        if hits:
            print(f, sorted(hits))
