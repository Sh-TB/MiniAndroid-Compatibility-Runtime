#!/usr/bin/env python3
"""w22_build_run.py — run one command, stream full timestamped output to a log,
report wall/CPU/peak-RSS/rc as JSON (replaces absent /usr/bin/time -v).

Usage: w22_build_run.py --log <logfile> --out <jsonl> <cmd> [args...]
Each output line is prefixed with elapsed seconds for per-TU timing analysis.
"""
import json
import os
import resource
import subprocess
import sys
import time


def main():
    argv = sys.argv[1:]
    log_path = None
    out_path = None
    while argv and argv[0] in ("--log", "--out"):
        flag = argv[0]
        path = argv[1]
        argv = argv[2:]
        if flag == "--log":
            log_path = path
        else:
            out_path = path
    t0 = time.time()
    p = subprocess.Popen(argv, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    logf = open(log_path, "w") if log_path else None
    for raw in iter(p.stdout.readline, b""):
        line = raw.decode("utf-8", "replace").rstrip("\n")
        stamped = "%8.2f %s" % (time.time() - t0, line)
        if logf:
            logf.write(stamped + "\n")
    p.wait()
    if logf:
        logf.close()
    wall = time.time() - t0
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    rec = {
        "cmd": argv,
        "rc": p.returncode,
        "wall_s": round(wall, 3),
        "cpu_user_s": round(ru.ru_utime, 3),
        "cpu_sys_s": round(ru.ru_stime, 3),
        "maxrss_kb": ru.ru_maxrss,
        "nproc": os.cpu_count(),
        "log": log_path,
    }
    line = json.dumps(rec)
    if out_path:
        with open(out_path, "a") as f:
            f.write(line + "\n")
    sys.stdout.write(line + "\n")


if __name__ == "__main__":
    main()
