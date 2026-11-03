#!/usr/bin/env python3
"""s156_phase3_fault_probe.py — sample the BUSY thread's fault profile over
time: majflt/minflt growth on the engine thread. If majflt grows during the
spin, the CPU-bound churn is actually PAGE-CACHE thrashing on mmap'd fonts
(or heap) — a memory-pressure pathology that explains VM-state dependence
without any binary difference. Also samples process /proc/PID/io read_bytes
(disk reads from mmap faults) and RSS."""
import json
import os
import re
import subprocess
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid"
OUT = BASE / "run155p2"
EVID = BASE / "evidence/s156_record_loop"
STORE = OUT / "store_A/data"
RUN_SECONDS = 60
VERDICT_RE = re.compile(r"FRAME_ANALYSIS state=(\S+)")


def tstat(pid, tid):
    try:
        stat = Path(f"/proc/{pid}/task/{tid}/stat").read_text()
        after = stat[stat.rindex(")") + 2:].split()
        return {"state": after[0], "minflt": int(after[5]),
                "majflt": int(after[7]), "utime": int(after[11]),
                "stime": int(after[12])}
    except (FileNotFoundError, ProcessLookupError, ValueError):
        return None


def io_bytes(pid):
    try:
        txt = Path(f"/proc/{pid}/io").read_text()
        return {k: int(v) for k, v in
                (l.split(": ") for l in txt.strip().splitlines())}
    except (FileNotFoundError, ProcessLookupError):
        return None


def rss_kb(pid):
    try:
        txt = Path(f"/proc/{pid}/status").read_text()
        return int(re.search(r"VmRSS:\s+(\d+)", txt).group(1))
    except (FileNotFoundError, ProcessLookupError, AttributeError):
        return None


def main():
    rundir = OUT / "P3_fault"
    console = OUT / "P3_fault_console.log"
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(STORE), "-o", str(rundir),
           "--max-seconds", str(RUN_SECONDS), "--frames", "30", "--trace",
           "--package", "io.github.yamin8000.dooz"]
    t0 = time.time()
    series = []
    with open(console, "w") as cf:
        proc = subprocess.Popen(cmd, stdout=cf, stderr=subprocess.STDOUT)
        pid = proc.pid
        first_seen = {}
        while proc.poll() is None and time.time() - t0 < RUN_SECONDS + 25:
            now = round(time.time() - t0, 2)
            try:
                tids = [int(d) for d in os.listdir(f"/proc/{pid}/task")
                        if d.isdigit()]
            except FileNotFoundError:
                break
            row = {"t": now}
            for tid in tids:
                s = tstat(pid, tid)
                if s:
                    key = tid if tid != pid else "main"
                    row[str(key)] = s
                    if key not in first_seen and s["utime"] > 0:
                        first_seen[key] = True
            row["rss_kb"] = rss_kb(pid)
            row["io"] = io_bytes(pid)
            series.append(row)
            time.sleep(1.0)
        wall = round(time.time() - t0, 1)
    proc.wait(timeout=20)
    text = console.read_text(errors="replace")
    verdict = (VERDICT_RE.findall(text) or [None])[-1]

    # find the busy thread (max utime growth) and report its fault curve
    result = {"verdict": verdict, "wall_s": wall, "n_samples": len(series),
              "series": series}
    EVID.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(EVID / "S156_P3_FAULT_CURVE.json", "w"),
              indent=1, default=str)
    # console summary: per-thread majflt/minflt first->last
    if series:
        f, l = series[1] if len(series) > 1 else series[0], series[-1]
        for key in ("main", "2"):
            if key in f and key in l:
                df = f[key]; dl = l[key]
                print(f"thread {key}: majflt {df['majflt']}->{dl['majflt']} "
                      f"(d={dl['majflt']-df['majflt']}), minflt "
                      f"{df['minflt']}->{dl['minflt']} "
                      f"(d={dl['minflt']-df['minflt']}), utime+stime "
                      f"{df['utime']+df['stime']}->{dl['utime']+dl['stime']} "
                      f"(d={dl['utime']+dl['stime']-df['utime']-df['stime']})")
        print(f"RSS: {f.get('rss_kb')}KB -> {l.get('rss_kb')}KB")
        io_f = f.get("io") or {}; io_l = l.get("io") or {}
        print(f"io.read_bytes: {io_f.get('read_bytes')} -> "
              f"{io_l.get('read_bytes')} "
              f"(d={io_l.get('read_bytes', 0)-io_f.get('read_bytes', 0)})")
        print(f"io.majflt-relevant rbytes: {io_f.get('rbytes')} -> "
              f"{io_l.get('rbytes')}")
    print("-> evidence/s156_record_loop/S156_P3_FAULT_CURVE.json")


if __name__ == "__main__":
    main()
