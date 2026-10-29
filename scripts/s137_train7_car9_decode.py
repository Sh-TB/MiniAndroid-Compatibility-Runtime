#!/usr/bin/env python3
"""s137_train7_car9_decode.py — static decode of the composed-factory arg
evaluation chain discovered DYNAMICALLY by car-9 (S137b probe):
  Lbr1;.h pc=103 -> Lkr1;.a(recv=Lol;, r0=Le12;#479, r1=Lpv;#6077, r0=Le12;#479)
  Lsv;.a pc=281  -> Lkr1;.a(recv=Lol;, r12=Le12;#479, r11=Lpv;#6076, r0=Ldn1;#8188)
Questions this decode answers:
  Q1 what class is Lol; (the Lkr1; implementor receiving the calls)?
  Q2 what are Lkr1;.a's exact params (from its invoke call inside)?
  Q3 WHICH instructions in Lbr1;.h feed r0/r1 before pc=103 — is the
     garbage (Le12;=COROUTINE_SUSPENDED, Lpv; no-op) produced by an sget of
     a real compose static (legit no-op overload) or by engine mis-execution?
  Q4 same for Lsv;.a pc=281 (which passes a REAL Ldn1; object).
"""
import sys, zipfile, re
try:
    from androguard.core.dex import DEX
except ImportError:
    from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX

APK = '/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk'

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
        print(f"!! class {name} not found for disasm")
        return
    for m in c.get_methods():
        if m.get_name() == meth:
            code = m.get_code()
            if not code:
                print(f"== {name}.{meth} abstract/native")
                return
            print(f"== {name}.{meth} {m.get_descriptor()} "
                  f"access={hex(m.get_access_flags())} len={code.get_length()}")
            pc = 0
            n = 0
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                out = f"  {pc:04x}: {op}"
                pc += ins.get_length()
                n += 1
                if n > max_ins:
                    print(out, "... TRUNCATED")
                    return
                try:
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
            return
    print(f"!! method {name}.{meth} not found")

def show_class_header(name):
    dn, c = find_class(name)
    if not c:
        print(f"!! class {name} not found")
        return
    print(f"== {name} dex={dn} super={c.get_superclassname()} "
          f"ifaces={list(c.get_interfaces())}")
    for f in c.get_fields():
        print(f"   field {f.get_name()} {f.get_descriptor()}")
    for m in c.get_methods():
        code = m.get_code()
        ln = code.get_length() if code else 0
        print(f"   method {m.get_name()} {m.get_descriptor()} len={ln}")

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('all', 'lol'):
        show_class_header('Lol;')
    if which in ('all', 'kr1'):
        show_class_header('Lkr1;')
    if which in ('all', 'br1'):
        disasm('Lbr1;', 'h', 300)
    if which in ('all', 'sv'):
        disasm('Lsv;', 'a', 500)
