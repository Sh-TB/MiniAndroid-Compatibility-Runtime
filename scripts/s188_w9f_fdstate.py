#!/usr/bin/env python3
"""S188-W9f: the decisive fd-state probe.
1. fdinfo of every eventfd (eventfd-count: nonzero = signaled-but-undrained)
   and timerfd (it_value) — no ptrace, no interference.
2. epoll rate census BEFORE and AFTER a single attach/detach of 1.raster
   (tests whether ptrace itself flips the hot loop to quiet).
3. maps-resolved stack return addresses for 1.raster / 1.io -> libflutter
   offsets for offline disassembly.
"""
import ctypes, json, os, re, subprocess, sys, time, struct
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w9'
RUNS = Path('/home/z/my-project/evidence/s188_w2/runs')
SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0
STORE = RUNS / 'store_com.sidhant.queens'
dpkg = [d.name for d in sorted((STORE / 'data' / 'app').iterdir())
        if d.is_dir() and not d.name.startswith('.') and (d / 'base.apk').exists()][0]
rundir = RUNS / 'w9f_fdstate'
console = OUT / 'w9f_queens.console.log'

libc = ctypes.CDLL('libc.so.6', use_errno=True)
libc.ptrace.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_long

def ptrace(cmd, tid, a=None, b=None):
    r = libc.ptrace(cmd, tid, a, b)
    if r < 0:
        raise OSError(ctypes.get_errno(), f'ptrace{cmd}')

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

def rate(pid, tid, secs=0.6):
    states, t0 = [], time.time()
    while time.time() - t0 < secs:
        try:
            s = Path(f'/proc/{pid}/task/{tid}/syscall').read_text(errors='ignore').strip()
            states.append(s.split()[0] if s else '?')
        except Exception:
            break
    return dict(n=len(states), running=sum(1 for s in states if s == 'running'),
                epoll=sum(1 for s in states if s == '232'),
                futex=sum(1 for s in states if s == '202'))

cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik', '--data-root', str(STORE),
       '-o', str(rundir), '--package', dpkg, '--seconds', str(int(SECS)), '--trace']
clog = open(console, 'wb')
proc = subprocess.Popen(cmd, stdout=clog, stderr=subprocess.STDOUT, cwd=str(BASE))
time.sleep(SECS * 0.45)

result = {}
for pid in ptree(proc.pid):
    try:
        tids = {int(t): Path(f'/proc/{pid}/task/{t}/comm').read_text().strip()
                for t in os.listdir(f'/proc/{pid}/task')}
    except Exception:
        continue
    entry = {}

    # 1. fdinfo census
    fds = {}
    try:
        fd_list = sorted(os.listdir(f'/proc/{pid}/fd'), key=lambda x: int(x))
    except Exception:
        fd_list = []
    for f in fd_list:
        tgt = '?'
        try:
            tgt = os.readlink(f'/proc/{pid}/fd/{f}')
        except Exception:
            pass
        d = dict(target=tgt)
        try:
            info = Path(f'/proc/{pid}/fdinfo/{f}').read_text()
            for key in ('eventfd-count', 'timerfd'):
                for line in info.splitlines():
                    if line.startswith(key):
                        d[key] = line
            d['flags'] = next((l for l in info.splitlines() if l.startswith('flags')), '')
        except Exception:
            pass
        if 'eventfd' in tgt or 'timerfd' in tgt or 'eventpoll' in tgt:
            fds[int(f)] = d
    entry['fd_state'] = fds

    # 2. rate before / attach / rate after
    rt = {}
    for tid, c in tids.items():
        if c in ('1.raster', '1.io'):
            rt[c] = dict(before=rate(pid, tid))
            if c == '1.raster':
                try:
                    ptrace(16, tid); time.sleep(0.2); ptrace(17, tid, None, None)
                except OSError as e:
                    rt[c]['attach_err'] = str(e)
            rt[c]['after'] = rate(pid, tid)
    entry['attach_test'] = rt

    # 3. maps-resolved stack walk
    try:
        maps = Path(f'/proc/{pid}/maps').read_text(errors='ignore').splitlines()
    except Exception:
        maps = []
    def resolve(addr):
        for line in maps:
            rng = line.split()[0]
            a, b = rng.split('-')
            if int(a, 16) <= addr < int(b, 16):
                path = line[line.find('/'):] if '/' in line else '[anon]'
                off = int(line.split()[2], 16)
                mod = path.rsplit('/', 1)[-1]
                return f'{mod}@voff_0x{addr - int(a, 16):x}(foff_0x{(addr - int(a, 16)) + off:x})'
        return 'unmapped'
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
                mem.seek(rsp); stk = mem.read(8192)
            rets = [struct.unpack('<Q', stk[i:i + 8])[0]
                    for i in range(0, 8192, 8)
                    if 0x7f0000000000 < struct.unpack('<Q', stk[i:i + 8])[0] < 0x800000000000]
            walk[c] = dict(rsp=hex(rsp),
                           resolved=[(hex(r), resolve(r)) for r in rets[:40]])
        except Exception as e:
            walk[c] = dict(error=str(e))
        finally:
            try:
                ptrace(17, tid, None, None)
            except OSError:
                pass
    entry['stack'] = walk
    result[f'pid{pid}'] = entry

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

(OUT / 'W9F_FDSTATE.json').write_text(json.dumps(result, indent=1))
for k, v in result.items():
    print('==', k)
    for fd, d in sorted(v['fd_state'].items()):
        print(' fd', fd, json.dumps(d)[:220])
    for c, r in v['attach_test'].items():
        print(' attach-test', c, json.dumps(r))
    for c, w in v['stack'].items():
        if 'resolved' in w:
            print(' stack', c)
            for a, r in w['resolved'][:30]:
                print('   ', a, r)
        else:
            print(' stack', c, json.dumps(w)[:200])
