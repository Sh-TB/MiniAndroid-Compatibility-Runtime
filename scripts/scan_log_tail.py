#!/usr/bin/env python3
"""Scan the tail of a huge run.log and count method-loop signatures."""
import collections, sys

path = sys.argv[1]
tail_bytes = int(sys.argv[2]) if len(sys.argv) > 2 else 8_000_000
with open(path, 'rb') as f:
    f.seek(0, 2)
    size = f.tell()
    f.seek(max(0, size - tail_bytes))
    buf = f.read().decode('utf-8', 'ignore')

c = collections.Counter()
for line in buf.splitlines():
    if 'RECURSIVE INVOKE:' in line:
        name = line.split('RECURSIVE INVOKE:')[1].split('(')[0].strip()
        c['INVOKE ' + name] += 1
    elif 'Executing: ' in line:
        c['EXEC ' + line.split('Executing:')[1].strip()] += 1
    elif 'UNIMPLEMENTED: 0x' in line:
        c[line.strip()[:60]] += 1

for k, v in c.most_common(10):
    print(v, k)
