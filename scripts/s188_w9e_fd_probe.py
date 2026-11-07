#!/usr/bin/env python3
"""S188-W9e: identify the hot epoll fds (fd 7 raster / fd 10 io) via
/proc/<pid>/fd symlinks + fdinfo, and walk the user stack at epoll depth
to resolve the libflutter call chain. Also measure the epoll wakeup RATE
(rapid /proc/tid/syscall sampling) to prove the hot loop.
"""
import ctypes, json, os, re, subprocess, sys, time, struct, hashlib
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w9'
RUNS = Path('/home/z/my-project/evidence/s188_w2/runs')
SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0
STORE = RUNS / 'store_com.sidhant.queens'
dpkg = [d.name for d in sorted((STORE / 'data' / 'app').iterdir())
        if d.is_dir() and not d.name.startswith('.') and (d / 'base.apk').exists()][0]
rundir = RUNS / 'w9e_fd_probe'
console = OUT / 'w9e_queens.console.log'

libc = ctypes.CDLL('libc.so.6', use_errno=True)
libc.ptrace.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_long

def ptrace(cmd, tid, a=None, b=None):
    r = libc.ptrace(cmd, tid, a, b)
    if r < 0:
        raise OSError(ctypes.get_errno(), f'ptrace{cmd} tid{tid}')

def ptree(root):
    par = {}
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                st = (p / 'stat').read_text()
                par.setdefault(int(st[st.rindex(')') + 2:].split()[1]), []).append(int(p.name))
            except Exception:
                pass
    out, st = [], [root]
    while st:
        c = st.pop(); out.append(c); st.extend(par.get(c, []))
    return out

cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik', '--data-root', str(STORE),
       '-o', str(rundir), '--package', dpkg, '--seconds', str(int(SECS)), '--trace']
clog = open(console, 'wb')
proc = subprocess.Popen(cmd, stdout=clog, stderr=subprocess.STDOUT, cwd=str(BASE))
time.sleep(SECS * 0.5)

result = {}
for pid in ptree(proc.pid):
    try:
        tids = {int(t): Path(f'/proc/{pid}/task/{t}/comm').read_text().strip()
                for t in os.listdir(f'/proc/{pid}/task')}
    except Exception:
        continue
    # ── fd census ──
    fds = {}
    for f in sorted(os.listdir(f'/proc/{pid}/fd'), key=lambda x: int(x)):
        try:
            tgt = os.readlink(f'/proc/{pid}/fd/{f}')
        except Exception as e:
            tgt = f'ERR {e}'
        try:
            info = Path(f'/proc/{pid}/fdinfo/{f}').read_text().splitlines()
            flags = next((l for l in info if l.startswith('flags')), '')
        except Exception:
            flags = ''
        fds[int(f)] = dict(target=tgt, flags=flags.strip())
    # ── epoll wakeup rate per thread ──
    rates = {}
    for tid, c in tids.items():
        if c not in ('1.raster', '1.io', 'dart:io EventHa'):
            continue
        states = []
        t0 = time.time()
        while time.time() - t0 < 1.0:
            try:
                s = Path(f'/proc/{pid}/task/{tid}/syscall').read_text(errors='ignore').strip()
            except Exception:
                break
            states.append(s.split()[0] if s else '?')
        epoll_total = sum(1 for s in states if s == '232')
        running = sum(1 for s in states if s == 'running')
        rates[c] = dict(samples=len(states), epoll_seen=epoll_total,
                        running=running, unique_states=sorted(set(states)))
    # ── stack walk of 1.raster at epoll depth ──
    walk = {}
    for tid, c in tids.items():
        if c not in ('1.raster', '1.io'):
            continue
        try:
            ptrace(16, tid)
        except OSError:
            continue
        time.sleep(0.15)
        try:
            regs = (ctypes.c_ulong * 27)()
            ptrace(12, tid, None, ctypes.addressof(regs))
            rsp = regs[19]
            with open(f'/proc/{pid}/mem', 'rb', 0) as mem:
                mem.seek(rsp)
                stk = mem.read(4096)
            rets = [struct.unpack('<Q', stk[i:i + 8])[0]
                    for i in range(0, 4096, 8)
                    if 0x7f0000000000 < struct.unpack('<Q', stk[i:i + 8])[0] < 0x800000000000]
            walk[c] = dict(rsp=hex(rsp), rets=[hex(r) for r in rets[:60]])
        except Exception as e:
            walk[c] = dict(error=str(e))
        finally:
            try:
                ptrace(17, tid, None, None)
            except OSError:
                pass
    result[f'pid{pid}'] = dict(fds=fds, epoll_rates=rates, stack_walk=walk)

killed = False
try:
    proc.wait(timeout=SECS + 3)
except Exception:
    killed = True
    try:
        proc.kill()
    except Exception:
        pass
    try:
        proc.wait(timeout=10)
    except Exception:
        pass
clog.close()

(OUT / 'W9E_FD_PROBE.json').write_text(json.dumps(result, indent=1))
for k, v in result.items():
    print('==', k)
    for fd, f in sorted(v['fds'].items()):
        print(f'  fd {fd:>3}: {f["target"][:90]} {f["flags"]}')
    for c, r in v['epoll_rates'].items():
        print('  rate', c, json.dumps(r))
    for c, w in v['stack_walk'].items():
        print('  walk', c, json.dumps(w)[:500])
