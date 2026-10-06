#!/usr/bin/env python3
"""Disassemble a method and list new-instance / invoke targets."""
import sys, zipfile, re
sys.path.insert(0, '/home/z/my-project/tmp/w4venv/lib/python3.12/site-packages')
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
_dexs = None
def dexs():
    global _dexs
    if _dexs is None:
        _dexs = []
        with zipfile.ZipFile(APK) as z:
            for n in sorted(x for x in z.namelist() if re.match(r'classes\d*\.dex$', x)):
                _dexs.append((n, DEX(z.read(n))))
    return _dexs

def get_method(cls_name, meth_name, desc=None):
    for n, d in dexs():
        for c in d.get_classes():
            if c.get_name() == cls_name:
                for m in c.get_methods():
                    if m.get_name() == meth_name and (desc is None or m.get_descriptor() == desc):
                        return (n, c, m)
    return None

def show_new_invokes(cls, meth, desc=None, max_ins=100000):
    r = get_method(cls, meth, desc)
    if not r:
        print(f"{cls}.{meth}{desc or ''} NOT FOUND"); return
    n, c, m = r
    code = m.get_code()
    bc = code.get_bc()
    idx = 0
    lines = []
    for ins in bc.get_instructions():
        op = ins.get_name()
        out = None
        if op.startswith('new-instance'):
            out = 'NEW ' + ins.get_string() if hasattr(ins, 'get_string') else op
        elif op.startswith(('invoke-',)):
            try:
                ref = ins.get_operands()
                # operand 1 is method ref
                mref = ins.get_ref_kind() if hasattr(ins,'get_ref_kind') else None
                s = str(ins.get_output()) if hasattr(ins, 'get_output') else ''
            except Exception:
                s = ''
            out = op.upper().split('-')[0] + ' ' + s[:150]
        if out:
            lines.append(out)
    print(f"=== {cls}.{meth} {m.get_descriptor()} ({len(lines)} new/invoke) ===")
    for L in lines[:max_ins]:
        print("  ", L.strip())

if __name__ == '__main__':
    cls, meth = sys.argv[1], sys.argv[2]
    desc = sys.argv[3] if len(sys.argv) > 3 else None
    show_new_invokes(cls, meth, desc)
