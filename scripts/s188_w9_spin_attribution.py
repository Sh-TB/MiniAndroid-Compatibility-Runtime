#!/usr/bin/env python3
"""S188-W9: queens Dart VM init spin attribution.

Directive: attribute the two spinning threads and their call paths; trace
parent and guarded child separately; verify whether the fork-probe/sigsuspend
behavior interferes; capture the last successful init milestone and the first
operation that fails to advance.

Method (no gdb/perf/strace in this container):
  1. /proc sampling: per-tid utime/stime deltas -> spinners; wchan; syscall
     (futex args incl. uaddr -> which lock); comm (Dart thread names).
  2. ptrace RIP sampling (PTRACE_ATTACH/GETREGS/DETACH via ctypes) for the
     top spinners -> RIP histogram symbolized against libflutter.so dynsym /
     miniandroid symtab / libc dynsym via /proc/<pid>/maps.
  3. Descendant census: main process vs fork-probe child vs guarded child
     (PPid chains), parent wchan (sigsuspend check).
  4. Console milestone parse: last successful init step + first non-advance.
"""
import ctypes, json, os, re, signal, struct, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w9'
RUNS = BASE / 'evidence/s188_w2/runs'
SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
SAMPLE_EVERY = 0.12
PTRACE_EVERY_N = 25

OUT.mkdir(parents=True, exist_ok=True)
STORE = RUNS / 'store_com.sidhant.queens'
apps = STORE / 'data' / 'app'
dpkg = [d.name for d in sorted(apps.iterdir())
        if d.is_dir() and not d.name.startswith('.')
        and (d / 'base.apk').exists()][0]
rundir = RUNS / 'w9_spin_attr'
console = OUT / 'w9_queens.console.log'

# ── symbol tables for RIP symbolization ────────────────────────────────
def load_symbols(path):
    syms = []
    try:
        txt = subprocess.run(['readelf', '-sW', str(path)], capture_output=True,
                             text=True, timeout=60).stdout
        for line in txt.splitlines():
            m = re.match(r'\s*\d+:\s+([0-9a-f]+)\s+(\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)', line)
            if m:
                addr, size, name = int(m.group(1), 16), int(m.group(2)), m.group(3)
                if addr and name not in ('', '*UND*'):
                    syms.append((addr, size, name))
    except Exception:
        pass
    syms.sort()
    return syms

FL = STORE / f'data/app/{dpkg}/lib/x86_64/libflutter.so'
SYMS = {'libflutter.so': load_symbols(FL),
        'miniandroid': load_symbols(BIN),
        'libc.so.6': load_symbols('/lib/x86_64-linux-gnu/libc.so.6')}

def symbolize(module, off):
    lst = SYMS.get(module) or []
    lo, hi = 0, len(lst) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if lst[mid][0] <= off:
            best = lst[mid]; lo = mid + 1
        else:
            hi = mid - 1
    if best:
        d = off - best[0]
        inside = 'IN' if (best[1] and d < best[1]) else 'near'
        return f'{best[2]}+0x{d:x} ({inside})'
    return f'off_0x{off:x}'

# ── ptrace via ctypes ──────────────────────────────────────────────────
libc = ctypes.CDLL('libc.so.6', use_errno=True)
PTRACE_ATTACH, PTRACE_GETREGS, PTRACE_DETACH = 16, 12, 17
libc.ptrace.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_long

def ptrace_rip(tid):
    if libc.ptrace(PTRACE_ATTACH, tid, None, None) < 0:
        return None
    regs = (ctypes.c_ulong * 27)()
    ok = libc.ptrace(PTRACE_GETREGS, tid, None, ctypes.addressof(regs))
    rip = regs[16] if ok == 0 else None
    libc.ptrace(PTRACE_DETACH, tid, None, None)
    return rip  # raw rip; maps give module base

# ── /proc helpers ──────────────────────────────────────────────────────
def readproc(pid, tid, name):
    try:
        return (Path(f'/proc/{pid}/task/{tid}/{name}').read_text(errors='ignore')).strip()
    except Exception:
        return None

def task_list(pid):
    try:
        return sorted(int(t) for t in os.listdir(f'/proc/{pid}/task'))
    except Exception:
        return []

