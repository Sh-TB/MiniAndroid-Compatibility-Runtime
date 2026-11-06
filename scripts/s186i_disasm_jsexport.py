#!/usr/bin/env python3
"""S186i: disassemble Lcom/getcapacitor/JSExport; — the getPluginJS NPE site
(blichess #49 / blidraughts #74, 1 uncaught each). Probe-first: exact bytecode
of the method bodies + which fields/methods they touch."""
import zipfile, tempfile, os, io, sys
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex

APK = sys.argv[1] if len(sys.argv) > 1 else 'upload/stuck_apks/com.vovagorodok.blichess.apk'
WANT_CLASS = 'Lcom/getcapacitor/JSExport;'

out = io.StringIO()
with zipfile.ZipFile(APK) as z:
    dexes = [n for n in z.namelist() if n.endswith('.dex')]
for name in dexes:
    with zipfile.ZipFile(APK) as z:
        tmp = tempfile.NamedTemporaryFile(suffix='.dex', delete=False)
        tmp.write(z.read(name)); tmp.close()
    try:
        a, d, dx = AnalyzeDex(tmp.name)
    except Exception:
        os.unlink(tmp.name); continue
    for m in d.get_classes():
        if m.get_name() != WANT_CLASS:
            continue
        print('=== CLASS', m.get_name())
        for f in m.get_fields():
            print('  FIELD', f.get_name(), f.get_descriptor())
        for meth in m.get_methods():
            print('--- METHOD', meth.get_name(), meth.get_descriptor())
            code = meth.get_code()
            if not code:
                print('   <abstract/native>')
                continue
            bc = meth.get_instructions()
            idx = 0
            for ins in bc:
                print(f'   {idx:#06x}: {ins.get_name():28s} {ins.get_output()}')
                idx += ins.get_length()
    os.unlink(tmp.name)
