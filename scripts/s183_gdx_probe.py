#!/usr/bin/env python3
"""s183_gdx_probe.py — decode the emmanuelttt (#11 real APK) blocker exactly:
GdxRuntimeException from AndroidApplication.<clinit>; NPE in AndroidGraphics.<init> at invoke_pc=0x60/0x1."""
import sys, zipfile, tempfile, os, io
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex

APK = "/home/z/my-project/upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk"
WANT = [
    ("Lcom/badlogic/gdx/backends/android/AndroidApplication;", "<clinit>"),
    ("Lcom/badlogic/gdx/backends/android/AndroidGraphics;", "<init>"),
    ("Lcom/badlogic/gdx/backends/android/AndroidApplication;", "initializeForView"),
]

def main():
    with zipfile.ZipFile(APK) as z:
        for name in [n for n in z.namelist() if n.endswith(".dex")]:
            tmp = tempfile.NamedTemporaryFile(suffix=".dex", delete=False)
            tmp.write(z.read(name)); tmp.close()
            try:
                _, d, _ = AnalyzeDex(tmp.name)
            except Exception:
                os.unlink(tmp.name); continue
            for c in d.get_classes():
                cn = c.get_name()
                for wcls, wmeth in WANT:
                    if cn == wcls:
                        for m in c.get_methods():
                            if m.get_name() == wmeth:
                                print(f"\n===== {cn} -> {m.get_name()} {m.get_descriptor()} ({name})")
                                code = m.get_code()
                                if code is None:
                                    print("  (no code)"); continue
                                off = 0
                                for ins in m.get_instructions():
                                    op = ins.get_name()
                                    out = ins.get_output()
                                    if op.startswith(("invoke", "new-instance", "sget", "sput", "const-string", "iget", "iput")):
                                        print(f"  {off:#06x}: {op:22s} {out[:110]}")
                                    off += ins.get_length()
            os.unlink(tmp.name)

main()
