#!/usr/bin/env python3
"""S186h: exact bytecode of Lb1/t0;.A (the pc=2 NPE site) + all callers of b0/k
and the FCV internal ctor body. Focused, no noise."""
import zipfile, tempfile, os, io
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex

APK = 'upload/stuck_apks/tibarj.tranquilstopwatch.apk'
WANT = {('Lb1/t0;', 'A'), ('Lb0/k;', '<init>'),
        ('Landroidx/fragment/app/FragmentContainerView;', '<init>')}

buf = io.StringIO()
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
        cn = c.get_name()
        for m in c.get_methods():
            if (cn, m.get_name()) in WANT:
                buf.write(f"\n=== {cn};->{m.get_name()} {m.get_descriptor()}\n")
                off = 0
                for ins in m.get_instructions():
                    buf.write(f"  {off:5d} {ins.get_name():26s} {ins.get_output()}\n")
                    off += ins.get_length()
    os.unlink(tmp.name)

txt = buf.getvalue()
open('/tmp/s186h170_A.txt','w').write(txt)
# print A's body and the 3-arg FCV ctor region
print(txt[:3500])
