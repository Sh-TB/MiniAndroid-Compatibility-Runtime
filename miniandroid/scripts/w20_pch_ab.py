#!/usr/bin/env python3
"""W20-P2: PCH A/B on one heavy TU (dalvik_engine_core.cpp, dev PIC flags).
Measures wall + peak RSS + warns on PCH activation failure."""
import resource
import subprocess
import sys
import time

INC = ('-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api '
       '-Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer '
       '-Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni '
       '-Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 '
       '-Ithird_party/nlohmann_json/include').split()
JSON = []
BASE = ['-std=c++17', '-Wall', '-Wextra', '-g', '-O2', '-g0', '-fPIC',
        '-DMINIANDROID_HAVE_WEBP']
TU = 'src/dex/dalvik_engine_core.cpp'


def run(name, extra):
    t0 = time.monotonic()
    p = subprocess.run(['g++', *BASE, *INC, *JSON, *extra, '-c', '-o',
                        f'/tmp/w20_{name}.o', TU],
                       capture_output=True, text=True)
    wall = time.monotonic() - t0
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    pch_warn = [l for l in p.stderr.splitlines() if 'pch' in l.lower()]
    print(f'{name}: rc={p.returncode} wall={wall:.1f}s '
          f'peakRSS={rss//1024}MB warnings={len(p.stderr.splitlines())}')
    for l in pch_warn[:2]:
        print('  ', l[:110])
    return wall


w0 = run('no_pch', [])
w1 = run('pch', ['-include', 'src/dex/dalvik_engine.h',
                 '-Winvalid-pch', '-I/tmp/w20_pchdir'])
print(f'speedup: {w0/w1:.2f}x  saved: {w0-w1:.1f}s')
