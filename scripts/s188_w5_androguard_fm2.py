#!/usr/bin/env python3
"""S188 W5-1b: androguard — who instantiates FragmentManager (b1/t0) and
who must wire the host (b0/k) into field c. Full-dex invoke scan."""
import sys, json
from pathlib import Path
from loguru import logger; logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = '/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk'
OUT = Path('/home/z/my-project/evidence/s188_w5/w5_androguard_instantiation.json')

FM = 'Lb1/t0;'    # FragmentManager (field c = host Lb0/k;)
HOST = 'Lb0/k;'   # merged class containing FragmentHostCallback

a = APK(APK_PATH)
d = DEX(a.get_dex())
classes = {c.get_name(): c for c in d.get_classes()}

def msig(m):
    return f"{m.get_name()}{m.get_descriptor()}"

# ---- calibration: print raw operand structure of one new-instance ----
calib = None
for c in d.get_classes():
    for m in c.get_methods():
        code = m.get_code()
        if not code: continue
        for ins in code.get_bc().get_instructions():
            if ins.get_name().startswith('new-instance'):
                calib = (c.get_name(), msig(m), ins.get_name(),
                         [(type(o).__name__, str(o)[:60]) for o in ins.get_operands()])
                break
        if calib: break
        # also capture invoke-direct operand shape
        for ins in code.get_bc().get_instructions():
            if ins.get_name().startswith('invoke-direct'):
                calib2 = (ins.get_name(), [(type(o).__name__, str(o)[:80]) for o in ins.get_operands()])
                break
        else:
            continue
        break
    if calib: break

print("CALIB new-instance:", calib)
try:
    print("CALIB invoke-direct:", calib2)
except NameError:
    pass

# ---- robust method-reference extraction from an instruction ----
def instr_ref(ins):
    """Return (ref_string, op) for invoke/new-instance/instance-field ops."""
    op = ins.get_name()
    try:
        ops = ins.get_operands()
    except Exception:
        return op, None
    for o in ops:
        s = str(o)
        if '->' in s and (s.startswith('L') or ';->' in s):
            # operand may be tuple repr like (KIND, 'Lx/y;->m()V')
            part = s
            # strip tuple wrapper
            if part.count('(') and ';->' in part:
                pass
            return op, part
    return op, None

hits = {'invoke_init_fm': [], 'iput_host_field': [], 'get_host_field': []}
for c in d.get_classes():
    for m in c.get_methods():
        code = m.get_code()
        if not code: continue
        try:
            for ins in code.get_bc().get_instructions():
                op, ref = instr_ref(ins)
                if not ref: continue
                site = {'class': c.get_name(), 'method': msig(m), 'op': op}
                if op.startswith('invoke-direct') and f'{FM}-><init>' in ref:
                    hits['invoke_init_fm'].append({**site, 'ref': ref[:120]})
                elif op.startswith('iput-object') and ref.startswith(f'{FM}->c:'):
                    hits['iput_host_field'].append({**site, 'ref': ref[:120]})
                elif op.startswith('sget-object') and ref.startswith(f'{FM}->c:'):
                    hits['get_host_field'].append({**site, 'ref': ref[:120]})
        except Exception as e:
            print('SCAN ERR', c.get_name(), msig(m), type(e).__name__, e)

print(json.dumps({k: v[:40] for k, v in hits.items()}, indent=1))

# ---- dump b1/a1 (FragmentController cand) and La/u (HostCallbacks cand) ----
dump = {}
for cn in ('Lb1/a1;', 'La/u;', 'La/a0;', 'Lo1/d;'):
    if cn in classes:
        c = classes[cn]
        entry = {'super': c.get_superclassname(),
                 'fields': [(f.get_name(), f.get_descriptor()) for f in c.get_fields()],
                 'methods': []}
        for m in c.get_methods():
            entry['methods'].append(msig(m))
        dump[cn] = entry

# BeeperActivity superclass + ctor chain
if 'Ltibarj/tranquilstopwatch/BeeperActivity;' in classes:
    c = classes['Ltibarj/tranquilstopwatch/BeeperActivity;']
    dump['BeeperActivity'] = {'super': c.get_superclassname(),
                              'methods': [msig(m) for m in c.get_methods()]}

sup = dump.get('BeeperActivity', {}).get('super')
seen = []
cur = sup
for _ in range(8):
    if cur in classes and cur not in seen:
        seen.append(cur)
        cur = classes[cur].get_superclassname()
    else:
        break
dump['beeper_super_chain'] = seen
for s in seen:
    if s in classes:
        dump[s] = {'super': classes[s].get_superclassname(),
                   'fields': [(f.get_name(), f.get_descriptor()) for f in classes[s].get_fields()],
                   'methods': [msig(m) for m in classes[s].get_methods()]}

OUT.write_text(json.dumps({'calib_new_instance': calib, 'hits': hits, 'dump': dump}, indent=1, default=str))
print('DUMP keys:', list(dump.keys()))
