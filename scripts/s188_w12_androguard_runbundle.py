#!/usr/bin/env python3
"""S188-W12 T2: androguard decode of queens FlutterJNI.runBundleAndSnapshotFromLibrary
and nativeRunBundleAndSnapshotFromLibrary call-site (raw DEX = fact source).
"""
import json
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex

DEX = '/home/z/my-project/evidence/s188_w2/runs/store_com.sidhant.queens/data/app/com.sidhant.queens/base.apk'
# extract dex from apk first
import zipfile
zf = zipfile.ZipFile(DEX)
dexname = [n for n in zf.namelist() if n.endswith('.dex')]
tmp = '/tmp/queens_classes.dex'
zf.extract(dexname[0], '/tmp/queens_dex')
import os
src = f'/tmp/queens_dex/{dexname[0]}'
a, d, dx = AnalyzeDex(src)

out = {'classes': []}
targets = {}
from androguard.core.dex import EncodedMethod
all_methods = list(d.get_methods())
all_methods = [m for m in all_methods if isinstance(m, EncodedMethod)]
for m in all_methods:
    cls = m.get_class_name()
    if 'FlutterJNI' in cls and 'RunBundle' in m.get_name():
        targets[f'{cls}->{m.get_name()}{m.get_descriptor()}'] = m

for sig, m in sorted(targets.items()):
    entry = {'sig': sig, 'access': m.get_access_flags_string(), 'code': []}
    code = m.get_code()
    if code:
        for ins in code.get_bc().get_instructions():
            entry['code'].append(f'{ins.get_name():30s} {ins.get_output()}')
    out['classes'].append(entry)

# also find callers of nativeRunBundleAndSnapshotFromLibrary
callers = []
for m in all_methods:
    c = m.get_code()
    if not c: continue
    for ins in c.get_bc().get_instructions():
        o = ins.get_output()
        if 'nativeRunBundleAndSnapshotFromLibrary' in o:
            callers.append(f'{m.get_class_name()}->{m.get_name()}{m.get_descriptor()}')
out['callers'] = sorted(set(callers))

with open('/home/z/my-project/evidence/s188_w12/W12_T2_ANDROGUARD_RUNBUNDLE.json', 'w') as f:
    json.dump(out, f, indent=1)
print('methods found:', len(out['classes']))
for e in out['classes']:
    print('==', e['sig'], e['access'])
    for line in e['code'][:45]:
        print('   ', line)
    if len(e['code']) > 45: print('   ...', len(e['code']), 'instructions total')
print('callers:', out['callers'])
