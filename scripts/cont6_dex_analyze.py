#!/usr/bin/env python3
"""cont6_dex_analyze.py — androguard-based DEX analysis for CONT-6 Compose frontier.

Usage: cont6_dex_analyze.py <apk> <command> [args...]
Commands:
  xrefs <Lcls;> <method>       — who calls this method (caller class.method @pc)
  methods <Lcls;>              — list all methods of a class
  body <Lcls;> <method>        — disassemble one method with operand detail
  findfield <Lcls;> <fname>    — which methods write (iput) this field
  callers-of-set               — all xrefs to owner-field writers of LayoutNode
"""
import sys, zipfile, io
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = sys.argv[1]
CMD = sys.argv[2]

z = zipfile.ZipFile(APK)
names = [n for n in z.namelist() if n.endswith('.dex')]
bufs = [z.read(n) for n in names]
ds = [DEX(b) for b in bufs]

def find_method(cls, mname):
    for d in ds:
        for c in d.get_classes():
            if c.get_name() != cls:
                continue
            for m in c.get_methods():
                if m.get_name() == mname:
                    return d, m
    return None, None

def iter_class_methods(cls):
    for d in ds:
        for c in d.get_classes():
            if c.get_name() == cls:
                for m in c.get_methods():
                    yield m

def all_methods():
    for d in ds:
        for c in d.get_classes():
            for m in c.get_methods():
                yield m

if CMD == 'methods':
    cls = sys.argv[3]
    for m in iter_class_methods(cls):
        print(f"{m.get_access_flags_string():24s} {m.get_descriptor()}  {m.get_name()}")
elif CMD == 'body':
    cls, mname = sys.argv[3], sys.argv[4]
    d, m = find_method(cls, mname)
    if not m:
        print("NOT FOUND"); sys.exit(1)
    print(f"{m.get_class_name()}.{m.get_name()} {m.get_descriptor()}")
    for ins in m.get_instructions():
        print(f"  {ins.get_name():28s} {ins.get_output()}")
elif CMD == 'callers':
    cls, mname = sys.argv[3], sys.argv[4]
    # scan all methods' instructions for invocations of cls.mname
    for meth in all_methods():
        if meth.get_code() is None: continue
        try:
            for ins in meth.get_instructions():
                op = ins.get_name()
                if op.startswith('invoke'):
                    out = ins.get_output()
                    if f"{cls}->{mname}(" in out or f"{cls}->{mname}:" in out:
                        print(f"{meth.get_class_name()}.{meth.get_name()} {meth.get_descriptor()}")
                        break
        except Exception:
            pass
elif CMD == 'findfield':
    cls, fname = sys.argv[3], sys.argv[4]
    for meth in all_methods():
        if meth.get_code() is None: continue
        try:
            for ins in meth.get_instructions():
                op = ins.get_name()
                if op.startswith(('iput', 'iget')):
                    out = ins.get_output()
                    if f"{cls}->{fname} " in out or f"{cls}->{fname} L" in out:
                        kind = 'WRITE' if op.startswith('iput') else 'READ '
                        print(f"{kind} {meth.get_class_name()}.{meth.get_name()} {meth.get_descriptor()}  [{op}]")
        except Exception:
            pass
