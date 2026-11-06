#!/usr/bin/env python3
"""S186e: disassemble the gnubg datastore extension-check delegate to see the
exact check the engine must satisfy (probe-first law)."""
import zipfile, tempfile, os, sys
from androguard.misc import AnalyzeDex

apk = 'upload/stuck_apks/com.clavierhaus.gnubg.apk'
target = sys.argv[1] if len(sys.argv) > 1 else 'PreferenceDataStoreFactory'


def _walk(m):
    off = 0
    out = []
    for ins in m.get_instructions():
        out.append((off, ins))
        off += ins.get_length()
    return out


with zipfile.ZipFile(apk) as z:
    dexes = [n for n in z.namelist() if n.endswith('.dex')]
for name in dexes:
    with zipfile.ZipFile(apk) as z:
        tmp = tempfile.NamedTemporaryFile(suffix='.dex', delete=False)
        tmp.write(z.read(name)); tmp.close()
    try:
        _, d, _ = AnalyzeDex(tmp.name)
    except Exception:
        os.unlink(tmp.name); continue
    for c in d.get_classes():
        cn = c.get_name()
        if target in cn:
            print('==', name, cn)
            for m in c.get_methods():
                print('  method:', m.get_name(), m.get_descriptor())
                try:
                    code = m.get_code()
                except Exception:
                    code = None
                if code is None:
                    continue
                bc = m.get_instructions()
                for off, ins in _walk(m):
                    print(f'    {off:04x}: {ins.get_name():22s} {ins.get_output()}')
    os.unlink(tmp.name)


