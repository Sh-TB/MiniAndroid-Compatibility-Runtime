#!/usr/bin/env python3
"""W20-P1/P2: verify the independent coder's dalvik_engine_tail.cpp finding
at the REAL production flags (INCLUDES + JSON_INCLUDE from the Makefile).
Runs `g++ -fsyntax-only` twice (with / without line 41) and reports true rc."""
import re
import subprocess
import sys

mk = open('Makefile').read()


def expand(var):
    """Expand a Makefile variable one level (handles += and $(VAR) refs)."""
    m = re.search(rf'^{var}\s*[+:?]?=\s*(.*)$', mk, re.M)
    if not m:
        return ''
    val = m.group(1)
    for ref, _ in re.findall(r'\$\((\w+)\s*(:?=.*)?\)', val):
        if ref != var:
            val = val.replace(f'$({ref})', expand(ref))
    return val


inc = expand('INCLUDES').replace('$(SRCDIR)', 'src') + \
    ' ' + expand('JSON_INCLUDE').replace('$(JSON_DIR)', 'third_party/json')
print('INCLUDES:', inc[:120])

src = open('src/dex/dalvik_engine_tail.cpp').read().splitlines(keepends=True)
flags = ['g++', '-std=c++17', '-Wall', '-Wextra', '-O2', '-g0',
         '-DMINIANDROID_HAVE_WEBP', *inc.split(), '-fsyntax-only']

r1 = subprocess.run(flags + ['src/dex/dalvik_engine_tail.cpp'],
                    capture_output=True, text=True)
print('WITH android_shadows.h include: rc =', r1.returncode,
      '| stderr lines:', len(r1.stderr.splitlines()))

no_inc = [l for i, l in enumerate(src) if i != 40]  # line 41 = index 40
open('/tmp/w20_tail_no.cpp', 'w').write(''.join(no_inc))
r2 = subprocess.run(flags + ['/tmp/w20_tail_no.cpp'],
                    capture_output=True, text=True)
print('WITHOUT include (removed line 41): rc =', r2.returncode,
      '| stderr lines:', len(r2.stderr.splitlines()))
if r2.returncode:
    print(r2.stderr[:600])
