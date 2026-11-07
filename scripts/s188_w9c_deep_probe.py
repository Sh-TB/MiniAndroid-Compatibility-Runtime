#!/usr/bin/env python3
"""S188-W9c: deep thread probe — attach once per thread, read RIP repeatedly,
read code bytes around RIP and stack memory via /proc/pid/mem, resolve stack
return addresses against maps -> real call-path evidence for the spinning
Flutter threads (1.raster / 1.io) and the blocked platform thread.
"""
import ctypes, json, os, re, subprocess, sys, time, struct, hashlib
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w9'
RUNS = BASE / 'evidence/s188_w2/runs'
SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 16.0
STORE = RUNS / 'store_com.sidhant.queens'
dpkg = [d.name for d in sorted((STORE / 'data' / 'app').iterdir())
        if d.is_dir() and not d.name.startswith('.') and (d / 'base.apk').exists()][0]
rundir = RUNS / 'w9c_deep'
console = OUT / 'w9c_queens.console.log'

libc = ctypes.CDLL('libc.so.6', use_errno=True)
libc.ptrace.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_long
ATTACH, GETREGS, DETACH, CONT = 16, 12, 17, 7

def ptrace(cmd, tid, a=None, b=None):
    r = libc.ptrace(cmd, tid, a, b)
    if r < 0:
        e = ctypes.get_errno()
        raise OSError(e, f'ptrace {cmd} tid {tid}')
    return r

def pidof_tree(root):
    par = {}
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                st = (p / 'stat').read_text()
                pp = int(st[st.rindex(')') + 2:].split()[1])
                par.setdefault(pp, []).append(int(p.name))
            except Exception:
                pass
    out, st = [], [root]
    while st:
        c = st.pop(); out.append(c); st.extend(par.get(c, []))
    return out

def comm_of(pid, tid):
    try:
        return Path(f'/proc/{pid}/task/{tid}/comm').read_text(errors='ignore').strip()
    except Exception:
        return '?'

def maps_of(pid):
    try:
        return Path(f'/proc/{pid}/maps').read_text(errors='ignore')
    except Exception:
        return ''

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

cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik', '--data-root', str(STORE),
       '-o', str(rundir), '--package', dpkg, '--seconds', str(int(SECS)), '--trace']
clog = open(console, 'wb')
proc = subprocess.Popen(cmd, stdout=clog, stderr=subprocess.STDOUT, cwd=str(BASE))
time.sleep(SECS * 0.55)   # let the VM init reach the stable stall

results = {}
for pid in pidof_tree(proc.pid):
    mt = maps_of(pid)
    if not mt:
        continue
    regs_by_mod = {}   # module path hint
    for tid in sorted(int(t) for t in os.listdir(f'/proc/{pid}/task')):
        comm = comm_of(pid, tid)
        try:
            ptrace(ATTACH, tid)
        except OSError as e:
            results[f'{pid}:{tid}:{comm}'] = dict(error=f'attach {e}')
            continue
        time.sleep(0.25)
        entry = dict(comm=comm, rips=[], code_bytes=[], stack_ret=[])
        try:
            regs = (ctypes.c_ulong * 27)()
            for _ in range(6):
                ptrace(GETREGS, tid, None, ctypes.addressof(regs))
                entry['rips'].append(hex(regs[16]))
                entry['rsp_hex'] = hex(regs[19])
                time.sleep(0.02)
            rip, rsp = regs[16], regs[19]
            with open(f'/proc/{pid}/mem', 'rb', 0) as mem:
                def rdmem(addr, ln):
                    mem.seek(addr)
                    return mem.read(ln)
                try:
                    entry['code_bytes'] = rdmem(rip - 16, 48).hex()
                except Exception as e:
                    entry['code_bytes'] = f'memfail {e}'
                try:
                    stk = rdmem(rsp, 640)
                    for i in range(0, 640, 8):
                        v = struct.unpack('<Q', stk[i:i + 8])[0]
                        if 0x410000 < v < 0x7f0000000000:
                            entry['stack_ret'].append(hex(v))
                except Exception as e:
                    entry['stack_ret'] = [f'memfail {e}']
        finally:
            try:
                ptrace(DETACH, tid, None, None)
            except OSError:
                pass
        # resolve rips + stack rets against maps
        def resolve(addr):
            for line in mt.splitlines():
                rng = line.split()[0]
                a, b = rng.split('-')
                if int(a, 16) <= addr < int(b, 16):
                    path = line[line.find('/'):] if '/' in line else '[anon]'
                    return path.rsplit('/', 1)[-1], addr - int(a, 16)
            return None, None
        mods = {}
        for pathhint, syms in [('libflutter.so', load_symbols(STORE / f'data/app/{dpkg}/lib/x86_64/libflutter.so')),
                               ('libapp.so', load_symbols(STORE / f'data/app/{dpkg}/lib/x86_64/libapp.so')),
                               ('libc.so.6', load_symbols('/lib/x86_64-linux-gnu/libc.so.6')),
                               ('miniandroid', load_symbols(BIN))]:
            mods[pathhint] = syms
        def symbolize(mod, off):
            lst = mods.get(mod) or []
            lo, hi, best = 0, len(lst) - 1, None
            while lo <= hi:
                mid = (lo + hi) // 2
                if lst[mid][0] <= off: best = lst[mid]; lo = mid + 1
                else: hi = mid - 1
            if best:
                d = off - best[0]
                return f'{best[2]}+0x{d:x}' + ('IN' if best[1] and d < best[1] else '')
            return f'off_0x{off:x}'
        entry['rip_resolved'] = []
        for r in set(entry['rips']):
            m, o = resolve(int(r, 16))
            if m: entry['rip_resolved'].append(f'{m}@0x{o:x} {symbolize(m, o)}')
        entry['stack_resolved'] = []
        for r in entry['stack_ret'][:40]:
            m, o = resolve(int(r, 16))
            if m: entry['stack_resolved'].append(f'{m}@0x{o:x} {symbolize(m, o)}')
        results[f'{pid}:{tid}'] = entry

killed = False
try:
    proc.wait(timeout=SECS + 3)
except Exception:
    killed = True
    try: proc.kill()
    except Exception: pass
    try: proc.wait(timeout=10)
    except Exception: pass
clog.close()

(OUT / 'W9C_DEEP_PROBE.json').write_text(json.dumps(results, indent=1))
for k, v in results.items():
    print(k, json.dumps({kk: vv for kk, vv in v.items() if kk != 'stack_ret'})[:1200])
    print()
