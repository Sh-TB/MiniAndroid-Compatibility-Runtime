#!/usr/bin/env python3
"""S188-W9b: dense spin attribution — raw syscall text, kernel stacks,
dense ptrace RIP sampling with full-module symbolization (incl. libapp.so),
and a final maps snapshot. Focus tids: the two spinners (1.raster/1.io) and
the two futex-blocked miniandroid threads.
"""
import ctypes, json, os, re, subprocess, sys, time, hashlib
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w9'
RUNS = BASE / 'evidence/s188_w2/runs'
SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
OUT.mkdir(parents=True, exist_ok=True)
STORE = RUNS / 'store_com.sidhant.queens'
dpkg = [d.name for d in sorted((STORE / 'data' / 'app').iterdir())
        if d.is_dir() and not d.name.startswith('.') and (d / 'base.apk').exists()][0]
rundir = RUNS / 'w9b_dense'
console = OUT / 'w9b_queens.console.log'

def load_symbols(path):
    syms = []
    try:
        txt = subprocess.run(['readelf', '-sW', str(path)], capture_output=True,
                             text=True, timeout=60).stdout
        for line in txt.splitlines():
            m = re.match(r'\s*\d+:\s+([0-9a-f]+)\s+(\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)', line)
            if m and int(m.group(1), 16) and m.group(3) not in ('', '*UND*'):
                syms.append((int(m.group(1), 16), int(m.group(2)), m.group(3)))
    except Exception:
        pass
    syms.sort()
    return syms

FL = STORE / f'data/app/{dpkg}/lib/x86_64/libflutter.so'
LA = STORE / f'data/app/{dpkg}/lib/x86_64/libapp.so'
SYMS = {'libflutter.so': load_symbols(FL), 'libapp.so': load_symbols(LA),
        'miniandroid': load_symbols(BIN),
        'libc.so.6': load_symbols('/lib/x86_64-linux-gnu/libc.so.6'),
        'libstdc++.so.6': load_symbols('/lib/x86_64-linux-gnu/libstdc++.so.6'),
        'libpthread.so.0': load_symbols('/lib/x86_64-linux-gnu/libpthread.so.0')}

def symbolize(mod, off):
    lst = SYMS.get(mod) or []
    lo, hi, best = 0, len(lst) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        if lst[mid][0] <= off: best = lst[mid]; lo = mid + 1
        else: hi = mid - 1
    if best:
        d = off - best[0]
        inside = 'IN' if (best[1] and d < best[1]) else 'next'
        return f'{best[2]}+0x{d:x}({inside})'
    return f'off_0x{off:x}'

libc = ctypes.CDLL('libc.so.6', use_errno=True)
libc.ptrace.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_long
ATTACH, GETREGS, DETACH = 16, 12, 17

def ptrace_rip(tid):
    if libc.ptrace(ATTACH, tid, None, None) < 0: return None, 'attach_fail'
    regs = (ctypes.c_ulong * 27)()
    ok = libc.ptrace(GETREGS, tid, None, ctypes.addressof(regs))
    rip = regs[16] if ok == 0 else None
    libc.ptrace(DETACH, tid, None, None)
    return rip, ('ok' if ok == 0 else 'getregs_fail')

def rd(pid, tid, name):
    try: return Path(f'/proc/{pid}/task/{tid}/{name}').read_text(errors='ignore').strip()
    except Exception: return None

def tasks(pid):
    try: return sorted(int(t) for t in os.listdir(f'/proc/{pid}/task'))
    except Exception: return []

def maps_of(pid):
    try: return Path(f'/proc/{pid}/maps').read_text(errors='ignore')
    except Exception: return ''

def mod_of(maps_text, rip):
    for line in maps_text.splitlines():
        rng = line.split()[0]
        a, b = rng.split('-')
        if int(a, 16) <= rip < int(b, 16):
            path = line[line.find('/'):] if '/' in line else '[anon]'
            key = next((k for k in SYMS if k in path), path.rsplit('/', 1)[-1])
            return key, rip - int(a, 16)
    return None, None

cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik', '--data-root', str(STORE),
       '-o', str(rundir), '--package', dpkg, '--seconds', str(int(SECS)), '--trace']
clog = open(console, 'wb')
t0 = time.time()
proc = subprocess.Popen(cmd, stdout=clog, stderr=subprocess.STDOUT, cwd=str(BASE))

rip_hist = {}       # tid -> {(mod,off): count}
raw_sys = {}        # tid -> last raw syscall strings
kstacks = {}        # tid -> last kernel stack
tid_comm = {}
maps_cache = {}
pg0 = None

def kids(root):
    par = {}
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                st = (p / 'stat').read_text()
                par[int(st[st.rindex(')') + 2:].split()[1])] = par.get(
                    int(st[st.rindex(')') + 2:].split()[1]), []) + [int(p.name)]
            except Exception: pass
    out, st = [], [root]
    while st:
        c = st.pop(); out.append(c); st.extend(par.get(c, []))
    return out

n = 0
while time.time() - t0 < SECS and proc.poll() is None:
    n += 1
    for pid in kids(proc.pid):
        if pid not in maps_cache: maps_cache[pid] = maps_of(pid)
        mt = maps_cache[pid]
        for tid in tasks(pid):
            tid_comm[tid] = rd(pid, tid, 'comm')
            raw = rd(pid, tid, 'syscall')
            if raw: raw_sys.setdefault(tid, []).append(raw.split()[0] + ' ' + ' '.join(raw.split()[1:7]))
            ks = rd(pid, tid, 'stack')
            if ks: kstacks[tid] = ks
            # dense RIP sampling: only interesting tids (spin/blocked short-list)
            comm = tid_comm.get(tid) or ''
            if comm in ('1.raster', '1.io', 'miniandroid') and n % 2 == 0:
                rip, why = ptrace_rip(tid)
                if rip is not None:
                    m, off = mod_of(mt, rip)
                    if m is not None:
                        rip_hist.setdefault(tid, {}).setdefault((m, off), 0)
                        rip_hist[tid][(m, off)] += 1
    time.sleep(0.10)

killed = False
try:
    proc.wait(timeout=SECS + 5)
except Exception:
    killed = True
    try: proc.kill()
    except Exception: pass
    try: proc.wait(timeout=15)
    except Exception: pass
clog.close()
elapsed = time.time() - t0

top = {}
for tid, h in rip_hist.items():
    tot = sum(h.values())
    top[tid] = dict(comm=tid_comm.get(tid), total=tot,
                    best=[dict(mod=m, off=f'0x{o:x}', cnt=c, sym=symbolize(m, o))
                          for (m, o), c in sorted(h.items(), key=lambda kv: -kv[1])[:10]])
res = dict(wave='S188-W9b dense attribution', date='2026-11-07',
           binary_sha16=hashlib.sha256(BIN.read_bytes()).hexdigest()[:16],
           secs=SECS, elapsed=elapsed, killed_by_us=killed, samples=n,
           symbol_tables={k: len(v) for k, v in SYMS.items()},
           maps_pg0_present={pid: any(int(l.split()[0].split('-')[0], 16) == 0
                                      for l in t.splitlines()) for pid, t in maps_cache.items()},
           rip_top=top,
           raw_syscalls={str(t): v[-6:] for t, v in raw_sys.items()},
           kernel_stacks={str(t): kstacks[t].splitlines()[-6:] for t in kstacks})
(OUT / 'W9B_DENSE_ATTRIBUTION.json').write_text(json.dumps(res, indent=1))
print(json.dumps({'elapsed': elapsed, 'killed': killed, 'samples': n}, indent=1))
print('=== RIP top per tid:')
print(json.dumps(top, indent=1)[:4000])
print('=== raw syscalls (last):')
for t, v in res['raw_syscalls'].items():
    print('tid', t, tid_comm.get(t), '->', v[-2:])
print('=== kernel stacks (tail):')
for t, v in res['kernel_stacks'].items():
    print('tid', t, tid_comm.get(t), '->', v)
