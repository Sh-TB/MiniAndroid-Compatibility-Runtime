#!/usr/bin/env python3
"""CONT-32 telegram train: decode the play_billing protobuf-lite MessageInfoFactory
chain (t1.zzb / i2.zzb / q2.a / u1.a) to pin the first engine-failing link."""
from androguard.core.dex import DEX
import zipfile, sys

APK = "/home/z/my-project/upload/telegram_official.apk"
TARGETS = ["Lcom/google/android/gms/internal/play_billing/t1;",   # the thrower
           "Lcom/google/android/gms/internal/play_billing/i2;",
           "Lcom/google/android/gms/internal/play_billing/p3;"]

zf = zipfile.ZipFile(APK)
found = {}
for name in zf.namelist():
    if not name.startswith("classes") or not name.endswith(".dex"):
        continue
    data = zf.read(name)
    try:
        d = DEX(data)
    except Exception:
        continue
    for m in d.get_methods():
        cls = m.get_class_name()
        if cls in TARGETS:
            meth = f"{cls}.{m.get_name()}{m.get_descriptor()}"
            found.setdefault(cls, {})[meth] = m

for cls, meths in found.items():
    print(f"=== {cls} ({len(meths)} methods)")
    for meth, m in sorted(meths.items()):
        code = m.get_code()
        if not code:
            print(f"  {meth}  <no-code>")
            continue
        bc = code.get_bc()
        print(f"  --- {meth}  (units={code.get_length()})")
        idx = 0
        for ins in bc.get_instructions():
            op = ins.get_name()
            txt = f"{op} {ins.get_output()}" if op not in ("nop",) else op
            print(f"    pc={idx:5d} {txt[:150]}")
            idx += ins.get_length()
            if idx > 900 and meth.endswith("zzb(I)"):
                break
