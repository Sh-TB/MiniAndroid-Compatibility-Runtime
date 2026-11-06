#!/usr/bin/env python3
"""S186h: disassemble tranquilstopwatch #170 blockers — Lb1/t0;.A (NPE site),
Lb0/k (null field .a), FragmentContainerView.<init> chain. Probe-first law."""
import zipfile, tempfile, os, sys, io
from loguru import logger
logger.remove()  # silence androguard noise

APK = 'upload/stuck_apks/tibarj.tranquilstopwatch.apk'
TARGETS = ['Lb1/t0;', 'Lb0/k;', 'Landroidx/fragment/app/FragmentContainerView;']

from androguard.misc import AnalyzeDex

def disasm_method(m, out):
    out.write(f"  METHOD {m.get_descriptor()}\n")
    off = 0
    for ins in m.get_instructions():
        op = ins.get_name()
        txt = ins.get_output()
        out.write(f"    {off:5d} {op:28s} {txt}\n")
        off += ins.get_length()
        if off > 1400: out.write("    ...trunc\n"); break

def disasm_class(c, out, only_methods=None):
    out.write(f"\nCLASS {c.get_name()}  super={c.get_superclassname()}\n")
    for f in c.get_fields():
        out.write(f"  FIELD {f.get_descriptor()} {f.get_name()}\n")
    for m in c.get_methods():
        if only_methods and m.get_name() not in only_methods:
            continue
        try:
            disasm_method(m, out)
        except Exception as e:
            out.write(f"  METHOD {m.get_descriptor()} ERR {e}\n")

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
        n = c.get_name()
        if n in TARGETS:
            only = {'A', '<init>', '<clinit>', 'l', 'a'} if n in ('Lb1/t0;', 'Lb0/k;') else {'<init>'}
            disasm_class(c, buf, only_methods=only)
    os.unlink(tmp.name)

txt = buf.getvalue()
open('/tmp/s186h170_disasm.txt', 'w').write(txt)
print(txt[:1500])
print("...\nfull -> /tmp/s186h170_disasm.txt", len(txt), "bytes")