def descendants(root):
    kids = {}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():
            continue
        try:
            st = (p / 'stat').read_text()
            rparen = st.rindex(')')
            fields = st[rparen + 2:].split()
            ppid = int(fields[1])
            kids.setdefault(ppid, []).append(int(p.name))
        except Exception:
            pass
    out, stack = [], [root]
    while stack:
        cur = stack.pop()
        out.append(cur)
        stack.extend(kids.get(cur, []))
    return out

def parse_syscall(txt):
    if not txt or txt == 'running':
        return txt
    parts = txt.split()
    if parts[0] == '202':  # futex
        op = int(parts[1], 16) & 0x7f
        ops = {0: 'WAIT', 1: 'WAKE', 9: 'WAIT_BITSET', 128: 'REQUEUE_PI'}
        return f'futex:{ops.get(op, op)}:uaddr_0x{int(parts[2], 16):x}'
    names = {0: 'read', 1: 'write', 7: 'poll', 35: 'nanosleep', 230: 'clock_nanosleep',
             232: 'epoll_wait', 271: 'pselect6', 30: 'shutdown', 33: 'select'}
    return f'sys{parts[0]}({names.get(int(parts[0]), "?")})'

# ── launch ─────────────────────────────────────────────────────────────
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(STORE), '-o', str(rundir),
       '--package', dpkg, '--seconds', str(int(SECS)), '--trace']
clog = open(console, 'wb')
t0 = time.time()
proc = subprocess.Popen(cmd, stdout=clog, stderr=subprocess.STDOUT, cwd=str(BASE))

samples = []          # per sample: {pid: {tid: {...}}}
rip_hist = {}         # (module, off) -> count per tid
ptrace_fail = 0
ptrace_ok = 0
n = 0
cpu_prev = {}

while time.time() - t0 < SECS and proc.poll() is None:
    n += 1
    snap = {}
    for pid in descendants(proc.pid):
        for tid in task_list(pid):
            stat = readproc(pid, tid, 'stat')
            if not stat:
                continue
            try:
                rp = stat.rindex(')')
                f = stat[rp + 2:].split()
                utime, stime = int(f[11]), int(f[12])
                state = f[0]
            except Exception:
                continue
            wchan = readproc(pid, tid, 'wchan')
            sc = parse_syscall(readproc(pid, tid, 'syscall'))
            comm = readproc(pid, tid, 'comm')
            key = (pid, tid)
            prev = cpu_prev.get(key, (utime, stime))
            cpu_prev[key] = (utime, stime)
            snap[(pid, tid)] = dict(comm=comm, state=state,
                                    cpu_d=utime - prev[0] + stime - prev[1],
                                    wchan=wchan, sys=sc)
    samples.append({f'{p}:{t}': v for (p, t), v in snap.items()})

    # ptrace RIP sampling on top spinners of the deepest descendant
    if n % PTRACE_EVERY_N == 0 and snap:
        deep = max(set(p for (p, t) in snap.keys() if p != proc.pid), default=None)
        target_pid = deep if deep is not None else proc.pid
        tids = [t for (p, t) in snap.keys() if p == target_pid and snap[(p, t)]['cpu_d'] > 0]
        if not tids:
            tids = [t for (p, t) in snap.keys() if p == target_pid]
        for tid in tids[:3]:
            try:
                maps = Path(f'/proc/{target_pid}/maps').read_text(errors='ignore')
            except Exception:
                break
            rip = ptrace_rip(tid)
            if rip is None:
                ptrace_fail += 1
                continue
            ptrace_ok += 1
            mod, off = None, None
            for line in maps.splitlines():
                rng = line.split()[0]
                path = line[line.find('/'):] if '/' in line else ''
                a, b = rng.split('-')
                if int(a, 16) <= rip < int(b, 16):
                    base = int(a, 16)
                    key = next((k for k in SYMS if k in path), path.rsplit('/', 1)[-1])
                    mod, off = key, rip - base
                    break
            if mod is not None:
                k2 = (tid, mod, off)
                rip_hist[k2] = rip_hist.get(k2, 0) + 1
    time.sleep(SAMPLE_EVERY)

killed_by_us = False
try:
    proc.wait(timeout=SECS + 5)
