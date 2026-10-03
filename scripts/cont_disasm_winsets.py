#!/usr/bin/env python3
"""CONT-ROOT-B: disassemble androidx.core.view s0 (WindowInsetsCompat) and
s0$k static-init chain in the memory APK to name the null receiver."""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/diff366/hidden_sources/com.sanskritbasics.memory_34.apk"
TARGETS = {"Landroidx/core/view/s0;": {"<clinit>", "u", "v"},
           "Landroidx/core/view/s0$k;": {"<clinit>"}}

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        cn = c.get_name()
        if cn not in TARGETS:
            continue
        for m in c.get_methods():
            if m.get_name() not in TARGETS[cn]:
                continue
            code = m.get_code()
            if not code:
                continue
            print(f"=== {cn}.{m.get_name()} {m.get_descriptor()} ===")
            pc = 0
            for ins in code.get_bc().get_instructions():
                if pc <= 90:
                    print(f"pc={pc} {ins.get_name()} {ins.get_output()}")
                pc += ins.get_length()
            print()
