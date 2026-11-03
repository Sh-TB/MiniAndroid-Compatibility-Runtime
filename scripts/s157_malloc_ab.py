#!/usr/bin/env python3
"""s157_malloc_ab.py — S157: malloc-environment A/B on the dooz record-phase spin.

S156-P4 verdict: the spin is a LIVE interpreter loop paying ~50x per-op
string-map/alloc cost on THIS VM (2 cores, 4GiB cgroup, kernel 5.10.134).
Profile evidence (S156_P3_RIP_SYMBOLIZED): ~12.8% of ENGINE-thread samples
inside libc malloc/string family; fault curve 470-800 minor-faults/s with
+2MB/s RSS growth; CowStr refcount churn. Phase-A getenv surgery gave only
-10.9%. The cheapest READY-MADE lever before any further code surgery:
glibc allocator environment knobs (arena count, mmap/trim thresholds).

Protocol: EXACT S155 E5 reuse (scripts/s155_dooz_placement.py), dooz v23,
no-tap, fresh store per arm, 30 frames, --trace, real-dalvik, 110s budget.
Arms:
  D = default env (control — reproduces the standing spin face 11a38a5a)
  M = MALLOC_ARENA_MAX=1 MALLOC_MMAP_THRESHOLD_=131072
      MALLOC_TRIM_THRESHOLD_=134217728 MALLOC_TOP_PAD_=131072
Success criteria: face 851cc1761a1dfcdf (board renders) on M, or wall-time
movement >=20% with identical face (throughput lever confirmed).

Usage: python3 scripts/s157_malloc_ab.py D|M|collect
"""
import json
import os
import sys
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s155_dooz_placement as s  # the EXACT pinned E5 protocol

OUT = BASE / "run/s157_malloc_ab"
OUT.mkdir(parents=True, exist_ok=True)

# current canonical dev binary (S156-P4 phase-A surgery, -10.9% iget-object)
BIN = BASE / "miniandroid/build/miniandroid"

PIN_BOARD = "851cc1761a1dfcdf"
PIN_SPIN = "11a38a5aeeff45a6"

MALLOC_ENV = {
    "MALLOC_ARENA_MAX": "1",
    "MALLOC_MMAP_THRESHOLD_": "131072",
    "MALLOC_TRIM_THRESHOLD_": "134217728",
    "MALLOC_TOP_PAD_": "131072",
}


def run_arm(tag):
    print(f"== ARM {tag} ==")
    s.BIN = BIN
    s.OUT = OUT
    store = OUT / f"store_{tag}/data"
    s.install(s.DOOZ_APK, store)
    row, _ = s.run_case(f"E5_{tag}_dooz_notap", s.DOOZ_APK, store,
                        taps=None, package="io.github.yamin8000.dooz")
    faces = row.get("frame_faces") or {}
    last_face = faces[max(faces.keys())] if faces else None
    interp = ("BOARD" if last_face == PIN_BOARD else
              "SPIN" if last_face == PIN_SPIN else "OTHER")
    print(f"arm={tag} verdict={row['verdict']} last_face={last_face} "
          f"wall={row['wall_s']}s -> {interp}")
    out = {"tag": tag, "binary": str(BIN), "sha16": s.sha16(BIN),
           "env": "MALLOC_TUNED" if tag == "M" else "DEFAULT",
           "row": {k: v for k, v in row.items() if k != "frame_faces"},
           "last_face": last_face, "interp": interp}
    json.dump(out, open(OUT / f"arm_{tag}.json", "w"), indent=1, default=str)
    return out


def collect():
    arms = {}
    for tag in ("D", "M"):
        p = OUT / f"arm_{tag}.json"
        if p.exists():
            arms[tag] = json.load(open(p))
    if len(arms) < 2:
        print("missing arm data"); return
    d, m = arms["D"], arms["M"]
    verdict = None
    if m["last_face"] == PIN_BOARD and d["last_face"] == PIN_SPIN:
        verdict = "MALLOC_ENV_RUNS_DO0Z"
    elif m["last_face"] == d["last_face"]:
        dw, mw = d["row"]["wall_s"], m["row"]["wall_s"]
        if dw and mw:
            pct = round((dw - mw) / dw * 100, 1)
            verdict = f"SAME_FACE_WALL_DELTA={pct}%"
        else:
            verdict = "SAME_FACE"
    print("VERDICT:", verdict)
    json.dump({"verdict": verdict, "arms": arms},
              open(BASE / "evidence/s156_record_loop/S157_MALLOC_AB.json", "w"),
              indent=1, default=str)
    print("-> evidence/s156_record_loop/S157_MALLOC_AB.json")


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "D"
    if which == "collect":
        collect(); return
    if which in ("D", "M"):
        # NOTE: env tuning must reach the ENGINE process. run_case builds
        # env from os.environ, so we patch os.environ for the arm, restore
        # after (the harness has no per-call env hook — keep protocol code
        # byte-identical by construction).
        saved = {k: os.environ.get(k) for k in MALLOC_ENV}
        if which == "M":
            os.environ.update(MALLOC_ENV)
        try:
            run_arm(which)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


if __name__ == "__main__":
    main()
