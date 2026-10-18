#!/usr/bin/env python3
"""CONT-87 Track 1 (F-NEW-395): full bytecode dump of Luu;.<clinit>."""
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = "upload/cont73_apks/org.andstatus.game2048_47.apk"
a = APK(APK_PATH)
for dex_name in a.get_dex_names():
    raw = a.get_file(dex_name)
    d = DEX(raw)
    for cls in d.get_classes():
        for m in cls.get_methods():
            if m.get_class_name() != "Luu;" or m.get_name() != "<clinit>":
                continue
            code = m.get_code()
            print("-- FULL bytecode --")
            idx = 0
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                operands = ins.get_operands()
                ops = []
                for o in operands:
                    ops.append("%s:%s" % (o[0], o[2] if len(o) > 2 else o[1]))
                print("  pc=%3d %-22s %s" % (idx, op, ", ".join(ops)))
                idx += ins.get_length()
            print("total insn bytes:", idx)
            print("-- handler list raw --")
            hl = code.get_handlers()
            print(hl)
