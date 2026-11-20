#!/usr/bin/env python3
"""S14-d timing wrapper: replaces the missing /usr/bin/time -v.
Runs the given command; reports the whole waited process-tree's peak RSS via
os.wait4 rusage (ru_maxrss rolls up reaped descendants — the same metric GNU
time prints) plus wall seconds. Output lines are what scripts/s14_update_ledger.py
and scripts/regen_deliverables.py parse:
    Maximum resident set size (kbytes): N
    Elapsed (wall) seconds: F
    == build rc=N ==
"""
import os, sys, time

if len(sys.argv) < 2:
    raise SystemExit("usage: s14_time_wrapper.py CMD [ARGS...]")
t0 = time.monotonic()
pid = os.fork()
if pid == 0:
    try:
        os.execvp(sys.argv[1], sys.argv[1:])
    except FileNotFoundError as e:
        sys.stderr.write(f"exec failed: {e}\n")
        os._exit(127)
_, status, ru = os.wait4(pid, 0)
wall = time.monotonic() - t0
rc = os.waitstatus_to_exitcode(status) if hasattr(os, "waitstatus_to_exitcode") else os.waitstatus_to_exitcode(status)
print(f"Maximum resident set size (kbytes): {ru.ru_maxrss}")
print(f"Elapsed (wall) seconds: {wall:.2f}")
print(f"== build rc={rc} ==")
sys.exit(0 if rc == 0 else 1)
