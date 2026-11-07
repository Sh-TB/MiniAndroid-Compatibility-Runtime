#!/usr/bin/env python3
"""S188-W9d: capture the failing syscall for each parked thread.
While ptrace-stopped, /proc/<pid>/task/<tid>/syscall is authoritative
(nr + args). Also read orig_rax (regs[15]) and the arg registers, and sample
the thread repeatedly (attach/detach cycles) to see the syscall MIX of the
spinning threads over time.
"""
import ctypes, json, os, re, subprocess, sys, time, hashlib
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w9'
RUNS = Path('/home/z/my-project/evidence/s188_w2/runs')
SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 14.0
STORE = RUNS / 'store_com.sidhant.queens'
dpkg = [d.name for d in sorted((STORE / 'data' / 'app').iterdir())
        if d.is_dir() and not d.name.startswith('.') and (d / 'base.apk').exists()][0]
rundir = RUNS / 'w9d_syscall_probe'
console = OUT / 'w9d_queens.console.log'

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

def comm(pid, tid):
    try:
        return Path(f'/proc/{pid}/task/{tid}/comm').read_text(errors='ignore').strip()
    except Exception:
        return '?'

def procsyscall(pid, tid):
    try:
        return Path(f'/proc/{pid}/task/{tid}/syscall').read_text(errors='ignore').strip()
    except Exception:
        return '?'

cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik', '--data-root', str(STORE),
       '-o', str(rundir), '--package', dpkg, '--seconds', str(int(SECS)), '--trace']
clog = open(console, 'wb')
proc = subprocess.Popen(cmd, stdout=clog, stderr=subprocess.STDOUT, cwd=str(BASE))
time.sleep(SECS * 0.5)

result = {}
for pid in ptree(proc.pid):
    try:
        tids = sorted(int(t) for t in os.listdir(f'/proc/{pid}/task'))
    except Exception:
        continue
    for tid in tids:
        c = comm(pid, tid)
        # attach/detach cycles: catch the syscall mix over time
        seen = {}
        regs_last = None
        for cyc in range(8):
            try:
                ptrace(16, tid)               # ATTACH
            except OSError:
                break
            time.sleep(0.02)
            try:
                sc = procsyscall(pid, tid)
                regs = (ctypes.c_ulong * 27)()
                try:
                    ptrace(12, tid, None, ctypes.addressof(regs))  # GETREGS
                    regs_last = dict(orig_rax=regs[15], rax=regs[10], rdi=hex(regs[14]),
                                     rsi=hex(regs[13]), rdx=hex(regs[12]), r10=hex(regs[7]),
                                     r8=hex(regs[9]), rip=hex(regs[16]), rsp=hex(regs[19]))
                except OSError:
                    pass
                key = sc.split()[0] if sc and sc != '?' else sc
                seen.setdefault(key, []).append(sc)
            finally:
                try:
                    ptrace(17, tid, None, None)   # DETACH
                except OSError:
                    pass
            time.sleep(0.03)
        result[f'{tid}:{c}'] = dict(syscall_mix={k: v[:2] for k, v in seen.items()},
                                    regs_last=regs_last)

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

(OUT / 'W9D_SYSCALL_MIX.json').write_text(json.dumps(result, indent=1))
for k, v in result.items():
    print(k, json.dumps(v)[:700])
