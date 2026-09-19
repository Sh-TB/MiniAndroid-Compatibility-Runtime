#!/usr/bin/env python3
"""S62: extract per-class-init durations from a timestamped stderr log.
Pairs [CLASS_INIT] class=X method=<clinit> bytecode_size=N (start) with the
matching result= line (end) and reports the heaviest chains."""
import re, sys

path = sys.argv[1] if len(sys.argv) > 1 else 'run/s62_buckets/stderr_t.log'
start_re = re.compile(r'^\s*([\d.]+) \[CLASS_INIT\] class=(\S+) method=<clinit> bytecode_size=(\d+)')
end_re = re.compile(r'^\s*([\d.]+) \[CLASS_INIT\] class=(\S+) method=<clinit> result=')

stack = []          # (t0, cls, size) — nested inits pair LIFO
durations = []      # (dur, cls, size, depth)
for line in open(path, encoding='utf-8', errors='replace'):
    m = start_re.match(line)
    if m:
        stack.append((float(m.group(1)), m.group(2), int(m.group(3))))
        continue
    m = end_re.match(line)
    if m and stack:
        t0, cls, size = stack.pop()
        # match: assume result line is for the same class (nearest start w/ same class)
        if cls != m.group(2):
            # tolerate mismatched pairing; push back and try to find match
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][1] == m.group(2):
                    t0, cls, size = stack.pop(i)
                    break
            else:
                continue
        dur = float(m.group(1)) - t0
        durations.append((dur, cls, size, len(stack) + 1))

durations.sort(reverse=True)
tot = sum(d for d, *_ in durations)
print("chains=%d  total_class_init_seconds=%.1f" % (len(durations), tot))
print("top 20 heaviest cold <clinit> chains:")
for d, cls, size, depth in durations[:20]:
    print("  %8.2fs  depth=%2d  size=%6s  %s" % (d, depth, size, cls))
# concentration
top10 = sum(d for d, *_ in durations[:10])
top50 = sum(d for d, *_ in durations[:50])
if durations:
    print("top10=%.1fs (%.0f%%)  top50=%.1fs (%.0f%%)  median=%.3fs" % (
        top10, 100 * top10 / tot, top50, 100 * top50 / tot,
        durations[len(durations)//2][0]))
