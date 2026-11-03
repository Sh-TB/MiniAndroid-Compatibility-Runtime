#!/usr/bin/env python3
"""s156_phase2_flags_split.py — S156 phase-2: the FLAGS-vs-LOST-DELTA split.

Phase-1 pinned frontier: dooz record-phase spin on rebuilt binaries (the
S154 pin binary a793f134936f7e58 was lost to the infra cleaner; S155 dev
rebuilds -O1/-O2g0 spin in compose record phase, face 11a38a5aeeff45a6
white/black; the pinned-era face is 851cc1761a1dfcdf).

Discovery at phase-2 start (upload/_ma_local_backup/):
  miniandroid_plainmake_42238cf2_a793f134936f7e58.bin -> sha16 a793f134936f7e58
  = the plain-make rebuild at 42238cf2 DID reproduce the pin sha BYTE-EXACT
  on Nov 3 13:11 (the session died before recording). Sources are complete
  at the rebuild level; the pin binary is RESTORED.

This script runs the S155-E0/E5 protocol (dooz NO-tap, fresh store, 30
frames, --trace, real-dalvik) on up to three binaries SAME-DAY same-VM:
  A = restored pin binary a793f134936f7e58   (pinned flags -O2, Nov-3 toolchain)
  B = fresh plain-make rebuild 756eb9e71da53779 (pinned flags -O2, TODAY toolchain)
  C = -O1 dev binary 03aca4b7b55a8ad5        (same-day control, phase-1 face 11a38a5a)

Verdict matrix (face of the last frame vs pins):
  A==851cc176 & B==11a38a5a  -> REBUILD/TOOLCHAIN delta (no lost delta, no flag story)
  A==851cc176 & B==851cc176  -> FLAGS story confirmed (S155 dev builds were the spin)
  A spins (11a38a5a/other)   -> VM-state dependence (record loop is env-sensitive;
                                aligns with S156-E1 idle-window census)

Usage: python3 scripts/s156_phase2_flags_split.py A|B|C|collect
"""
import json
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s155_dooz_placement as s  # reuse the EXACT pinned protocol code

OUT = BASE / "run155p2"
OUT.mkdir(parents=True, exist_ok=True)

BIN_A = BASE / "upload/_ma_local_backup/miniandroid_plainmake_42238cf2_a793f134936f7e58.bin"
BIN_B = BASE / "wt_s156/miniandroid/build/miniandroid"
BIN_C = BASE / "upload/_ma_local_backup/miniandroid_o1_03aca4b7.bin"

PIN_BOARD = "851cc1761a1dfcdf"   # pinned-era dooz no-tap face (board chrome renders)
PIN_SPIN = "11a38a5aeeff45a6"    # S155 white/black face (record-phase spin, no board)

ROWS = {}


def run_one(tag, binpath):
    print(f"== Run {tag}: {binpath.name} ==")
    s.BIN = binpath
    s.OUT = OUT
    sha = s.sha16(binpath)
    print(f"binary sha16={sha}")
    store = OUT / f"store_{tag}/data"
    s.install(s.DOOZ_APK, store)
    row, _ = s.run_case(
        f"E5_{tag}_dooz_notap", s.DOOZ_APK, store, taps=None,
        package="io.github.yamin8000.dooz")
    faces = row.get("frame_faces") or {}
    last_face = faces[max(faces.keys())] if faces else None
    print(f"verdict={row['verdict']} last_face={last_face}")
    if last_face == PIN_BOARD:
        interp = "BOARD RENDERS (== pinned-era face)"
    elif last_face == PIN_SPIN:
        interp = "SPIN FACE (white/black, record-phase loop)"
    else:
        interp = f"OTHER face (drift)"
    print(f"-> {interp}")
    return row, last_face, interp


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "A"
    if which == "collect":
        collect()
        return
    for tag, path in (("A", BIN_A), ("B", BIN_B), ("C", BIN_C)):
        if tag != which and which != "ABC":
            continue
        if not path.exists():
            print(f"FATAL: {path} missing"); sys.exit(2)
        row, last_face, interp = run_one(tag, path)
        ROWS[tag] = {"bin": str(path), "sha16": s.sha16(path),
                     "row": {k: v for k, v in row.items() if k != "frame_faces"},
                     "last_face": last_face, "interp": interp}
        json.dump(ROWS, open(OUT / f"phase2_rows_{tag}.json", "w"),
                  indent=1, default=str)


def collect():
    rows = {}
    for tag in ("A", "B", "C"):
        p = OUT / f"phase2_rows_{tag}.json"
        if p.exists():
            rows[tag] = json.load(open(p))[tag]  # file holds {tag: row}
    faces = {t: rows[t]["last_face"] for t in rows}
    print("FACES:", json.dumps(faces, indent=1))
    verdict = None
    if "A" in faces:
        a_board = faces["A"] == PIN_BOARD
        if a_board and "B" in faces:
            verdict = ("FLAGS" if faces["B"] == PIN_BOARD
                       else "REBUILD_OR_TOOLCHAIN_DELTA")
        elif not a_board:
            verdict = "VM_STATE_DEPENDENT_SPIN"
    print("VERDICT:", verdict)
    json.dump({"faces": faces, "verdict": verdict, "rows": rows},
              open(BASE / "evidence/s156_record_loop/S156_PHASE2_FLAGS_SPLIT.json",
                   "w"), indent=1, default=str)
    print("-> evidence/s156_record_loop/S156_PHASE2_FLAGS_SPLIT.json")


if __name__ == "__main__":
    main()
