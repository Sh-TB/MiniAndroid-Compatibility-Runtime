#!/usr/bin/env python3
"""S188-W10 androguard probe (primary DEX oracle): tranquilstopwatch's
Toolbar.onMeasure / CoordinatorLayout.onMeasure bodies — WHY do the parents
answer 0x0 while their children answer real sizes? (the W7 next frontier:
the dimension/draw chain, first_missing_stage=APP_DRAW_OPS).
Evidence -> evidence/s188_w10/W10_ANDROGUARD_TS_MEASURE.json
"""
import json, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/s188_w10'

import zipfile
apk = BASE / 'upload/stuck_apks/com.tibarj.tranquilstopwatch.apk'
if not apk.exists():
    cands = list((BASE / 'upload/stuck_apks').glob('*tranquil*'))
    apk = cands[0]
adir = OUT / 'ts_dex_extract'
adir.mkdir(parents=True, exist_ok=True)
dex_paths = []
with zipfile.ZipFile(apk) as z:
    for n in z.namelist():
        if n.startswith('classes') and n.endswith('.dex'):
            p = adir / Path(n).name
            p.write_bytes(z.read(n))
            dex_paths.append(p)
print('dex files:', [d.name for d in dex_paths])

from androguard.misc import AnalyzeDex

TARGETS = {
    'Landroidx/appcompat/widget/Toolbar;': {'onMeasure', 'onLayout'},
    'Landroidx/coordinatorlayout/widget/CoordinatorLayout;': {'onMeasure'},
    'Landroidx/appcompat/widget/ActionBarOverlayLayout;': {'onMeasure'},
}

results = {'apk': str(apk), 'dex_files': [str(d) for d in dex_paths],
           'methods': {}}
for dp in dex_paths:
    try:
        a, d, dx = AnalyzeDex(str(dp))
    except Exception:
        continue
    for c in dx.find_classes('.*'):
        cm = c.get_vm_class()
        if cm is None or c.name not in TARGETS:
            continue
        for m in cm.get_methods():
            if m.get_name() not in TARGETS[c.name]:
                continue
            if type(m).__name__ != 'EncodedMethod':
                continue
            if m.get_code() is None:
                continue
            key = f'{c.name}.{m.get_name()}{m.get_descriptor()}'
            if key in results['methods']:
                continue
            rows = []
            off = 0
            try:
                for ins in m.get_instructions():
                    rows.append(f'{off:#06x} {ins.get_name()} {ins.get_output()}')
                    off += ins.get_length()
            except Exception as e:
                rows.append(f'<ins-err {e}>')
            results['methods'][key] = {
                'units': len(rows),
                'disasm': rows,
            }
            print(f'== {key} ({len(rows)} units)')

OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'W10_ANDROGUARD_TS_MEASURE.json').write_text(json.dumps(results, indent=1))
print('evidence:', OUT / 'W10_ANDROGUARD_TS_MEASURE.json')
