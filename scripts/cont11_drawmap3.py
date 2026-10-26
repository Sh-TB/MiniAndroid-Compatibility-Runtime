#!/usr/bin/env python3
"""CONT-11 W7 part 3: identify Ldi; (canvas iface?), Ljt1; (AndroidCanvas),
Lel0;.i draw dispatch, and who constructs the root canvas wrapper."""
import zipfile, re
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
with zipfile.ZipFile(APK) as z:
    dexs = [DalvikVMFormat(z.read(n)) for n in sorted(z.namelist()) if re.match(r'classes\d*\.dex$', n)]
cls = {}
for d in dexs:
    for c in d.get_classes():
        cls[c.get_name()] = c

def dump_class(name, max_methods=40, full=False, only=None):
    c = cls.get(name)
    if not c:
        print(f"--- {name}: NOT FOUND"); return
    print(f"--- {name} super={c.get_superclassname()} ifaces={list(c.get_interfaces())}")
    for f in c.get_fields():
        print(f"    field {f.get_name()} {f.get_descriptor()}")
    for m in c.get_methods()[:max_methods]:
        print(f"    method {m.get_name()} {m.get_descriptor()} codelen={m.get_code() and m.get_code().get_length() or 0}")
    if full and only:
        for m in c.get_methods():
            if m.get_name() in only:
                print(f"    === {m.get_name()} FULL ===")
                if m.get_code():
                    for i in m.get_code().get_bc().get_instructions():
                        print("       ", f"{i.get_name():16s} {i.get_output()}"[:170])

dump_class('Ljt1;')
dump_class('Ldi;', full=True, only=['<init>'])
# Lel0;.i — the draw dispatch
c = cls.get('Lel0;')
for m in c.get_methods():
    if m.get_name() == 'i' and m.get_descriptor().startswith('(Ldi;'):
        print(f"--- Lel0;.i {m.get_descriptor()} codelen={m.get_code().get_length()}")
        for i in m.get_code().get_bc().get_instructions():
            print("       ", f"{i.get_name():16s} {i.get_output()}"[:170])
        break
# who references Ljt1;-><init> anywhere (any signature)
print("\n=== references to Ljt1;-><init> ===")
n=0
for cn, c in cls.items():
    for m in c.get_methods():
        if not m.get_code(): continue
        for i in m.get_code().get_bc().get_instructions():
            s=i.get_output()
            if 'Ljt1;-><init>' in s:
                print(f"  {cn}->{m.get_name()}{m.get_descriptor()}\n      {i.get_name()} {s[:140]}")
                n+=1
                if n>12: break
        if n>12: break
    if n>12: break
