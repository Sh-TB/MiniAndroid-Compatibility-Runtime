#!/usr/bin/env python3
"""s137_car2_decode.py — static decode of Lx71; / Lhz0; / Lor1; from dooz v23 dex.
Car 2 of train-6: identify the class reached per-node inside HitPathTracker
dispatch (Lhz0;.e) and determine whether an A=4 filter-invoke exists anywhere
on the path, or whether dispatch dies earlier.
Usage: python3 s137_car2_decode.py
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

def show_class(name, max_methods=60):
    dn, c = find_class(name)
    if not c:
        print(f"!! class {name} not found")
        return
    print(f"== {name} (dex={dn}) super={c.get_superclassname()} ifaces={list(c.get_interfaces())}")
    ms = list(c.get_methods())
    for m in ms[:max_methods]:
        cl = m.get_code() and m.get_code().get_length() or 0
        print(f"   {m.get_name()} {m.get_descriptor()}  len={cl}")
    if len(ms) > max_methods:
        print(f"   ... +{len(ms)-max_methods} more")

def disasm(name, meth, max_ins=200):
    dn, c = find_class(name)
    if not c:
        print(f"!! class {name} not found for disasm")
        return
    for m in c.get_methods():
        if m.get_name() == meth:
            code = m.get_code()
            if not code:
                print(f"== {name}.{meth} abstract/native")
                return
            print(f"== {name}.{meth} {m.get_descriptor()} len={code.get_length()}")
            n = 0
            pc = 0
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                out = f"  {pc:04x}: {op}"
                pc += ins.get_length()
                try:
                    if 'invoke' in op:
                        idx = ins.get_operands()
                        out += " " + ", ".join(str(o[2]) for o in idx if o[0] >= 0x100 and o[0] < 0x200)
                        out += f"   [{op} regs={ins.get_length()/2:.0f}w]"
                    elif 'iget' in op or 'iput' in op or 'sget' in op or 'sput' in op or 'const' in op:
                        idx = ins.get_operands()
                        parts = []
                        for o in idx:
                            if o[0] >= 0x100:
                                parts.append(str(o[2]))
                            else:
                                parts.append(f"v{o[1]}")
                        out += " " + ", ".join(parts)
                except Exception as e:
                    out += f" <err {e}>"
                print(out)
                n += 1
                if n >= max_ins:
                    print("  ... truncated")
                    return
            return
    print(f"!! method {name}.{meth} not found")

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('all', 'x71'):
        show_class('Lx71;')
        disasm('Lx71;', 'J')
    if which in ('all', 'or1j'):
        disasm('Lor1;', 'J')
        disasm('Lor1;', 'M0')
        disasm('Lor1;', 'N0')
    if which in ('all', 'wt0'):
        show_class('Lwt0;')
    if which in ('all', 'n71'):
        show_class('Ln71;')
    if which in ('all', 'o71'):
        show_class('Lo71;')
    if which in ('all', 'hz0'):
        show_class('Lhz0;')
        disasm('Lhz0;', 'e')
    if which in ('all', 'lor1'):
        show_class('Lor1;')
    if which in ('all', 'sj'):
        show_class('Lsj;')
