#!/usr/bin/env python3
"""Isolated per-TU peak-RSS measurement: one compile per process so
getrusage(RUSAGE_CHILDREN).ru_maxrss reports THAT TU's peak (the counter
is a running max across children — same-process loops mask later TUs).
Usage: p0_measure_one.py <src-basename> <flags...>
"""
import resource
import subprocess
import sys
import time

f = sys.argv[1]
flags = sys.argv[2]
INC = ('-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api '
       '-Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer '
       '-Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni '
       '-Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 '
       '-Ithird_party/nlohmann_json/include')
t0 = time.monotonic()
cmd = f'g++ {flags} {INC} -c -o /tmp/p0_iso_{f}.o src/dex/{f}.cpp'
r = subprocess.run(cmd, shell=True, capture_output=True)
wall = time.monotonic() - t0
peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
print(f'{f:<42}{peak:>12} KB{wall:>9.1f} s  exit={r.returncode}')
