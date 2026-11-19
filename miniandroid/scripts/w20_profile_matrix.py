#!/usr/bin/env python3
"""W20-P2: measure the 12 dev PIC TUs at -O2 (current dev profile) vs -O1
(candidate dev profile). Isolated serial compiles, wall + peak RSS each.
Peak RSS via getrusage(RUSAGE_CHILDREN) is CUMULATIVE-MAX across children;
reset per child by sampling in a fresh subprocess wrapper."""
import subprocess
import sys
import time

INC = ('-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api '
       '-Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer '
       '-Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni '
       '-Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 '
       '-Ithird_party/nlohmann_json/include').split()
BASE = ['-std=c++17', '-Wall', '-Wextra', '-g0', '-fPIC',
        '-DMINIANDROID_HAVE_WEBP']

PARTS = ['dalvik_bridge', 'dalvik_bridge_domain_jdk',
         'dalvik_bridge_domain_android_core',
         'dalvik_bridge_domain_ui_graphics',
         'dalvik_bridge_domain_app_runtime',
         'dalvik_bridge_domain_io_lang', 'dalvik_engine_core',
         'dalvik_engine_invoke', 'dalvik_engine_tail', 'dalvik_interpreter',
         'dalvik_opcodes', 'dalvik_opcodes_invoke']

# Wrapper: measure ONE g++ in an isolated python child (fresh rusage).
WRAP = r'''
import resource, subprocess, sys, time
t0=time.monotonic()
p=subprocess.run(sys.argv[1:], capture_output=True, text=True)
w=time.monotonic()-t0
r=resource.getrusage(resource.RUSAGE_CHILDREN)
print(f"RESULT {p.returncode} {w:.1f} {r.ru_maxrss//1024}")
'''


def one(tu, opt):
    flags = BASE + ([f'-{opt}'] if opt != 'O2' else []) + INC + [
        '-c', '-o', f'/tmp/w20_{tu}_{opt}.o', f'src/dex/{tu}.cpp']
    # remove default -O2 if opt != O2: BASE has none, we append opt
    p = subprocess.run([sys.executable, '-c', WRAP, 'g++', *flags],
                       capture_output=True, text=True)
    out = p.stdout.strip().split()
    assert out[0] == 'RESULT', p.stdout
    rc, wall, rss = out[1], out[2], out[3]
    print(f'{tu:38s} -{opt}: rc={rc} wall={wall}s rss={rss}MB')
    return float(wall)


tot = {'O2': 0.0, 'O1': 0.0}
for tu in PARTS:
    tot['O2'] += one(tu, 'O2')
    tot['O1'] += one(tu, 'O1')
print(f"TOTAL 12-TU serial: -O2={tot['O2']:.1f}s  -O1={tot['O1']:.1f}s "
      f"({tot['O2']/tot['O1']:.2f}x)")
