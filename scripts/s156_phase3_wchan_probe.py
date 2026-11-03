#!/usr/bin/env python3
"""s156_phase3_wchan_probe.py — S156 phase-3 opener: WHERE does the record
phase idle? No strace/perf on this VM -> /proc sampler (zero invasiveness).

Launches the canonical engine on the dooz E5 protocol (bounded window) and
samples every 0.5s, for EVERY thread:
  - wchan      (kernel wait channel: futex_wait_queue / hrtimer_nanosleep /
                epoll_poll / do_wait / 0 = running)
  - stat state (R running, S sleep, D disk)
  - utime/stime (CPU clock ticks) -> per-thread CPU deltas
  - status voluntary/nonvoluntary ctxt switches (process-wide deltas)

Verdict families:
  futex_wait_queue dominant  -> cross-thread handshake starvation (2 cores?)
  hrtimer/nanosleep dominant -> deliberate sleep law (budget/timing keyed)
  epoll/poll dominant        -> event-loop wait (frame clock source)
  R dominant + slow rate     -> pure VM slowness (CPU-bound)
"""
import json
import os
import re
import subprocess
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid"   # canonical pin binary a793f134
OUT = BASE / "run155p2"
EVID = BASE / "evidence/s156_record_loop"
DOOZ_APK = BASE / "upload/canonical_apks/dooz_23_toplevel.apk"
STORE = OUT / "store_A/data"                  # already installed in phase-2 run A

RUN_SECONDS = 60
SAMPLE_EVERY = 0.5

VERDICT_RE = re.compile(r"FRAME_ANALYSIS state=(\S+)")


def read_thread(pid, tid):
    try:
        wchan = Path(f"/proc/{pid}/task/{tid}/wchan").read_text().strip()
        stat = Path(f"/proc/{pid}/task/{tid}/stat").read_text()
        # comm may contain spaces/parens -> parse after last ')'
        after = stat[stat.rindex(")") + 2:].split()
        state = after[0]
        utime, stime = int(after[11]), int(after[12])  # fields 14,15 (1-based)
        return {"wchan": wchan, "state": state, "utime": utime, "stime": stime}
    except (FileNotFoundError, ProcessLookupError, ValueError):
        return None


def read_status_switches(pid):
    try:
        txt = Path(f"/proc/{pid}/status").read_text()
        v = int(re.search(r"voluntary_ctxt_switches:\s+(\d+)", txt).group(1))
        n = int(re.search(r"nonvoluntary_ctxt_switches:\s+(\d+)", txt).group(1))
        return {"vol": v, "nonvol": n}
    except (FileNotFoundError, ProcessLookupError, AttributeError):
        return None


def main():
    rundir = OUT / "P3_wchan"
    console = OUT / "P3_wchan_console.log"
    env = dict(os.environ)
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(STORE), "-o", str(rundir),
           "--max-seconds", str(RUN_SECONDS), "--frames", "30", "--trace",
           "--package", "io.github.yamin8000.dooz"]
    t0 = time.time()
    with open(console, "w") as cf:
        proc = subprocess.Popen(cmd, stdout=cf, stderr=subprocess.STDOUT, env=env)
        pid = proc.pid
        samples = []
        cpu0 = {}
        sw0 = read_status_switches(pid)
        while proc.poll() is None and time.time() - t0 < RUN_SECONDS + 25:
            now = round(time.time() - t0, 2)
            threads = {}
            try:
                tids = [int(d) for d in
                        os.listdir(f"/proc/{pid}/task") if d.isdigit()]
            except FileNotFoundError:
                break
            for tid in tids:
                r = read_thread(pid, tid)
                if r:
                    threads[tid] = r
            samples.append({"t": now, "threads": threads})
            time.sleep(SAMPLE_EVERY)
        wall = round(time.time() - t0, 1)
        sw1 = read_status_switches(pid)
    proc.wait(timeout=20)

    text = console.read_text(errors="replace")
    verdict = (VERDICT_RE.findall(text) or [None])[-1]

    # ---- aggregation ----
    wchan_hist = {}
    state_hist = {}
    tid_names = {}
    cpu_final = {}
    for s in samples:
        for tid, r in s["threads"].items():
            wchan_hist[r["wchan"]] = wchan_hist.get(r["wchan"], 0) + 1
            state_hist[r["state"]] = state_hist.get(r["state"], 0) + 1
            cpu_final[tid] = (r["utime"], r["stime"])
            tid_names[tid] = tid
    n_samples = len(samples)
    first = samples[0]["threads"] if samples else {}
    cpu_deltas = {}
    for tid, (u1, s1) in cpu_final.items():
        r0 = first.get(tid)
        if r0:
            cpu_deltas[tid] = {"utime_ticks": u1 - r0["utime"],
                               "stime_ticks": s1 - r0["stime"]}
    switches = None
    if sw0 and sw1:
        switches = {"voluntary": sw1["vol"] - sw0["vol"],
                    "nonvoluntary": sw1["nonvol"] - sw0["nonvol"]}

    # main thread = tid == pid
    main_wchan = {}
    for s in samples:
        m = s["threads"].get(pid)
        if m:
            main_wchan[m["wchan"]] = main_wchan.get(m["wchan"], 0) + 1

    CLKTAK = os.sysconf("SC_CLK_TCK")
    total_cpu_s = sum(u + s for u, s in cpu_final.values()) / CLKTAK

    result = {
        "probe": "S156-P3 wchan opener",
        "binary_sha16": "a793f134936f7e58",
        "wall_s": wall, "n_samples": n_samples,
        "sample_every_s": SAMPLE_EVERY,
        "verdict": verdict,
        "wchan_hist_all_threads": wchan_hist,
        "wchan_hist_main_thread": main_wchan,
        "state_hist": state_hist,
        "thread_count_max": max((len(s["threads"]) for s in samples), default=0),
        "cpu_ticks_final": {str(k): v for k, v in cpu_final.items()},
        "cpu_deltas_ticks": {str(k): v for k, v in cpu_deltas.items()},
        "total_cpu_s": round(total_cpu_s, 2),
        "idle_fraction_est": round(1 - total_cpu_s / max(wall, 0.1), 3),
        "ctxt_switches": switches,
        "clk_tck": CLKTAK,
        "env": {"nproc": os.cpu_count(), "kernel": "5.10.134-kangaroo.al8"},
    }
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("cpu_ticks_final",)}, indent=1)[:2400])
    OUT.mkdir(parents=True, exist_ok=True)
    EVID.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(EVID / "S156_P3_WCHAN_OPENER.json", "w"),
              indent=1, default=str)
    print("-> evidence/s156_record_loop/S156_P3_WCHAN_OPENER.json")


if __name__ == "__main__":
    main()
