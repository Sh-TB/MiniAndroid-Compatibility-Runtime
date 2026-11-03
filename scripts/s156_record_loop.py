#!/usr/bin/env python3
"""s156_record_loop.py — S156 wave: compose RECORD-phase loop forensics.

S155 pinned frontier (evidence/s155_dooz_placement/S155_EVIDENCE.json): on
rebuilt engines dooz's compose record phase spins (Lpz0;.M0 hot; 43M instr
@1 frame / 111.9M @6 frames; ~80K instr/s = 5-6x slower than the S152-era
VM) and Lt4;.onDraw never completes one draw pass -> DEFAULT_BACKGROUND_ONLY
(face 11a38a5a == all-black tower3d pin). Lel0;.B (insertAt) NEVER executes,
so the S155-APPLY law has 0 fires. Classic-View apps (unote) render fine on
the SAME binaries -> divergence is compose-record-phase specific.

S156 probes (ALL read-only diagnostics, instruments already in-binary):
Binary: miniandroid_o1.bin sha16 03aca4b7b55a8ad5 (restored from the OSS
insurance copy; = 42238cf2 sources at -O1: has AWAIT-UP-GATE, lacks
S155-APPLY — provenance asserted by the strings guard below).

  E1_fresh_census : fresh store, MINIANDROID_METHOD_CENSUS=1 (per-method
                    insn census, top-8 every 2s, bounded 64 dumps) +
                    MINIANDROID_T68_NODE_TRACE=1 (composition node entries).
                    -> which methods burn the record phase; does the burn
                    SHIFT over the window (progress) or stay FIXED (spin)?
  E2_fresh_m0     : fresh store, MINIANDROID_METHOD_TRACE=Lpz0;|M0 (pc +
                    register/param rows, budget-bounded) + PMC watch
                    Lpz0;|M0 (callee resolution, bounded 2400).
                    -> M0 re-entry keys: same-state cycling or advancing?
  E3_mature_m0    : E1's store REUSED (matured by one full run) — the
                    fresh-store A/B. DataStore fresh-store state is
                    candidate #2 for the spin; identical spin shape here
                    exonerates it.

Laws honored: diagnostics are read-only (M3 law), byte-inert by default
(no tap, no env besides the diagnostics); console-flood guard kills a run
whose stderr grows past the cap (itself a datum: an unbudgeted diag storm).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid_o1.bin"
OUT = BASE / "run156"
EVID = BASE / "evidence/s156_record_loop"
OUT.mkdir(parents=True, exist_ok=True)
EVID.mkdir(parents=True, exist_ok=True)

DOOZ_APK = BASE / "upload/canonical_apks/dooz_23_toplevel.apk"
PKG = "io.github.yamin8000.dooz"
S1 = OUT / "store_s1"          # fresh in E1, matured for E3
S2 = OUT / "store_s2"          # fresh for E2

MAX_SECONDS = 420
FRAMES = 3
CONSOLE_CAP = 600 * 1024 * 1024  # flood guard

VERDICT_RE = re.compile(r"FRAME_ANALYSIS state=(\S+)")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def guard():
    """Provenance + instrument strings gate (S154 lesson: stale builds)."""
    import subprocess as sp
    txt = sp.run(["strings", str(BIN)], capture_output=True).stdout
    checks = {
        "AWAIT-UP-GATE (S154 law present)": b"AWAIT-UP-GATE" in txt,
        "S155-APPLY absent (= 42238cf2 sources)":
            b"S155-APPLY" not in txt,
        "METHOD-CENSUS present": b"METHOD-CENSUS" in txt,
        "T68-ENTRY present": b"T68-ENTRY" in txt,
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print(("  OK  " if v else "  FAIL") + " " + k)
    if not ok:
        sys.exit(2)
    print("binary provenance gate OK:", BIN, "sha16", sha16(BIN))


def install(apk, store):
    store.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), "install", str(apk), "--data-root",
                    str(store)], capture_output=True, timeout=300)


def run_case(tag, store, env_extra):
    rundir = OUT / tag
    console = OUT / f"{tag}_console.log"
    if console.exists():
        console.unlink()
    env = dict(os.environ)
    env.update(env_extra)
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(MAX_SECONDS), "--frames", str(FRAMES),
           "--trace", "--package", PKG]
    t0 = time.time()
    flooded = False
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=open(console, "w"), env=env)
    while True:
        rc = proc.poll()
        el = time.time() - t0
        if el > MAX_SECONDS + 90 and rc is None:
            proc.kill()
            rc = -9
        try:
            if console.stat().st_size > CONSOLE_CAP:
                proc.kill()
                flooded = True
                rc = -8
        except FileNotFoundError:
            pass
        if rc is not None:
            break
        time.sleep(2)
    wall = round(time.time() - t0, 1)
    text = console.read_text(errors="replace") if console.exists() else ""
    row = analyze(tag, wall, flooded, text, rundir)
    print(json.dumps({k: v for k, v in row.items() if k != "census_rows"},
                     indent=1)[:2200])
    return row, text


def analyze(tag, wall, flooded, text, rundir):
    census = re.findall(r"\[METHOD-CENSUS\] window_insns=(\d+)(.*)", text)
    census_rows = [{"win": int(w), "top": t.strip()[:400]}
                   for w, t in census]
    # top method across all dumps: first method segment after the
    # "total_methods=N |" prefix; leaders over time (shift = progress)
    leaders = []
    for r in census_rows:
        segs = r["top"].split("|")
        m = segs[1].strip() if len(segs) > 1 else (segs[0].strip() if segs else "?")
        leaders.append(m.split("=")[0].strip() if m else "?")
    m3_cycle = re.findall(r"\[M3-19-CYCLE\] (\S+) re-entered", text)
    m3_reentry = len(re.findall(r"\[M3-19-REENTRY\]", text))
    m3_open = len(re.findall(r"\[M3-19-OPEN\]", text))
    m0_rows = re.findall(r"\[METHOD-TRACE\] Lpz0;\.M0 pc=(\d+) (.*)", text)
    m0_pc_hist = {}
    for pc, _ in m0_rows:
        m0_pc_hist[pc] = m0_pc_hist.get(pc, 0) + 1
    m0_entries = [rest for pc, rest in m0_rows if pc == "0"]
    m0_entry_states = []
    for e in m0_entries:
        params = " ".join(re.findall(r"p\d+=\S+", e))
        m0_entry_states.append(params)
    distinct_entries = list(dict.fromkeys(m0_entry_states))
    pmc = re.findall(r"\[PMC\] (\S+)", text)
    t68 = len(re.findall(r"\[T68-ENTRY\]", text))
    faces = sorted(p.name for p in
                   Path(rundir).glob("frames/frame_*")) if rundir.exists() else []
    row = {
        "tag": tag, "wall_s": wall, "flooded": flooded,
        "console_bytes": len(text),
        "verdict": (lambda v: v[-1] if v else None)(
            VERDICT_RE.findall(text)),
        "face_screenshot": sha16(rundir / "screenshot.png")
        if (rundir / "screenshot.png").exists() else None,
        "census_dumps": len(census_rows),
        "census_leader_seq": leaders[:40],
        "census_last": census_rows[-1]["top"] if census_rows else None,
        "m3_cycle_keys": list(dict.fromkeys(m3_cycle))[:12],
        "m3_cycle_n": len(m3_cycle),
        "m3_reentry_n": m3_reentry, "m3_open_n": m3_open,
        "m0_rows": len(m0_rows),
        "m0_pc_hist_top": sorted(m0_pc_hist.items(),
                                 key=lambda kv: -kv[1])[:12],
        "m0_entries_n": len(m0_entries),
        "m0_distinct_entry_states_n": len(distinct_entries),
        "m0_distinct_entry_states_sample": distinct_entries[:6],
        "pmc_n": len(pmc),
        "pmc_sample": pmc[:10],
        "t68_rows": t68,
        "uncaught": len(re.findall(r"UNCAUGHT", text)),
        "n_frames": len(faces),
    }
    return row


ENV_E1 = {
    "MINIANDROID_METHOD_CENSUS": "1",
    "MINIANDROID_T68_NODE_TRACE": "1",
}
ENV_M0 = {
    "MINIANDROID_METHOD_TRACE": "Lpz0;|M0",
    "MINIANDROID_METHOD_TRACE_BUDGET": "60000",
    "MINIANDROID_PMC_TRACE": "Lpz0;|M0",
}


def phase(tag, store, env_extra):
    r, _ = run_case(tag, store, env_extra)
    json.dump(r, open(EVID / f"S156_{tag}.json", "w"), indent=1)
    print("evidence ->", EVID / f"S156_{tag}.json")
    return r


def merge():
    r1 = json.load(open(EVID / "S156_E1_fresh_census.json"))
    r2 = json.load(open(EVID / "S156_E2_fresh_m0.json"))
    r3 = json.load(open(EVID / "S156_E3_mature_m0.json"))
    eval_ = {
        "spin_shape": {
            "census_leaders_shift": len(set(r1["census_leader_seq"])) > 2,
            "leaders_distinct": sorted(set(r1["census_leader_seq"]))[:8],
        },
        "store_ab": {
            "fresh_m0_rows": r2["m0_rows"],
            "mature_m0_rows": r3["m0_rows"],
            "fresh_distinct_entries": r2["m0_distinct_entry_states_n"],
            "mature_distinct_entries": r3["m0_distinct_entry_states_n"],
            "fresh_face": r2["face_screenshot"],
            "mature_face": r3["face_screenshot"],
            "fresh_verdict": r2["verdict"],
            "mature_verdict": r3["verdict"],
        },
        "m3_gate_involvement": {
            "cycle_keys": r1["m3_cycle_keys"],
            "cycle_n_E1": r1["m3_cycle_n"],
            "reentry_n_E1": r1["m3_reentry_n"],
        },
    }
    doc = {
        "wave": "S156", "binary": sha16(BIN),
        "binary_provenance": "42238cf2 sources at -O1 (S155-APPLY absent)",
        "apk": "dooz_23_toplevel", "max_seconds": MAX_SECONDS,
        "frames_cap": FRAMES,
        "runs": {"E1": r1, "E2": r2, "E3": r3}, "eval": eval_,
    }
    json.dump(doc, open(EVID / "S156_RECORD_LOOP.json", "w"), indent=1)
    print("evidence ->", EVID / "S156_RECORD_LOOP.json")
    print(json.dumps(eval_, indent=1))


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("== S156 provenance gate ==")
    guard()
    if which in ("E1", "all"):
        install(DOOZ_APK, S1)
        print("== E1 fresh census (store S1) ==")
        phase("E1_fresh_census", S1, ENV_E1)
    if which in ("E2", "all"):
        install(DOOZ_APK, S2)
        print("== E2 fresh M0 keys (store S2) ==")
        phase("E2_fresh_m0", S2, ENV_M0)
    if which in ("E3", "all"):
        # NOTE: E3 reuses S1 MATURED by the E1 run (fresh-store A/B).
        print("== E3 mature M0 keys (store S1, matured by E1) ==")
        phase("E3_mature_m0", S1, ENV_M0)
    if which == "merge":
        merge()


if __name__ == "__main__":
    main()
