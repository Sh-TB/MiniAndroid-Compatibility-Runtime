#!/usr/bin/env python3
"""w24_tu_ranking.py — parse a -j1 FASTPROFILE build log (w22_build_run format:
'<elapsed> <line>') into a true per-TU cost ranking.

At -j1 every event is serial, so duration(event_i) = start(event_{i+1}) - start(event_i).
Emits evidence/w24/TU_COST_RANKING.csv.
"""
import csv
import re
import sys

LOG = sys.argv[1] if len(sys.argv) > 1 else "evidence/w24/RAW_LOGS/w24_fastprofile_j1.log"
OUT = sys.argv[2] if len(sys.argv) > 2 else "evidence/w24/TU_COST_RANKING.csv"

compile_re = re.compile(r"^\s*([0-9.]+) g\+\+ .* -c -o (\S+) (\S+\.cpp)\s*$")
other_re = re.compile(r"^\s*([0-9.]+) (\S+.*\S)\s*$")

events = []
for line in open(LOG, errors="replace"):
    m = compile_re.match(line)
    if m:
        t, obj, src = float(m.group(1)), m.group(2), m.group(3)
        events.append((t, "compile", src, obj, line.strip()))
        continue
    m = other_re.match(line)
    if m:
        t, rest = float(m.group(1)), m.group(2)
        kind = None
        if " -o " in rest and " -c " not in rest and ".cpp" not in rest and ".o " in rest:
            kind = "link"
        elif rest.startswith("ar ") or rest.startswith("ranlib") or rest.startswith("gcc-ar"):
            kind = "archive"
        elif "generate_version_header" in rest:
            kind = "version-gen"
        elif rest.startswith("make"):
            kind = "make-internal"
        if kind:
            events.append((t, kind, rest, "", line.strip()))

events.sort(key=lambda e: e[0])
# true log end time: last elapsed stamp anywhere in the log
log_end = 0.0
for line in open(LOG, errors="replace"):
    m = re.match(r"^\s*([0-9.]+) \S", line)
    if m:
        log_end = max(log_end, float(m.group(1)))
rows = []
for i, (t, kind, src, obj, raw) in enumerate(events):
    end = events[i + 1][0] if i + 1 < len(events) else log_end
    rows.append((kind, src, obj, end - t, raw))

# aggregate: durations of compile events keyed by source TU
tu_time = {}
tu_raw = {}
for kind, src, obj, dur, raw in rows:
    if kind == "compile" and dur > 0.02:
        tu_time[src] = tu_time.get(src, 0.0) + dur
        tu_raw[src] = raw

serial = []
for kind, src, obj, dur, raw in rows:
    if kind in ("link", "archive", "version-gen") and dur > 0.05:
        serial.append((kind, src, dur))

total_compile = sum(tu_time.values())
n = len(tu_time)

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["rank", "tu", "compile_wall_s", "pct_of_compile_total",
                "cmdline_first_160_chars"])
    for r, (src, t) in enumerate(sorted(tu_time.items(), key=lambda kv: -kv[1]), 1):
        w.writerow([r, src, round(t, 2), round(100 * t / total_compile, 2),
                    tu_raw[src][:160]])
    w.writerow([])
    w.writerow(["# TU count", n, "compile CPU-wall sum", round(total_compile, 2)])
    for kind, src, dur in serial:
        w.writerow([f"# {kind}", src[:120], round(dur, 2)])
print(f"TUs={n} compile_wall_sum={total_compile:.2f}s serial_events={len(serial)}")
for kind, src, dur in serial:
    print(f"  {kind}: {dur:.2f}s  {src[:80]}")