except subprocess.TimeoutExpired:
    killed_by_us = True          # the W8 'timeout kill honest' signature:
    try:                         # parent sigsuspend-forever, never exits
        proc.kill()
    except Exception:
        pass
    try:
        proc.wait(timeout=20)
    except Exception:
        pass
clog.close()
elapsed = time.time() - t0

# ── analyze ────────────────────────────────────────────────────────────
per_tid_cpu = {}
per_tid_sys = {}
per_tid_comm = {}
per_tid_wchan = {}
for s in samples:
    for k, v in s.items():
        per_tid_cpu[k] = per_tid_cpu.get(k, 0) + v['cpu_d']
        per_tid_sys.setdefault(k, {})
        per_tid_sys[k][v['sys']] = per_tid_sys[k].get(v['sys'], 0) + 1
        per_tid_comm[k] = v['comm']
        per_tid_wchan[k] = v['wchan']

spinners = sorted(per_tid_cpu.items(), key=lambda kv: -kv[1])[:12]
spin_detail = []
for k, cpu in spinners:
    pid, tid = k.split(':')
    top_sys = sorted(per_tid_sys[k].items(), key=lambda kv: -kv[1])[:3]
    entry = dict(proc=pid, tid=tid, comm=per_tid_comm.get(k), cpu_ticks=cpu,
                 top_syscalls=top_sys, wchan_last=per_tid_wchan.get(k))
    rips = [(off, cnt) for (t2, mod, off), cnt in rip_hist.items()
            if t2 == int(tid) and mod in ('libflutter.so', 'miniandroid')]
    symd = {}
    for off, cnt in sorted(rips, key=lambda x: -x[1])[:8]:
        sym = symbolize('libflutter.so' if any(off == o and m == 'libflutter.so'
                       for (t3, m, o), c3 in rip_hist.items() if t3 == int(tid))
                       else 'miniandroid', off)
        symd[f'0x{off:x}'] = dict(count=cnt, sym=sym)
    if symd:
        entry['rip_hist'] = symd
    spin_detail.append(entry)

log = console.read_text(errors='ignore')
milestones = {}
for pat, tag in [
        (r'dlopen.*libflutter[^\n]*', 'flutter_dlopen'),
        (r'JNI_OnLoad[^\n]*', 'jni_onload'),
        (r'RegisterNatives[^\n]*', 'register_natives'),
        (r'\[PTHREAD-SHADOW\][^\n]*', 'pthread_shadow'),
        (r'\[BIONIC-ABORT\][^\n]*', 'bionic_abort'),
        (r'pthread error[^\n]*', 'pthread_error'),
        (r'VM snapshot[^\n]*', 'vm_snapshot'),
        (r'Check failed[^\n]*', 'check_failed'),
        (r'UNSUPPORTED (JNIEnv|JavaVM) slot \d+[^\n]*', 'unsupported_slots'),
        (r'UNSUPPORTED slot census:[^\n]*', 'slot_census'),
        (r'\[ROUTE\][^\n]*', 'route_decision'),
        (r'libapp\.so[^\n]*', 'libapp')]:
    ms = re.findall(pat, log)
    if ms:
        milestones[tag] = ms[:6] if tag not in ('pthread_shadow', 'unsupported_slots') else ms[:14]

res = dict(
    wave='S188-W9 spin attribution', date='2026-11-07',
    binary_sha16=None, pkg='com.sidhant.queens', secs_run=SECS, elapsed=elapsed,
    killed_by_us=killed_by_us, exit_code=proc.returncode,
    samples=n, ptrace_ok=ptrace_ok, ptrace_fail=ptrace_fail,
    symbol_tables={k: len(v) for k, v in SYMS.items()},
    spinners=spin_detail,
    thread_census={k: dict(comm=per_tid_comm[k], sys_hist=per_tid_sys[k])
                   for k in per_tid_comm},
    milestones=milestones,
)
import hashlib
res['binary_sha16'] = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
(OUT / 'W9_SPIN_ATTRIBUTION.json').write_text(json.dumps(res, indent=1))
print(json.dumps({k: res[k] for k in
                  ('elapsed', 'exit_code', 'samples', 'ptrace_ok', 'ptrace_fail')}, indent=1))
print('--- spinners (top):')
for e in spin_detail[:8]:
    print(json.dumps(e)[:400])
print('--- milestones keys:', list(milestones.keys()))
