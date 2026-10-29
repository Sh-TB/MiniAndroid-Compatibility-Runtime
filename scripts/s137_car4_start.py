#!/usr/bin/env python3
"""s137_car4_start.py — decode Ls;.h0 (JobSupport.start) and Lyr; (CoroutineStart)
to pinpoint where the UNDISPATCHED block launch dies before running its body."""
import sys, zipfile, re
try:
    from androguard.core.dex import DEX
except ImportError:
    from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX

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

def find_class(name):
    for dn, d in dexs():
        for c in d.get_classes():
            if c.get_name() == name:
                return dn, c
    return None, None

def disasm(name, meth, max_ins=400):
    dn, c = find_class(name)
    if not c:
        print(f"!! class {name} not found"); return
    print(f"== {name} super={c.get_superclassname()} ifaces={list(c.get_interfaces())}")
    for m in c.get_methods():
        if m.get_name() == meth:
            code = m.get_code()
            if not code:
                print(f"== {name}.{meth} {m.get_descriptor()} abstract"); return
            print(f"== {name}.{meth} {m.get_descriptor()} len={code.get_length()}")
            n=0; pc=0
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                out = f"  {pc:04x}: {op}"
                pc += ins.get_length()
                try:
                    parts=[]
                    for o in ins.get_operands():
                        if o[0] >= 0x100 and o[0] < 0x200: parts.append(str(o[2]))
                        elif o[0] < 0x100: parts.append(f"v{o[1]}")
                    out += " " + ", ".join(parts)
                except Exception: pass
                print(out)
                n+=1
                if n>=max_ins: print("  ...trunc"); return
            return
    print(f"!! {name}.{meth} not found")

if __name__ == '__main__':
    w = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if w in ('all','s'):
        disasm('Ls;', 'h0')
    if w in ('all','yr'):
        dn, c = find_class('Lyr;')
        if c:
            print(f"== Lyr; super={c.get_superclassname()} ifaces={list(c.get_interfaces())}")
            for m in c.get_methods():
                cl = m.get_code() and m.get_code().get_length() or 0
                print(f"   {m.get_name()} {m.get_descriptor()} len={cl}")
        for meth in ('invoke','a','b','c','d'):
            disasm('Lyr;', meth, max_ins=120)
