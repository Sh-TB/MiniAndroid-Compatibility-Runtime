#!/usr/bin/env python3
# s27_w5_matrix.py — builds evidence/s27/s27w5_matrix.tsv from the S27-W5
# run dirs: the pz environment-transient blocker closure (the NoSuchElementException
# that fired in the S27-W3-era sandbox does NOT reproduce after the rebuild)
# plus the full wall/battery gate rows.
import hashlib
import json
import os

BASE = "/home/z/my-project/miniandroid/evidence/s27"
OUT = os.path.join(BASE, "s27w5_matrix.tsv")

ROWS = [
    ("name.livitski.games.puzzle.android", "w5_pz_r1", "production",
     "REBUILD (post-recycle sandbox, pre-instrument tree): rc=0, face "
     "6375a3a3813af176 = the ORIGINAL w2 canonical — the S27-W3-era "
     "NoSuchElementException at Board.placeTilesRandom pc=60 DID NOT "
     "reproduce"),
    ("name.livitski.games.puzzle.android", "w5_pz_r2", "production", "rebuild x2"),
    ("name.livitski.games.puzzle.android", "w5_pz_r3", "production", "rebuild x3"),
    ("name.livitski.games.puzzle.android", "w5_pz_final_r1", "production",
     "post-instrument (the [S27-W5-ITER-EXHAUST] throw-site receipt "
     "instrument): rc=0, face 6375a3a3813af176, ZERO throw lines — the "
     "instrument is inert on success"),
    ("name.livitski.games.puzzle.android", "w5_pz_final_r2", "production",
     "final x2"),
    ("name.livitski.games.puzzle.android", "w5_pz_final_r3", "production",
     "final x3 — deterministic 6375a3a3813af176 x3"),
    ("name.livitski.games.puzzle.android", "w3_pz", "production",
     "REFERENCE (the S27-W3-era sandbox): face 35c4e53b rc=1 ×3 with the "
     "app-visible NoSuchElementException — the S27-W3 bisect reproduced it "
     "from a DIFFERENT clean-tree binary in the SAME sandbox; the SAME "
     "source tree rebuilt in the NEW sandbox does NOT reproduce it ⇒ the "
     "determinant is the sandbox environment, NOT the source and NOT the "
     "law set"),
]


def last_frame_hash(run_dir):
    p = os.path.join(BASE, run_dir, "screenshot.png")
    if not os.path.exists(p):
        return ""
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def rc(run_dir):
    p = os.path.join(BASE, run_dir, "rc.txt")
    if os.path.exists(p):
        return open(p).read().strip()
    return ""


def events(run_dir):
    p = os.path.join(BASE, run_dir, "trace_summary.json")
    if os.path.exists(p):
        try:
            return str(json.load(open(p)).get("events_total"))
        except Exception:
            return ""
    return ""


with open(OUT, "w") as f:
    f.write("apk\trun_dir\tbinary\tlast_frame_hash16\trc\tevents\tnote\n")
    for apk, run_dir, binary, note in ROWS:
        f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            apk, run_dir, binary, last_frame_hash(run_dir), rc(run_dir),
            events(run_dir), note))
print("wrote", OUT)
with open(OUT) as f:
    print(f.read())
