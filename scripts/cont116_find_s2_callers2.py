#!/usr/bin/env python3
"""cont116_find_s2_callers2.py — precise: scan all play_billing methods' bytecode
for invoke-kind opcodes whose method index references s2;-><init>, then report
the calling method and its const-string refs."""
import sys, zipfile
sys.path.insert(0, "scripts")
from cont9_dexdump import Dex

APK = "upload/telegram_official.apk"
PKG = "Lcom/google/android/gms/internal/play_billing/"

z = zipfile.ZipFile(APK)
d = Dex(z.read("classes.dex"))

# 1) find method_ids entries for s2;-><init>
s2_init_ids = []
for idx in range(d.method_ids_size):
    cls, name, _proto = d.method_ref(idx)
    if str(cls).endswith("s2;") and str(name) == "<init>":
        s2_init_ids.append(idx)
print("s2.<init> method_ids:", s2_init_ids)

def iter_class_defs(d):
    for i in range(d.class_defs_size):
        yield d.u(d.class_defs_off + 32 * i, 4)

INVOKE_OPS = {0x6E, 0x6F, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78}
callers = []
for cdef in iter_class_defs(d):
    desc = d.type_str(d.u(cdef, 4))
    if not desc.startswith(PKG):
        continue
    info = d.class_methods(cdef)
    for kind in ("direct", "virtual"):
        for mname, mdesc, acc, sz, code in info[kind]:
            if not code:
                continue
            for j in range(sz):
                w = d.u(code + 2 * j, 2)
                if (w & 0xFF) in INVOKE_OPS:
                    midx = d.u(code + 2 * j + 2, 2)
                    if midx in s2_init_ids:
                        callers.append((desc, kind, mname, mdesc, sz, code))
                        break

print(f"s2.<init> callers: {len(callers)}")
for desc, kind, mname, mdesc, sz, code in callers:
    print(f"== CALLER {desc} {kind} {mname}{mdesc} size={sz}")
    # print its const-string lines via cont9 disasm
    for line in d.disasm(code):
        if "const-string" in line:
            print("   ", line.strip()[:150])
