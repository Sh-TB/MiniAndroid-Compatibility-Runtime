#!/usr/bin/env python3
"""s156_p3_resolve_v2.py — full symbol resolution:
- exe rips via nm bisect (symtab present, 12k symbols; addr2line fails on -g0 TUs)
- libc/libstdc++ rips via readelf -sW (ALL local symbols, not just dynsym)
Cross-checked against the hist2.maps regions."""
import re
import subprocess
from pathlib import Path

BASE = Path("/home/z/my-project")
HIST = BASE / "run155p2/P3_rip_hist2.txt"
MAPS = BASE / "run155p2/P3_rip_hist2.txt.maps"
EXE = BASE / "miniandroid/build/miniandroid"


def load_syms(path):
    out = subprocess.run(["readelf", "-sW", str(path)], capture_output=True,
                         text=True).stdout
    syms = []
    for l in out.splitlines():
        m = re.match(r"\s*\d+:\s+([0-9a-f]+)\s+(\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)", l)
        if m:
            addr, size, name = int(m.group(1), 16), int(m.group(2)), m.group(3)
            if name and addr:
                syms.append((addr, size, name))
    syms.sort()
    return syms


def resolve(syms, off):
    lo, hi = 0, len(syms)
    best = None
    while lo < hi:
        mid = (lo + hi) // 2
        if syms[mid][0] <= off:
            best = mid; lo = mid + 1
        else:
            hi = mid
    if best is None:
        return "?"
    a, s, n = syms[best]
    inside = " (inside)" if s and off < a + s else " (gap after)"
    return f"{n}{inside}"


base = None
for line in HIST.read_text().splitlines():
    m = re.search(r"base=0x([0-9a-f]+)", line)
    if m:
        base = int(m.group(1), 16)

maps = []
for line in MAPS.read_text().splitlines():
    m = re.match(r"([0-9a-f]+)-([0-9a-f]+) (\S+) \S+ \S+ \S+\s*(.*)", line)
    if m:
        maps.append((int(m.group(1), 16), int(m.group(2), 16), m.group(4).strip()))

exe_syms = load_syms(EXE)
libc_syms = load_syms("/usr/lib/x86_64-linux-gnu/libc.so.6")
std_syms = load_syms("/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33")

rows = []
for line in HIST.read_text().splitlines():
    m = re.match(r"\s*(\d+)\s+([\d.]+)%\s+tid=(\d+)\s+vaddr=0x([0-9a-f]+)", line)
    if m:
        rows.append((int(m.group(1)), int(m.group(3)),
                     int(m.group(4), 16) + base))

agg = {}
out = []
for n, tid, rip in rows:
    path = None
    for lo, hi, p in maps:
        if lo <= rip < hi:
            path = p or "anon"; mlo = lo
            break
    if path == str(EXE):
        sym = resolve(exe_syms, rip - base)
        tag = f"EXE {sym}"
    elif path and "libc.so" in path:
        tag = f"LIBC {resolve(libc_syms, rip - mlo)}"
    elif path and "libstdc++" in path:
        tag = f"STD {resolve(std_syms, rip - mlo)}"
    elif path == "anon":
        tag = "ANON"
    else:
        tag = f"{path}"
    agg.setdefault((tid, tag), [0, rip])
    agg[(tid, tag)][0] += n

print(f"# total={sum(r[0] for r in rows)}")
for (tid, tag), (n, rip) in sorted(agg.items(), key=lambda kv: -kv[1][0])[:36]:
    print(f"{n:6d} tid={tid}  {tag}")
