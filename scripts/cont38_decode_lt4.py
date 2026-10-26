#!/usr/bin/env python3
"""CONT-38 — decode the dooz compose view draw chain: Lt4; (the
AndroidComposeView-shaped class, dispatchDraw ran with ops=0) — find the
draw path it calls (Owner.draw / Root / LayoutNode cascade) and where the
CanvasDrawScope dispatch (Loc0;.c) SHOULD be invoked from."""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location("d9", "/home/z/my-project/scripts/cont9_dexdump.py")
d9 = importlib.util.module_from_spec(spec)
sys.modules["d9"] = d9
spec.loader.exec_module(d9)

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
d = d9.Dex(z.read("classes.dex"))

def class_info(desc):
    off = d.find_class(desc)
    if off is None:
        return None
    return d.class_methods(off)

info = class_info("Lt4;")
print("=== Lt4; === super:", info['super'], "ifaces:", info['ifaces'])
for f in info['fields'][:15]:
    print("  field", f)
for kind in ("direct","virtual"):
    for (mname, mdesc, acc, sz, code) in info[kind]:
        if sz > 0 and any(k in mname for k in ("onDraw","dispatchDraw","draw","onSizeChanged","onLayout","onMeasure")):
            print(f"  {kind} {mname}{mdesc} acc={acc:#x} size={sz}")

# disasm dispatchDraw / onDraw if present
for (mname, mdesc, acc, sz, code) in info['direct'] + info['virtual']:
    if mname in ("dispatchDraw","onDraw") and code:
        print(f"\n--- disasm Lt4;.{mname}{mdesc} size={sz} ---")
        print(d.disasm(code))

# who calls Loc0;.c (CanvasDrawScope.dispatch)?
print("\n=== invoke sites of Loc0;.c ===")
INVOKE_OPS = {0x6e,0x6f,0x70,0x71,0x72}
for i in range(d.class_defs_size):
    off = d.class_defs_off + i*32
    cdesc = d.type_str(d.u(off, 4))
    try:
        cinfo = d.class_methods(off)
    except Exception:
        continue
    for kind in ("direct","virtual"):
        for (mname, mdesc, acc, sz, code) in cinfo[kind]:
            if not code or sz == 0: continue
            insns_off = code + 16
            pc = 0
            while pc < sz:
                o = insns_off + pc*2
                word = d.u(o, 2)
                op = word & 0xff
                if op in INVOKE_OPS:
                    midx = d.u(o+2, 2)
                    try: cref, mref, mdsc = d.method_ref(midx)
                    except Exception: pc += 3; continue
                    if mref == 'c' and cref == 'Loc0;':
                        print(f"  {cdesc}.{mname}{mdesc} pc={pc} op={op:#x} -> Loc0;.c{mdsc}")
                    pc += 3
                elif op == 0x00: pc += 1
                else:
                    if op in (0x22,0x1c,0x1f,0x20,0x23,0x24,0x25,0x1a) or 0x52 <= op <= 0x6d: pc += 2
                    elif op in (0x13,0x16,0x19,0x29,0x2a,0x2b,0x2c,0x17): pc += 2
                    elif op in (0x18,0x14): pc += 3
                    else: pc += 1
