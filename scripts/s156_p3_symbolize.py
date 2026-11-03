#!/usr/bin/env python3
"""s156_p3_symbolize.py — resolve tracer RIP histogram entries against
/proc maps + addr2line. Per-tid attribution + per-mapping attribution +
full exe-side function ranking."""
import re
import subprocess
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
HIST = BASE / "run155p2/P3_rip_hist2.txt"
MAPS = BASE / "run155p2/P3_rip_hist2.txt.maps"
EXE = BASE / "miniandroid/build/miniandroid"
OUT = BASE / "evidence/s156_record_loop/S156_P3_RIP_SYMBOLIZED.txt"

rows = []
for line in HIST.read_text().splitlines():
    if line.startswith("#"):
        m = re.search(r"base=0x([0-9a-f]+)", line)
        base = int(m.group(1), 16) if m else 0
        continue
    m = re.match(r"\s*(\d+)\s+([\d.]+)%\s+tid=(\d+)\s+vaddr=0x([0-9a-f]+)", line)
    if m:
        rows.append({"n": int(m.group(1)), "pct": float(m.group(2)),
                     "tid": int(m.group(3)), "rip": int(m.group(4), 16) + base})

maps = []
for line in MAPS.read_text().splitlines():
    m = re.match(r"([0-9a-f]+)-([0-9a-f]+) (\S+) \S+ \S+ \S+\s*(.*)", line)
    if m:
        maps.append((int(m.group(1), 16), int(m.group(2), 16),
                     m.group(3), m.group(4).strip()))


def find_map(rip):
    for lo, hi, perm, path in maps:
        if lo <= rip < hi:
            return lo, hi, perm, path
    return None


def addr2line_sym(vaddr):
    try:
        r = subprocess.run(["addr2line", "-f", "-C", "-e", str(EXE),
                            hex(vaddr)], capture_output=True, text=True,
                           timeout=10)
        lines = r.stdout.strip().splitlines()
        return lines[0] if lines else "?", (lines[1] if len(lines) > 1 else "?")
    except Exception:
        return "?", "?"


by_map, by_tid = {}, {}
exe_funcs = {}
out_lines = []
for r in rows:
    mm = find_map(r["rip"])
    if not mm:
        tag, detail = "unmapped", "?"
    else:
        lo, hi, perm, path = mm
        short = path or "anon"
        off = r["rip"] - lo
        tag = short
        detail = f"+0x{off:x}"
        by_map[short] = by_map.get(short, 0) + r["n"]
        if path == str(EXE):
            vaddr = r["rip"] - base
            sym, loc = addr2line_sym(vaddr)
            detail = f"{sym} @ {loc}"
            exe_funcs.setdefault(sym, [0, loc])
            exe_funcs[sym][0] += r["n"]
    by_tid[r["tid"]] = by_tid.get(r["tid"], 0) + r["n"]
    out_lines.append(f"{r['n']:6d} {r['pct']:6.2f}% tid={r['tid']}  {tag} {detail}")

total = sum(r["n"] for r in rows)
out_lines.append("")
out_lines.append(f"# total={total}")
out_lines.append("# per-tid:")
for tid, n in sorted(by_tid.items(), key=lambda kv: -kv[1]):
    out_lines.append(f"  tid={tid}: {n} ({100.0*n/total:.1f}%)")
out_lines.append("# per-mapping:")
for k, n in sorted(by_map.items(), key=lambda kv: -kv[1]):
    out_lines.append(f"  {n:6d} ({100.0*n/total:5.1f}%)  {k}")
out_lines.append("# exe function ranking:")
for sym, (n, loc) in sorted(exe_funcs.items(), key=lambda kv: -kv[1][0]):
    out_lines.append(f"  {n:6d} ({100.0*n/total:5.1f}%)  {sym} @ {loc}")

OUT.write_text("\n".join(out_lines) + "\n")
print("\n".join(out_lines[-40:]))
print(f"-> {OUT}")
