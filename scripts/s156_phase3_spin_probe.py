#!/usr/bin/env python3
"""s156_phase3_spin_probe.py — S156 phase-3 v2: WHAT burns 99% CPU in the
record-phase spin, given the interpreter instrument sees idle windows?

The opener (S156_P3_WCHAN_OPENER.json) proved: main thread R at ~99% CPU,
second thread futex-waiting (worker, zero CPU), verdict still
DEFAULT_BACKGROUND_ONLY. So the burn is engine-NATIVE code (outside the
dalvik fetch_decode_execute instrument). This probe discriminates the burn
family WITHOUT strace/perf, via /proc counters on the MAIN thread:
  - minflt/majflt deltas (field 8/10 of stat)  -> allocation/mmap churn
  - utime vs stime deltas                      -> userspace vs kernel burn
  - /proc/PID/io rchar/wchar/syscr/syscw       -> file-IO loop
  - /proc/PID/task/TID/syscall samples         -> catch it inside a syscall
  - /proc/PID/status ctxt switches (fixed: read while ALIVE)
  - smaps_rollup anonymous every 10s           -> memory growth
  - every sample: wall + a 2s-window interpreter-instrument cross-check is
    NOT needed here (E1 did it); this probe is about the non-instrumented burn.

Verdict families:
  minflt storm (utime-heavy)  -> allocation churn (compose snapshot copies?)
  stime-heavy + minflt        -> kernel-side (mmap/munmap, page faults)
  io syscr storm              -> file re-read loop
  syscall=rare + R everywhere -> pure userspace spin (hot C++ loop)
"""
import json
import os
import re
import subprocess
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid"   # canonical pin a793f134
OUT = BASE / "run155p2"
EVID = BASE / "evidence/s156_record_loop"
DOOZ_APK = BASE / "upload/canonical_apks/dooz_23_toplevel.apk"
STORE = OUT / "store_A/data"

RUN_SECONDS = 60
SAMPLE_EVERY = 0.5
VERDICT_RE = re.compile(r"FRAME_ANALYSIS state=(\S+)")
SYSCALLS = {0: "read", 1: "write", 9: "mmap", 10: "mprotect", 11: "munmap",
            12: "brk", 202: "futex", 232: "epoll_wait", 35: "nanosleep",
            230: "clock_nanosleep", 2: "open", 3: "close", 257: "openat",
            16: "ioctl", 8: "lseek", 21: "access", 281: "sched_yield"}


def stat_fields(pid, tid):
    try:
        stat = Path(f"/proc/{pid}/task/{tid}/stat").read_text()
        after = stat[stat.rindex(")") + 2:].split()
        return {"state": after[0], "minflt": int(after[5]),
                "majflt": int(after[7]), "utime": int(after[11]),
                "stime": int(after[12])}
    except (FileNotFoundError, ProcessLookupError, ValueError):
        return None


def cur_syscall(pid, tid):
    try:
        raw = Path(f"/proc/{pid}/task/{tid}/syscall").read_text().strip()
        if raw.startswith("running") or raw.startswith("no syscall"):
            return raw.split()[0]
        num = int(raw.split()[0])
        return SYSCALLS.get(num, f"sys#{num}")
    except (FileNotFoundError, ProcessLookupError, ValueError, IndexError):
        return None


def io_row(pid):
    try:
        txt = Path(f"/proc/{pid}/io").read_text()
        return {k: int(v) for k, v in
                (l.split(": ") for l in txt.strip().splitlines())}
    except (FileNotFoundError, ProcessLookupError, ValueError):
        return None


def switches(pid):
    try:
        txt = Path(f"/proc/{pid}/status").read_text()
        return {"vol": int(re.search(r"voluntary_ctxt_switches:\s+(\d+)",
                                     txt).group(1)),
                "nonvol": int(re.search(r"nonvoluntary_ctxt_switches:\s+(\d+)",
                                        txt).group(1))}
    except (FileNotFoundError, ProcessLookupError, AttributeError):
        return None


def anon_kb(pid):
    try:
        txt = Path(f"/proc/{pid}/smaps_rollup").read_text()
        m = re.search(r"^Anonymous:\s+(\d+)", txt, re.M)
        return int(m.group(1)) if m else None
    except (FileNotFoundError, ProcessLookupError):
        return None


