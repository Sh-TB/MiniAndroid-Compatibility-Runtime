#!/usr/bin/env python3
"""S188 W5-1c: who writes FragmentManager host field (b1/t0.c) — substring scan."""
import json
from pathlib import Path
from loguru import logger; logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = '/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk'
OUT = Path('/home/z/my-project/evidence/s188_w5/w5_androguard_host_wire.json')
FM, HOSTF = 'Lb1/t0;', 'Lb1/t0;->c:'

a = APK(APK_PATH)
d = DEX(a.get_dex())
classes = {c.get_name(): c for c in d.get_classes()}

def msig(m): return f"{m.get_name()}{m.get_descriptor()}"

hits = {'iput_c': [], 'iget_c': [], 'invoke_attachlike': []}
for c in d.get_classes():
    for m in c.get_methods():
        code = m.get_code()
        if not code: continue
        try:
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                if not (op.startswith('iput') or op.startswith('iget') or op.startswith('invoke')):
                    continue
                ref = None
                for o in ins.get_operands():
                    s = str(o)
                    if ';->' in s:
                        ref = s
                        break
                if not ref: continue
                site = {'class': c.get_name(), 'method': msig(m), 'op': op, 'ref': ref[:140]}
                if op.startswith('iput-object') and HOSTF in ref:
                    hits['iput_c'].append(site)
                elif op.startswith('iget-object') and HOSTF in ref:
                    hits['iget_c'].append(site)
                elif op.startswith('invoke-virtual') and f'{FM}->' in ref and op in ref.replace(ref.split(FM)[0], '', 1):
                    pass
        except Exception as e:
            print('ERR', type(e).__name__)

# methods on b1/t0 that READ c (candidates for attachController / isStateSaved etc.)
fm_readers = []
if FM[:-1] + ';' in {k[:-1] + ';' for k in [FM]}:
    pass
fmc = classes.get(FM)
if fmc:
    for m in fmc.get_methods():
        code = m.get_code()
        if not code: continue
        reads = writes = 0
        try:
            for ins in code.get_bc().get_instructions():
                if ins.get_name().startswith(('iget-object', 'iput-object')):
                    for o in ins.get_operands():
                        if HOSTF in str(o):
                            if ins.get_name().startswith('iput'):
                                writes += 1
                            else:
                                reads += 1
        except Exception:
            pass
        if writes:
            fm_readers.append({'method': msig(m), 'writes_c': writes, 'reads_c': reads})

# dump FragmentController candidate Lb1/a1; fully
def dump_class(cn):
    c = classes.get(cn)
    if not c: return None
    return {'super': c.get_superclassname(),
            'fields': [(f.get_name(), f.get_descriptor()) for f in c.get_fields()],
            'methods': [msig(m) for m in c.get_methods()]}

print(json.dumps({'iput_c': hits['iput_c'],
                  'iput_c_count': len(hits['iput_c']),
                  'iget_c_count': len(hits['iget_c']),
                  'fm_writers_of_c': fm_readers,
                  'Lb1/a1': dump_class('Lb1/a1;'),
                  'Lb1/a0': dump_class('Lb1/a0;'),
                  'Lg/l': dump_class('Lg/l;')}, indent=1))
OUT.write_text(json.dumps({'hits': hits, 'fm_writers_of_c': fm_readers,
                           'Lb1/a1': dump_class('Lb1/a1;'), 'Lb1/a0': dump_class('Lb1/a0;'),
                           'Lg/l': dump_class('Lg/l;')}, indent=1))
