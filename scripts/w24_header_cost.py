#!/usr/bin/env python3
"""w24_header_cost.py — HEADER_COST_RANKING.csv from real .d files.

Joins per-header consumer sets (build_w24b1/**/*.d) with per-TU compile wall
from TU_COST_RANKING.csv. Estimated header-attributable parse cost uses the
measured parse+deferred share of small TUs (see COMPILER_PHASE_COSTS.csv,
default 0.22) — a conservative, documented constant, refined after phase
profiling.
"""
import csv
import glob
import os
import re

RANKING = "evidence/w24/TU_COST_RANKING.csv"
DFILES = glob.glob("build_w24b1/**/*.d", recursive=True)
OUT = "evidence/w24/HEADER_COST_RANKING.csv"
PARSE_SHARE = 0.22  # parse+lang-deferred share (refined after COMPILER_PHASE_COSTS)

tu_time = {}
for row in csv.reader(open(RANKING)):
    if len(row) >= 3 and row[0].isdigit():
        tu_time[row[1]] = float(row[2])

hdr_consumers = {}
for df in DFILES:
    src = None
    text = open(df).read().replace("\\\n", " ")
    m = re.match(r"^[^:]+:\s*(.*)$", text, re.S)
    if not m:
        continue
    parts = m.group(1).split()
    parts = [p.replace("\\ ", " ") for p in parts]
    # first entry is the .cpp source; rest are headers
    for p in parts:
        if p.endswith(".cpp"):
            src = p
            continue
        if p.startswith("/usr/"):
            continue  # system headers: not ours to fix
        p = os.path.normpath(p).rstrip(":")
        hdr_consumers.setdefault(p, set()).add(src)

rows = []
for hdr, cons in hdr_consumers.items():
    cons = {c for c in cons if c in tu_time}
    if not cons:
        continue
    total = sum(tu_time[c] for c in cons)
    rows.append((hdr, len(cons), round(total, 2),
                 round(PARSE_SHARE * total, 2), sorted(cons)[:6]))

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["header", "n_consumers", "sum_consumer_compile_s",
                "est_parse_attributable_s", "sample_consumers"])
    for r in sorted(rows, key=lambda r: -r[3])[:60]:
        w.writerow(r)
print(f"headers={len(rows)} dfiles={len(DFILES)}")
for r in sorted(rows, key=lambda r: -r[3])[:15]:
    print(f"  {r[0]}: consumers={r[1]} sum={r[2]}s est_parse={r[3]}s")
