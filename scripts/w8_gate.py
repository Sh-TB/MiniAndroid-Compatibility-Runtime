#!/usr/bin/env python3
"""W8 gate timing: wall + children peak RSS (ru_maxrss) + child CPU for one command.
Usage: w8_gate.py <label> <cmd...>  (run each measurement in a FRESH process so
ru_maxrss is the high-water mark of THAT command's children only)"""
import subprocess, sys, time, os, resource

label = sys.argv[1]
cmd = sys.argv[2:]
t0 = time.monotonic()
r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
wall = time.monotonic() - t0
ru = resource.getrusage(resource.RUSAGE_CHILDREN)
cpu = ru.ru_utime + ru.ru_stime
npass = r.stdout.count("[PASS]")
print(f"{label}|rc={r.returncode}|wall={wall:.2f}s|children_peak_rss={ru.ru_maxrss/1024:.0f}MB|children_cpu={cpu:.2f}s|PASS={npass}")
if r.returncode != 0:
    print("STDERR:", (r.stdout + r.stderr)[-600:])
