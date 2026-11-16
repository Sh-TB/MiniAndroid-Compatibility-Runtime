#!/usr/bin/env python3
"""#612 measurement harness: run a build command, record wall + peak RSS."""
import resource, subprocess, sys, time

argv = sys.argv[1:]
t0 = time.time()
p = subprocess.run(argv)
wall = time.time() - t0
ru = resource.getrusage(resource.RUSAGE_CHILDREN)
print(f"\nMEASURE rc={p.returncode} wall={wall:.1f}s user={ru.ru_utime:.1f}s "
      f"sys={ru.ru_stime:.1f}s peakRSS={ru.ru_maxrss/1024:.0f}MiB")
sys.exit(p.returncode)
