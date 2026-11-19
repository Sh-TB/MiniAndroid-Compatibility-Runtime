#!/usr/bin/env python3
"""w22_tu_profile.py — parse the timestamped fresh-build log into per-TU
compile durations; also extract the final link duration. B2 evidence."""
import re
import sys

LOG = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/my-project/miniandroid/evidence/w22/prod_build_fresh.log"
rows = []
for line in open(LOG):
    m = re.match(r"\s*(\d+\.\d\d)\s+(.*)", line.rstrip())
    if not m:
        continue
    t, txt = float(m.group(1)), m.group(2)
    rows.append((t, txt))

compiles = []
link_t0 = None
# compile START stamps; slot_N = start_{N+1} - start_N (warnings inside the
# slot have intermediate stamps and must not terminate the slot)
for t, txt in rows:
    if " -c -o " in txt:
        m = re.search(r" -c -o (\S+)\s*(\S+)?", txt)
        src = m.group(2) if (m and m.group(2)) else "?"
        compiles.append([t, src, m.group(1) if m else "?"])
    if " -rdynamic " in txt or (" -o build/miniandroid " in txt and " -c " not in txt):
        link_t0 = t

slots = []
for i, (t0, src, obj) in enumerate(compiles):
    t1 = compiles[i + 1][0] if i + 1 < len(compiles) else (link_t0 or t0)
    slots.append((t1 - t0, src, obj))
slots.sort(reverse=True)
compiles = slots

compiles.sort(reverse=True)
total_c = sum(d for d, _, _ in compiles)
print("TOTAL_TUS %d  total_compile_s %.1f  link_s %s" % (
    len(compiles), total_c,
    ("%.1f" % (slots[-1][0])) if compiles else "n/a"))
print("\nTOP15 compile TUs (s | source | object):")
for d, src, obj in compiles[:15]:
    print("  %6.2f  %s" % (d, src))
print("\nBottom quads (fastest 4):")
for d, src, _ in compiles[-4:]:
    print("  %6.2f  %s" % (d, src))
print("\nBucket counts: >=100s %d | 30-100s %d | 10-30s %d | <10s %d" % (
    sum(1 for d, _, _ in compiles if d >= 100),
    sum(1 for d, _, _ in compiles if 30 <= d < 100),
    sum(1 for d, _, _ in compiles if 10 <= d < 30),
    sum(1 for d, _, _ in compiles if d < 10)))
