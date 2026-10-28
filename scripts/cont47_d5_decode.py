#!/usr/bin/env python3
"""CONT-47 D5 DOOZ: decode the applyChanges chain (Ls21;.Y / Ly11;.a/.b /
Lv02;.c/.q) from the dooz APK — is the AOSP per-scope applier.down(node)
present at replay? AOSP CompositionImpl.applyChanges:
  for ((scope, changes) in changeLists) { applier.down(scope.node); ... }
Usage: cont47_d5_decode.py"""
import sys, logging, zipfile
logging.disable(logging.CRITICAL)
from loguru import logger as _lg
_lg.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
TARGETS = [("Ls21;", "Y"), ("Ly11;", "a"), ("Ly11;", "b"), ("Lv02;", "c"), ("Lv02;", "q")]

z = zipfile.ZipFile(APK)
for dn in [n for n in z.namelist() if n.endswith(".dex")]:
    d = DEX(z.read(dn))
    for c in d.get_classes():
        cn = c.get_name()
        for (tc, tm) in TARGETS:
            if cn != tc:
                continue
            for m in c.get_methods():
                if m.get_name() != tm:
                    continue
                code = m.get_code()
                if not code:
                    print(f"{tc}.{tm}: no code")
                    continue
                print(f"=== {tc}.{tm}{m.get_descriptor()} [{dn}] ===")
                ops = []
                for ins in code.get_bc().get_instructions():
                    nm = ins.get_name()
                    if nm.startswith("invoke-") or nm.startswith("iget") or nm.startswith("iput") or nm in ("const/4","const/16","const/high16"):
                        try:
                            o = ins.get_operands(0)
                        except Exception:
                            o = []
                        detail = ""
                        for x in o:
                            if len(x) >= 3 and isinstance(x[2], str):
                                detail += f" {x[2]}"
                        ops.append(nm + detail)
                # print condensed: invocations + field ops
                for line in ops[:60]:
                    print("   ", line)
                if len(ops) > 60:
                    print(f"    ... +{len(ops)-60} more")
