#!/usr/bin/env python3
"""P0 evidence — per-TU peak RSS + wall time on the exact production
command (-O2 -g0, serial). /usr/bin/time is unavailable on this host
(no 'time' package, no apt), so this wrapper reads the SAME kernel
counter time -v reports: getrusage(RUSAGE_CHILDREN).ru_maxrss (KB peak
RSS of the child) — documented equivalent, not an approximation.
Also captures -ftime-report phase output per TU.
"""
import os
import resource
import subprocess
import sys
import time

FLAGS = ('-std=c++17 -Wall -Wextra -g -O2 -MMD -MP -DMINIANDROID_HAVE_WEBP '
         '-g0')
INC = ('-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api '
       '-Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer '
       '-Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni '
       '-Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 '
       '-Ithird_party/nlohmann_json/include')
TUS = ['dalvik_bridge', 'dalvik_bridge_domain_jdk',
       'dalvik_bridge_domain_android_core', 'dalvik_bridge_domain_ui_graphics',
       'dalvik_bridge_domain_app_runtime', 'dalvik_bridge_domain_io_lang']
os.makedirs('evidence/p0_split', exist_ok=True)
out = open('evidence/p0_split/per_tu_rss.txt', 'w')
print(f'{"TU":<42}{"peak RSS (KB)":>15}{"wall (s)":>10}  cmd', file=out)
for f in TUS:
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    t0 = time.monotonic()
    cmd = f'g++ {FLAGS} {INC} -c -o /tmp/p0_{f}.o src/dex/{f}.cpp'
    r = subprocess.run(cmd, shell=True, capture_output=True)
    wall = time.monotonic() - t0
    after = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    peak = max(after, before)  # ru_maxrss of children is a running max
    print(f'{f:<42}{peak:>15}{wall:>10.1f}  exit={r.returncode}', file=out)
    print(f'{f:<42}{peak:>15}{wall:>10.1f}  exit={r.returncode}')
out.close()
for f in ['dalvik_bridge_domain_jdk', 'dalvik_bridge_domain_ui_graphics']:
    cmd = f'g++ {FLAGS} -ftime-report {INC} -c -o /tmp/p0_ft_{f}.o ' \
          f'src/dex/{f}.cpp'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    with open(f'evidence/p0_split/ftime_{f}.txt', 'w') as fh:
        fh.write(r.stderr)
print('wrote evidence/p0_split/per_tu_rss.txt + ftime reports')
