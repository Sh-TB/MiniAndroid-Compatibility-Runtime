#!/usr/bin/env python3
"""S188-W12 T7: androguard decode of ts ActionBarOverlayLayout.onMeasure
height-split arithmetic (raw DEX = fact source).
"""
import json, zipfile, tempfile
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex
from androguard.core.dex import EncodedMethod

APK = '/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk'
zf = zipfile.ZipFile(APK)
tmpd = tempfile.mkdtemp()
for n in zf.namelist():
    if n.endswith('.dex'):
        zf.extract(n, tmpd)

import glob
targets = ['ActionBarOverlayLayout', 'ContentFrameLayout', 'ActionBarContainer']
out = {}
for dex in sorted(glob.glob(tmpd + '/*.dex')):
    a, d, dx = AnalyzeDex(dex)
    for ma in dx.find_methods(classname='.*androidx/appcompat/widget/(ActionBarOverlayLayout|ContentFrameLayout|ActionBarContainer).*'):
        m = ma.get_method()
        if m.get_name() != 'onMeasure' and m.get_name() != 'onLayout':
            continue
        cls = m.get_class_name()
        key = f"{cls}->{m.get_name()}{m.get_descriptor()}"
        if key in out:
            continue
        code = m.get_code()
        ins = []
        if code:
            for i in code.get_bc().get_instructions():
                ins.append(f'{i.get_name():26s} {i.get_output()}')
        out[key] = {'access': str(m.get_access_flags()), 'n_ins': len(ins), 'code': ins}

json.dump(out, open('/home/z/my-project/evidence/s188_w12/W12_T7_ANDROGUARD_TS_MEASURE.json','w'), indent=1)
print('decoded', len(out), 'methods:')
for k in out: print('  ', k, out[k]['n_ins'], 'ins')
