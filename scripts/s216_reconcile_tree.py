#!/usr/bin/env python3
"""S216 source-tree reconciliation:
1. Restore the 4 wave-target source files to 01586a17 state.
2. Re-apply ONLY the local R14 superclass-first class-init hunk (the earlier
   S216 instance's own A-R3 fix, env-gated MINIANDROID_R14_SUPER_INIT).
3. Leave the tree ready for the CONT-131 wave parts 1-4 (applied separately).
"""
import re, subprocess, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
LOCAL_DIFF = Path('/tmp/local_src.diff')
KEEP_HUNK_START = 6747  # the R14 hunk in dalvik_engine.cpp
OUT = BASE / 'evidence/s216/r14_replay.diff'

d = LOCAL_DIFF.read_text()
# Split into per-file sections
files = re.split(r'^diff --git ', d, flags=re.M)
kept = []
for f in files:
    if not f.strip():
        continue
    m = re.match(r'a/(\S+) b/(\S+)', f)
    path = m.group(2)
    # split hunks
    hunk_iter = list(re.finditer(r'(?m)^@@ -(\d+),?\d* \+\d+,?\d* @@', f))
    for i, hm in enumerate(hunk_iter):
        start_line = int(hm.group(1))
        hstart = hm.start()
        hend = hunk_iter[i + 1].start() if i + 1 < len(hunk_iter) else len(f)
        hunk = f[hstart:hend]
        if path == 'miniandroid/src/dex/dalvik_engine.cpp' and start_line == KEEP_HUNK_START:
            kept.append((path, hunk))

assert kept, 'R14 hunk not found'
# Rebuild a valid single-file diff: header from the original section
header = None
for f in files:
    if 'a/miniandroid/src/dex/dalvik_engine.cpp' in f.splitlines()[0] if f.strip() else False:
        header_lines = []
        for ln in f.splitlines():
            if ln.startswith('@@'):
                break
            header_lines.append(ln)
        header = '\n'.join(header_lines) + '\n'
        break

body = ''.join(h for _, h in kept)
OUT.write_text(header + body)
print(f'R14 replay diff written: {OUT} ({len(body.splitlines())} hunk lines)')

# 1. Restore source files to 01586a17
files_at_base = [
    'miniandroid/src/dex/dalvik_engine.cpp',
    'miniandroid/src/dex/dalvik_engine.h',
    'miniandroid/src/runtime/execution_engine.h',
    'miniandroid/src/runtime/execution_engine.cpp',
]
subprocess.run(['git', 'checkout', '01586a17', '--'] + files_at_base, cwd=BASE, check=True)
print('source files restored to 01586a17')

# 2. Re-apply the R14 hunk
r = subprocess.run(['git', 'apply', str(OUT)], cwd=BASE, capture_output=True, text=True)
print('R14 apply rc=', r.returncode, r.stderr[:300])
if r.returncode == 0:
    # 3. Verify the tree is now 01586a17 + R14 exactly
    st = subprocess.run(['git', 'diff', '--stat', '01586a17', '--', 'miniandroid/src/'],
                        cwd=BASE, capture_output=True, text=True).stdout
    print('tree vs 01586a17 after R14 replay:')
    print(st)
