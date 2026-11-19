#!/usr/bin/env python3
"""w21_runner.py — run one command, report wall/CPU/peak-RSS/rc as JSON.

One fresh process per measured command, so RUSAGE_CHILDREN is exactly that
command's subtree (ru_maxrss = peak RSS in KB, utime+stime = CPU seconds).
Replacement for the absent /usr/bin/time -v on this host.
Usage: w21_runner.py <cmd> [args...] [--out <jsonl>]
"""
import json
import resource
import subprocess
import sys
import time


def main():
    argv = sys.argv[1:]
    out_path = None
    if "--out" in argv:
        i = argv.index("--out")
        out_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    t0 = time.time()
    p = subprocess.run(argv, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    wall = time.time() - t0
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    rec = {
        "cmd": argv,
        "rc": p.returncode,
        "wall_s": round(wall, 3),
        "cpu_user_s": round(ru.ru_utime, 3),
        "cpu_sys_s": round(ru.ru_stime, 3),
        "maxrss_kb": ru.ru_maxrss,
        "nproc": __import__("os").cpu_count(),
    }
    line = json.dumps(rec)
    if out_path:
        with open(out_path, "a") as f:
            f.write(line + "\n")
    sys.stdout.write(line + "\n")
    # child output passthrough (kept, may be large)
    sys.stderr.write(p.stdout.decode("utf-8", "replace")[-20000:])


if __name__ == "__main__":
    main()
