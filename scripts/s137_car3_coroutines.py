#!/usr/bin/env python3
"""s137_car3_coroutines.py — decode the coroutine machinery classes hit by
SuspendingPointerInputModifierNodeImpl (Lor1;): launch (Lxz1;.I), Job (Lkp1;),
CoroutineStart (Lj90;), lambda (Lru;), handler-coroutine (Lnr1;), awaiter (Lzh;).
"""
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

def show_class(name, max_methods=40):
    dn, c = find_class(name)
    if not c:
        print(f"!! class {name} not found")
        return
    print(f"== {name} (dex={dn}) super={c.get_superclassname()} ifaces={list(c.get_interfaces())}")
    for f in c.get_fields():
        print(f"   field {f.get_name()} {f.get_descriptor()}")
    ms = list(c.get_methods())
    for m in ms[:max_methods]:
        cl = m.get_code() and m.get_code().get_length() or 0
        print(f"   {m.get_name()} {m.get_descriptor()}  len={cl}")
    if len(ms) > max_methods:
        print(f"   ... +{len(ms)-max_methods} more")

def disasm(name, meth, max_ins=250):
    dn, c = find_class(name)
    if not c:
        print(f"!! class {name} not found for disasm")
        return
    for m in c.get_methods():
        if m.get_name() == meth:
            code = m.get_code()
            if not code:
                print(f"== {name}.{meth} {m.get_descriptor()} abstract/native")
                return
            print(f"== {name}.{meth} {m.get_descriptor()} len={code.get_length()}")
            n = 0; pc = 0
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                out = f"  {pc:04x}: {op}"
                pc += ins.get_length()
                try:
                    idx = ins.get_operands()
                    parts = []
                    for o in idx:
                        if o[0] >= 0x100 and o[0] < 0x200:
                            parts.append(str(o[2]))
                        elif o[0] < 0x100:
                            parts.append(f"v{o[1]}")
                    out += " " + ", ".join(parts)
                except Exception:
                    pass
                print(out)
                n += 1
                if n >= max_ins:
                    print("  ... truncated"); return
            return
    print(f"!! method {name}.{meth} not found")

if __name__ == '__main__':
    w = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if w in ('all', 'xz1'):
        show_class('Lxz1;')
        disasm('Lxz1;', 'I')
    if w in ('all', 'zh'):
        show_class('Lzh;')
        disasm('Lzh;', 'g')
    if w in ('all', 'nr1'):
        show_class('Lnr1;')
    if w in ('all', 'j90'):
        show_class('Lj90;')
    if w in ('all', 'ru'):
        show_class('Lru;')
