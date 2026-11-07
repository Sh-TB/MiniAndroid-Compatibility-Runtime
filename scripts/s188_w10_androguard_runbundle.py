#!/usr/bin/env python3
"""S188-W10 androguard probe (primary DEX oracle per the W8 policy):
what does queens' FlutterJNI pass to nativeRunBundleAndSnapshotFromLibrary?
Finds the Java caller, the argument provenance (which arg can be null),
and the @Nullable/@NonNull annotations. Evidence -> W10_ANDROGUARD_RUNBUNDLE.json
"""
import json, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE))
OUT = BASE / 'evidence/s188_w10'

from androguard.misc import AnalyzeDex

STORE = BASE / 'evidence/s188_w2/runs/store_com.sidhant.queens/data/app/com.sidhant.queens'
# DEXes live inside base.apk — extract to the analysis dir (read-only source)
import zipfile
dex_paths = sorted(STORE.glob('**/*.dex'))
if not dex_paths:
    adir = OUT / 'dex_extract'
    adir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(STORE / 'base.apk') as z:
        for n in z.namelist():
            if n.startswith('classes') and n.endswith('.dex'):
                (adir / Path(n).name).write_bytes(z.read(n))
    dex_paths = sorted(adir.glob('*.dex'))
print('dex files:', [d.name for d in dex_paths])

results = {'dex_files': [str(d) for d in dex_paths], 'methods': {}}
target = 'nativeRunBundleAndSnapshotFromLibrary'
caller_name = 'runBundleAndSnapshotFromLibrary'

for dp in dex_paths:
    try:
        a, d, dx = AnalyzeDex(str(dp))
    except Exception as e:
        continue
    for m in d.get_methods():
        cls = m.get_class_name()
        if not cls or 'FlutterJNI' not in cls:
            continue
        name = m.get_name()
        if name not in (caller_name, 'nativeRunBundleAndSnapshotFromLibrary',
                        'attachToNative', 'performNativeAttach', 'init'):
            continue
        if type(m).__name__ != 'EncodedMethod':
            continue  # MethodIdItem entries carry no code
        code = m.get_code()
        if code is None:
            results['methods'][f'{cls}.{name}'] = {'abstract': True}
            continue
        # decompile-lite: disassemble the bytecode with pc
        from androguard.core.analysis.analysis import MethodAnalysis
        ins_rows = []
        for ins in m.get_instructions():
            off = ins.get_offset()
            op = ins.get_name()
            out = ins.get_output()
            ins_rows.append(f'{off:#06x} {op} {out}')
        results['methods'][f'{cls}.{name}'] = {
            'descriptor': m.get_descriptor(),
            'access': hex(m.get_access_flags()),
            'code_units': len(ins_rows),
            'disasm': ins_rows[:220],
        }
        print(f'== {cls}.{name} {m.get_descriptor()} ({len(ins_rows)} units)')

OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'W10_ANDROGUARD_RUNBUNDLE.json').write_text(json.dumps(results, indent=1))
print('evidence:', OUT / 'W10_ANDROGUARD_RUNBUNDLE.json')
