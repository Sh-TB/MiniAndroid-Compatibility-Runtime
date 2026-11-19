#!/usr/bin/env python3
"""W19-2/W19-4: serial production build wrapper — captures elapsed time,
child peak RSS (getrusage(RUSAGE_CHILDREN), the counter /usr/bin/time -v
reports; /usr/bin/time is absent on this host), exit status, and tees the
full build log. Usage: p0_build_wrap.py <logfile> <make args...>"""
import os
import resource
import subprocess
import sys
import time

logfile, mk_args = sys.argv[1], sys.argv[2:]
t0 = time.monotonic()
with open(logfile, 'w') as fh:
    p = subprocess.Popen(['make', *mk_args, '-j1'], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    for line in p.stdout:
        fh.write(line)
        fh.flush()
    rc = p.wait()
wall = time.monotonic() - t0
peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
with open(logfile, 'a') as fh:
    fh.write(f'\n[WRAPPER] exit={rc} wall={wall:.1f}s '
             f'peak_child_RSS={peak} KB\n')
print(f'[WRAPPER] exit={rc} wall={wall:.1f}s peak_child_RSS={peak} KB')
