#!/usr/bin/env python3
"""S104: parse packed-switch-payload raw (ident/size/first_key/targets) for the merged ctor."""
import struct, sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/s99/apks/com.vayunmathur.games.solitaire.apk"
TARGET = "Lkotlin/text/MatcherMatchResult;"

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        if c.get_name() != TARGET:
            continue
        for m in c.get_methods():
            if m.get_name() != "<init>" or m.get_descriptor() != "(Landroidx/savedstate/internal/SavedStateRegistryImpl; B)V":
                continue
            code = m.get_code()
            raw = code.get_raw() if hasattr(code, "get_raw") else None
            # instruction-level access
            pc = 0
            for ins in m.get_instructions():
                if ins.get_name() == "packed-switch-payload":
                    # androguard PackedSwitchArrayPayload: get_size, get_first_key, get_targets
                    print("size:", ins.get_size() if hasattr(ins, "get_size") else "?")
                    print("first_key:", ins.get_first_key() if hasattr(ins, "get_first_key") else "?")
                    print("targets:", ins.get_targets() if hasattr(ins, "get_targets") else "?")
                    try:
                        rb = ins.get_raw_payload() if hasattr(ins, "get_raw_payload") else None
                    except Exception:
                        rb = None
                    print("raw:", rb.hex() if rb else "n/a")
                pc += ins.get_length()
            # also dump packed-switch instruction itself
            pc = 0
            for ins in m.get_instructions():
                if ins.get_name() == "packed-switch":
                    print(f"packed-switch at pc={pc}: {ins.get_output()}")
                pc += ins.get_length()
