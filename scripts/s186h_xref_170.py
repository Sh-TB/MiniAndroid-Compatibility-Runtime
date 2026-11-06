#!/usr/bin/env python3
"""S186h: who constructs the (renamed) FragmentManager and who calls the FCV
internal ctor — cross-reference analysis for tranquilstopwatch #170."""
import zipfile, tempfile, os, io
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex

APK = 'upload/stuck_apks/tibarj.tranquilstopwatch.apk'
FM = 'Lb1/t0;'          # renamed FragmentManager
FCV = 'Landroidx/fragment/app/FragmentContainerView;'

results = []
with zipfile.ZipFile(APK) as z:
    dexes = [n for n in z.namelist() if n.endswith('.dex')]
for name in dexes:
    with zipfile.ZipFile(APK) as z:
        tmp = tempfile.NamedTemporaryFile(suffix='.dex', delete=False)
        tmp.write(z.read(name)); tmp.close()
    try:
        _, d, _ = AnalyzeDex(tmp.name)
    except Exception:
        os.unlink(tmp.name); continue
    for c in d.get_classes():
        for m in c.get_methods():
            try:
                for ins in m.get_instructions():
                    out = ins.get_output()
                    if (f'->{FM}-><init>' in out and ins.get_name().startswith('invoke')) or \
                       (f'->{FCV}-><init>' in out and ins.get_name().startswith('invoke')):
                        results.append(f"{c.get_name()}->{m.get_name()} {m.get_descriptor()[:80]} : {ins.get_name()} {out[:120]}")
            except Exception:
                pass
    os.unlink(tmp.name)

print(f"{len(results)} xrefs")
for r in results[:25]:
    print(r)
