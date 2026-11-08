#!/usr/bin/env python3
"""S188-W15 — p9 faulting-constructor attribution run.

W14 pinned NEXT: the p9 libgdx.so dlopen faults (SIGSEGV fault_addr=0x0)
but the S100-CRASH-FORENSICS row lacked the faulting IP (backtrace cannot
cross the signal frame). Two observability fixes landed:
  1. crash_forensics.cpp handler now captures the faulting IP from the
     ucontext and attributes it (dladdr + /proc/self/maps fallback).
  2. dlopen_exec.cpp logs honest phase rows (deps-prep begin/done,
     fork-probe child begin/done + verdict + waitpid status, parent
     dlopen begin) so the log itself proves WHICH process/phase faulted.

This run re-executes p9 and extracts those rows for attribution.
Outputs land in evidence/s188_w15/.
"""
import json, re, shutil, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

w2.OUT = BASE / 'evidence/s188_w15'
w2.RUNS = w2.OUT / 'runs'
w2.OUT.mkdir(parents=True, exist_ok=True)

PKG = 'se.tube42.p9.android'

print('==', PKG, flush=True)
apk = BASE / f'upload/stuck_apks/{PKG}.apk'
shutil.rmtree(w2.RUNS / f'store_{PKG}', ignore_errors=True)
r = w2.run_one(PKG, str(apk))

log = (w2.OUT / f'{PKG}.console.log').read_text(errors='ignore')
lines = log.splitlines()

phase_rows = [l for l in lines if l.startswith('[DLOPEN-PHASE]')]
faultip_rows = [l for l in lines if l.startswith('[S100-FAULT-IP]')]
forensics_head = [l for l in lines if l.startswith('[S100-CRASH-FORENSICS]')]
s2_rows = [l for l in lines if l.startswith('[S2-NATIVE]') and 'gdx' in l]
gdx_host = [l for l in lines if '[GDX-HOST]' in l]

out = dict(
    binary_sha16_new='bde6fa563a0661d4',
    status=r.get('status'), tier=r.get('tier'),
    uncaught=r.get('uncaught_marks'),
    route_decision=r.get('route_decision'),
    dlopen_phase_rows=phase_rows,
    fault_ip_rows=faultip_rows,
    forensics_head_rows=forensics_head,
    s2_native_rows=s2_rows,
    gdx_host_rows=gdx_host,
)
(w2.OUT / 'W15_FAULT_ATTR.json').write_text(json.dumps(out, indent=1))
print('--- DLOPEN-PHASE ---')
for l in phase_rows:
    print(l)
print('--- FAULT-IP ---')
for l in faultip_rows:
    print(l)
print('--- FORENSICS HEAD ---')
for l in forensics_head:
    print(l)
print('--- S2-NATIVE ---')
for l in s2_rows:
    print(l)
print('status=', r.get('status'), 'tier=', r.get('tier'),
      'uncaught=', r.get('uncaught_marks'), flush=True)