def main():
    rundir = OUT / "P3_spin"
    console = OUT / "P3_spin_console.log"
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(STORE), "-o", str(rundir),
           "--max-seconds", str(RUN_SECONDS), "--frames", "30", "--trace",
           "--package", "io.github.yamin8000.dooz"]
    t0 = time.time()
    with open(console, "w") as cf:
        proc = subprocess.Popen(cmd, stdout=cf, stderr=subprocess.STDOUT)
        pid = proc.pid
        samples, syscall_samples = [], []
        io0 = switches0 = None
        io_series, anon_series = [], []
        while proc.poll() is None and time.time() - t0 < RUN_SECONDS + 25:
            now = round(time.time() - t0, 2)
            m = stat_fields(pid, pid)          # main thread: tid == pid
            w2 = stat_fields(pid, pid + 1) if False else None
            sc = cur_syscall(pid, pid)
            if sc is not None:
                syscall_samples.append(sc)
            if m:
                samples.append({"t": now, **m})
                s = switches(pid)
                if s and switches0 is None:
                    switches0 = s
                if s:
                    switches_last = s
                if io0 is None:
                    io0 = io_row(pid)
                if len(anon_series) == 0 or now - anon_series[-1]["t"] >= 10:
                    anon_series.append({"t": now, "anon_kb": anon_kb(pid)})
            time.sleep(SAMPLE_EVERY)
        io_last = io_row(pid)
        switches_last_keep = switches(pid) if proc.poll() is None else None
        wall = round(time.time() - t0, 1)
    proc.wait(timeout=20)
    text = console.read_text(errors="replace")
    verdict = (VERDICT_RE.findall(text) or [None])[-1]

    first, last = samples[0], samples[-1]
    d = {k: last[k] - first[k] for k in ("minflt", "majflt", "utime", "stime")}
    tick = os.sysconf("SC_CLK_TCK")
    io_d = None
    if io0 and io_last:
        io_d = {k: io_last.get(k, 0) - io0.get(k, 0)
                for k in ("rchar", "wchar", "syscr", "syscw")}
    sw_d = None
    try:
        sw_d = {"voluntary": switches_last["vol"] - switches0["vol"],
                "nonvoluntary": switches_last["nonvol"] - switches0["nonvol"]}
    except (KeyError, NameError, TypeError):
        pass

    sc_hist = {}
    for s in syscall_samples:
        sc_hist[s] = sc_hist.get(s, 0) + 1

    utime_s, stime_s = d["utime"] / tick, d["stime"] / tick
    wall_d = last["t"] - first["t"]
    fam = ("minflt-storm (allocation churn)"
           if d["minflt"] > 10000 else
           "kernel-heavy (stime>utime)" if stime_s > utime_s else
           "io-loop" if io_d and io_d["syscr"] > 5000 else
           "pure-userspace-spin")
    result = {
        "probe": "S156-P3 spin v2 (main-thread /proc counters)",
        "binary_sha16": "a793f134936f7e58",
        "verdict": verdict, "wall_s": wall, "n_samples": len(samples),
        "main_thread_deltas": d,
        "utime_s": round(utime_s, 2), "stime_s": round(stime_s, 2),
        "sample_window_s": round(wall_d, 2),
        "cpu_util": round((utime_s + stime_s) / max(wall_d, 0.1), 3),
        "minflt_per_s": round(d["minflt"] / max(wall_d, 0.1), 1),
        "io_deltas": io_d,
        "ctxt_switches": sw_d,
        "syscall_sample_hist": sc_hist,
        "anon_kb_series": anon_series,
        "verdict_family": fam,
        "frames_dir_frames": len(list(rundir.glob("frames/frame_*"))),
    }
    slim = {k: v for k, v in result.items() if k != "anon_kb_series"}
    print(json.dumps(slim, indent=1)[:2400])
    EVID.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(EVID / "S156_P3_SPIN_V2.json", "w"), indent=1,
              default=str)
    print("-> evidence/s156_record_loop/S156_P3_SPIN_V2.json")


if __name__ == "__main__":
    main()
