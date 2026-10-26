#!/usr/bin/env python3
"""CONT-38 — decode Lho1;.b(Lf90;) — the dooz draw-block dispatcher that the
M3-19 active-cycle stub kills at lifetime_calls=6 (~pc2 same-site re-entry).

Outputs:
1. Full disassembly of Lho1;.b overloads.
2. Lho1; class shape (fields, interfaces, super).
3. Every invoke site of Lho1;.b across the APK (class.method pc -> who).
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"

z = zipfile.ZipFile(APK)
dexes = []
for name in [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]:
    dexes.append((name, d9.Dex(z.read(name))))

print(f"loaded {len(dexes)} dex files")

# 1) Lho1; class shape + disasm of b()
for dexname, d in dexes:
    off = d.find_class("Lho1;")
    if off is None:
        continue
    print(f"\n=== {dexname}: Lho1; @class_defs[{off}] ===")
    info = d.class_methods(off)
    print("super:", info['super'], "ifaces:", info['ifaces'])
    print("fields:")
    for f in info['fields']:
        print("  ", f)
    for kind in ("direct", "virtual"):
        for (mname, mdesc, acc, sz, code) in info[kind]:
            print(f"  {kind} {mname}{mdesc} acc={acc:#x} size={sz}")
    # disasm only b()
    for (mname, mdesc, acc, sz, code) in info['direct'] + info['virtual']:
        if mname == 'b' and code:
            print(f"\n--- disasm Lho1;.b{mdesc} (size={sz}) ---")
            print(d.disasm(code))
    break

# 2) all invoke sites of Lho1;.b
print("\n=== invoke sites of Lho1;.b ===")
INVOKE_OPS = {0x6e,0x6f,0x70,0x71,0x72}  # virtual/super/direct/static/interface
for dexname, d in dexes:
    for i in range(d.class_defs_size):
        off = d.class_defs_off + i*32
        cdesc = d.type_str(d.u(off, 4))
        try:
            info = d.class_methods(off)
        except Exception:
            continue
        for kind in ("direct", "virtual"):
            for (mname, mdesc, acc, sz, code) in info[kind]:
                if not code or sz == 0:
                    continue
                insns_off = code + 16
                pc = 0
                while pc < sz:
                    o = insns_off + pc*2
                    word = d.u(o, 2)
                    op = word & 0xff
                    if op in INVOKE_OPS:
                        midx = d.u(o+2, 2)
                        try:
                            cref, mref, mdsc = d.method_ref(midx)
                        except Exception:
                            pc += 3
                            continue
                        if mref == 'b' and cref == 'Lho1;':
                            print(f"  {cdesc}.{mname}{mdesc} pc={pc} op={op:#x}")
                        pc += 3
                    elif op in (0x00,):
                        pc += 1
                    else:
                        # approximate: most ops advance 1; a few advance 2-3
                        if op in (0x22,0x1c,0x1f,0x20,0x23,0x24,0x25,0x1a) or 0x52 <= op <= 0x6d:
                            pc += 2
                        elif op in (0x13,0x16,0x19,0x29,0x2a,0x2b,0x2c,0x17):
                            pc += 2
                        elif op == 0x18 or op == 0x14:
                            pc += 3
                        elif op == 0x2b or op == 0x2c:
                            pc += 3
                        else:
                            pc += 1
