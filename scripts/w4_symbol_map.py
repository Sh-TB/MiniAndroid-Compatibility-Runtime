#!/usr/bin/env python3
"""W4 symbol map: compiler-truth function inventory of the built
dalvik_engine.o — symbol addresses, text sizes, source start lines.
Used for (a) the Phase-1 cost ranking (real object text sizes) and
(b) TU-split boundaries (contiguous start-line ranges)."""
import subprocess, json, re

OBJ = "/tmp/w4_g1.o"
nm = subprocess.run(["nm", "--defined-only", "--print-size", "--size-sort",
                     "-C", OBJ], capture_output=True, text=True).stdout
syms = []
for line in nm.splitlines():
    m = re.match(r"([0-9a-f]+) ([0-9a-f]+) ([TtWw]) (.+)", line)
    if m:
        syms.append({"addr": int(m.group(1), 16), "size": int(m.group(2), 16),
                     "name": m.group(4)})
# addr2line for all start addresses
addrs = "\n".join(hex(s["addr"]) for s in syms)
a2l = subprocess.run(["addr2line", "-e", OBJ, "-f", "--inline"],
                     input=addrs, capture_output=True, text=True).stdout
pairs = a2l.splitlines()
for k, s in enumerate(syms):
    loc = pairs[2 * k + 1] if 2 * k + 1 < len(pairs) else "??:0"
    mm = re.match(r"(.+):(\d+)", loc)
    s["file"] = mm.group(1) if mm else "?"
    s["line"] = int(mm.group(2)) if mm else 0

mine = [s for s in syms if s["file"].endswith("dalvik_engine.cpp") and s["line"] > 0]
mine.sort(key=lambda s: s["line"])
total_text = sum(s["size"] for s in mine)
print(f"text symbols from dalvik_engine.cpp: {len(mine)}, total text "
      f"{total_text/1e6:.2f} MB")
print("\nTOP 30 by TEXT SIZE (bytes — real generated code):")
for s in sorted(mine, key=lambda x: -x["size"])[:30]:
    print(f"  {s['size']:9d}  line {s['line']:6d}  {s['name'][:70]}")
json.dump(mine, open("evidence/issue612_audit/wave4_symbol_map.json", "w"), indent=1)
print("\nsaved evidence/issue612_audit/wave4_symbol_map.json")
