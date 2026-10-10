#!/usr/bin/env python3
# cont38_color_decode.py — CONT-38 Phase-1: static decode of the
# composeStopwatch text-color chain. Find: (1) the Text composables and the
# color values/params they pass; (2) the AndroidParagraphIntrinsics (Lk6;)
# TextPaint color path incl. takeOrElse fallback; (3) any MaterialTheme /
# CompositionLocal color reads. Field-ref-exact, no guessing.
import zipfile, sys
from androguard.core.dex import DEX

APK = '/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk'
z = zipfile.ZipFile(APK)
d = DEX(z.read('classes.dex'))

def show_method(cls_name, meth_prefix=None, max_instr=None):
    for c in d.get_classes():
        if c.get_name() != cls_name:
            continue
        for m in c.get_methods():
            if meth_prefix and not m.get_name().startswith(meth_prefix):
                continue
            code = m.get_code()
            print(f"== {cls_name}->{m.get_name()}{m.get_descriptor()} regs={code.get_registers_size() if code else '?'}")
            if not code:
                continue
            for i in code.get_bc().get_instructions():
                op = i.get_name()
                out = i.get_output()
                print(f"   {i.get_hex():<10} {op:<28} {out[:110]}")
        return True
    return False

# 1. Lk6; = AndroidParagraphIntrinsics — the TextPaint construction site
#    (decoded in CONT-35). Dump the <init>.
if not show_method('Lk6;'):
    print("Lk6; not found — searching for AndroidParagraphIntrinsics-like classes...")
EOF = None
