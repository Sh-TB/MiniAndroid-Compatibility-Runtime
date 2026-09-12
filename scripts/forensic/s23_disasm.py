#!/usr/bin/env python3
"""androguard oracle: full disassembly of one method (registers + branches).

Usage: python3 scripts/forensic/s23_disasm.py <apk> <class-desc> <method> [<proto-hint>]
  class-desc in DEX form, e.g. LM1/i;
Examples:
  python3 scripts/forensic/s23_disasm.py app.apk LM1/i; a
"""
import sys, zipfile
from loguru import logger
logger.remove()  # silence androguard debug spam
from androguard.core.dex import DEX

apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
proto_hint = sys.argv[4] if len(sys.argv) > 4 else None

z = zipfile.ZipFile(apk)
d = DEX(z.read('classes.dex'))

found = 0
for cl in d.get_classes():
    if cl.get_name() != cls:
        continue
    for m in cl.get_methods():
        if m.get_name() != meth:
            continue
        if proto_hint and proto_hint not in m.get_descriptor():
            continue
        found += 1
        print(f"== {cls}.{meth}{m.get_descriptor()} ==")
        code = m.get_code()
        if code is None:
            print("  <abstract/native>")
            continue
        off = code.get_bc().get_offset() if hasattr(code.get_bc(), 'get_offset') else 0
        for idx, ins in enumerate(code.get_bc().get_instructions()):
            print(f"  {ins.get_length():>2} @ {ins.get_name():26s} {ins.get_output()}")
        if code.get_tries_size():
            print(f"  tries={code.get_tries_size()}")
if not found:
    print(f"NOT FOUND: {cls}.{meth}")
