#!/usr/bin/env python3
"""S104: dump packed-switch payload targets + ComponentActivity.<init> pc=0..100 (what classId is passed)."""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/s99/apks/com.vayunmathur.games.solitaire.apk"

zf = zipfile.ZipFile(APK)
done = set()
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        cn = c.get_name()
        if cn not in ("Lkotlin/text/MatcherMatchResult;", "Landroidx/activity/ComponentActivity;"):
            continue
        for m in c.get_methods():
            if cn == TARGET_MMR if False else False:
                pass
            if cn == "Lkotlin/text/MatcherMatchResult;" and m.get_name() == "<init>" \
               and m.get_descriptor() == "(Landroidx/savedstate/internal/SavedStateRegistryImpl; B)V":
                if "payload" in done: continue
                done.add("payload")
                pc = 0
                for ins in m.get_instructions():
                    if "payload" in ins.get_name():
                        print("PAYLOAD:", ins.get_output())
                        # raw targets
                        try:
                            print("  size:", ins.get_operation().tgts if hasattr(ins.get_operation(), 'tgts') else "?")
                        except Exception as e:
                            pass
                    pc += ins.get_length()
            if cn == "Landroidx/activity/ComponentActivity;" and m.get_name() == "<init>" \
               and m.get_descriptor() == "()V":
                if "ca" in done: continue
                done.add("ca")
                pc = 0
                for ins in m.get_instructions():
                    if pc <= 100:
                        print(f"CA pc={pc} {ins.get_name()} {ins.get_output()}")
                    pc += ins.get_length()
